"""
Scraping incremental seguro — roda via GitHub Actions toda semana.
Mantém os dados antigos intactos e apenas insere registros novos.
"""

import logging
import sys

# Garante que o root do projeto está no path ao rodar via `python -m scraper.sync`
sys.path.insert(0, ".")

from sqlalchemy import func
from sqlalchemy.orm import Session

from api.core.database import SessionLocal
from api.models.scrape_erro import ScrapeErro
from api.models.veiculo import Marca, Modelo, ModeloAno, Versao, VersaoDetalhe
from scraper.erros import registrar_erro, resolver_erro_se_existir
from scraper.sources.fichacompleta import FichaCompletaScraper

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def upsert_marca(db: Session, nome: str) -> tuple[Marca, bool]:
    """Retorna a Marca e um booleano indicando se ela é NOVA no banco."""
    nome_formatado = nome.strip().title()
    marca = db.query(Marca).filter(func.lower(Marca.nome) == func.lower(nome_formatado)).first()

    if not marca:
        marca = Marca(nome=nome_formatado)
        db.add(marca)
        db.flush()
        return marca, True

    return marca, False


def upsert_modelo(db: Session, marca_id: int, nome: str, url: str) -> tuple[Modelo, bool]:
    """Retorna o Modelo e um booleano indicando se ele é NOVO no banco."""
    nome_formatado = nome.strip().title()
    modelo = (
        db.query(Modelo)
        .filter(Modelo.marca_id == marca_id, func.lower(Modelo.nome) == func.lower(nome_formatado))
        .first()
    )

    if not modelo:
        modelo = Modelo(marca_id=marca_id, nome=nome_formatado, url=url)
        db.add(modelo)
        db.flush()
        return modelo, True

    return modelo, False


def upsert_ano(db: Session, modelo_id: int, ano: int) -> ModeloAno:
    ma = db.query(ModeloAno).filter_by(modelo_id=modelo_id, ano=ano).first()
    if not ma:
        ma = ModeloAno(modelo_id=modelo_id, ano=ano)
        db.add(ma)
        db.flush()
    return ma


def _processar_versao(
    db: Session, scraper: FichaCompletaScraper, marca: Marca, modelo: Modelo, versao_raw: dict
) -> str:
    """
    Processa uma versão de forma estritamente incremental.
    Se já existir no banco, ignora completamente sem alterar o registro antigo.
    """
    versao_crua = versao_raw["versao"].strip()

    # Padroniza como o nome DEVERIA ser caso precise ser inserido
    if versao_crua.lower().startswith(modelo.nome.lower()):
        versao_formatada = versao_crua
    else:
        versao_formatada = f"{modelo.nome} {versao_crua}"

    contexto = f"{marca.nome} > {modelo.nome} > {versao_raw['ano']} > {versao_formatada}"

    try:
        ano = upsert_ano(db, modelo.id, versao_raw["ano"])

        # Busca se a versão já existe por URL ou por nome (tanto o composto quanto o cru antigo)
        existe = (
            db.query(Versao)
            .filter(
                Versao.modelo_ano_id == ano.id,
                (Versao.url == versao_raw["url"])
                | (func.lower(Versao.versao) == func.lower(versao_formatada))
                | (func.lower(Versao.versao) == func.lower(versao_crua)),
            )
            .first()
        )

        # 🛑 SE JÁ EXISTE, PARA AQUI. Não atualiza URL, não altera texto, não faz nada.
        if existe:
            return "DUPLICADO"

        # Se REALMENTE NÃO EXISTE, faz o scrap dos detalhes e insere o registro novo
        with db.begin_nested():
            detalhes = scraper.detalhe_versao(versao_raw["url"])

            versao = Versao(
                modelo_ano_id=ano.id,
                versao=versao_formatada,
                url=versao_raw["url"],
            )
            db.add(versao)
            db.flush()
            db.add(VersaoDetalhe(versao_id=versao.id, **detalhes))

        resolver_erro_se_existir(db, versao_raw["url"])
        logger.info("🚗 Nova Versão Inserida: %s", contexto)
        return "INSERIDO"

    except Exception as exc:
        registrar_erro(
            db, url=versao_raw["url"], etapa="detalhe_versao", exc=exc, contexto=contexto
        )
        return "FALHA"


def sync() -> None:
    db: Session = SessionLocal()
    novos = 0
    falhas = 0

    try:
        with FichaCompletaScraper(delay=1.5) as scraper:
            marcas = scraper.listar_marcas()
            logger.info("Total de marcas encontradas no site: %d", len(marcas))

            for marca_raw in marcas:
                marca, marca_eh_nova = upsert_marca(db, marca_raw["nome"])
                if marca_eh_nova:
                    logger.info("✨ Nova Marca: %s", marca.nome)

                try:
                    modelos = scraper.listar_modelos(marca_raw["url"])
                    resolver_erro_se_existir(db, marca_raw["url"])
                except Exception as exc:
                    registrar_erro(
                        db,
                        url=marca_raw["url"],
                        etapa="listar_modelos",
                        exc=exc,
                        contexto=marca.nome,
                    )
                    db.commit()
                    falhas += 1
                    continue

                for modelo_raw in modelos:
                    modelo, modelo_eh_novo = upsert_modelo(
                        db, marca.id, modelo_raw["nome"], modelo_raw["url"]
                    )
                    if modelo_eh_novo:
                        logger.info("📦 Novo Modelo: %s > %s", marca.nome, modelo.nome)

                    try:
                        versoes = scraper.listar_versoes(modelo_raw["url"])
                        resolver_erro_se_existir(db, modelo_raw["url"])
                    except Exception as exc:
                        registrar_erro(
                            db,
                            url=modelo_raw["url"],
                            etapa="listar_versoes",
                            exc=exc,
                            contexto=f"{marca.nome} > {modelo.nome}",
                        )
                        db.commit()
                        falhas += 1
                        continue

                    model_novos = 0
                    model_pulados = 0

                    for versao_raw in versoes:
                        status = _processar_versao(db, scraper, marca, modelo, versao_raw)
                        if status == "INSERIDO":
                            novos += 1
                            model_novos += 1
                        elif status == "FALHA":
                            falhas += 1
                        elif status == "DUPLICADO":
                            model_pulados += 1

                    if model_pulados > 0:
                        logger.info(
                            "⏭️ %s > %s: %d versão(ões) mantida(s) do banco antigo (pulada(s))",
                            marca.nome,
                            modelo.nome,
                            model_pulados,
                        )

                    db.commit()

    except Exception:
        db.rollback()
        logger.exception("Erro fatal durante o sync — execução interrompida")
        raise
    finally:
        pendentes = db.query(ScrapeErro).count()
        db.close()

    logger.info(
        "Sync concluído — %d novas versões | %d falhas neste run | %d erros pendentes no total",
        novos,
        falhas,
        pendentes,
    )


if __name__ == "__main__":
    sync()
