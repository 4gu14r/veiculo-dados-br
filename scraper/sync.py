"""
Scraping incremental — roda via GitHub Actions toda semana.

Lógica:
  1. Percorre marcas → modelos → anos/versões (só listagens, rápido)
  2. Para cada versão verifica pela URL se já existe no banco
  3. Se não existe → baixa a ficha completa e insere
  4. Se existe     → pula (sem rebaixar a performance revisitando fichas antigas)

Resiliência a erros:
  - Uma falha em qualquer nível (marca, modelo ou versão) NÃO derruba o
    resto do run — é registrada em `scrape_erros` (ver scraper/erros.py),
    com a etapa, a URL e o motivo exato, e o scraper segue pro próximo item.
  - Falhas em nível de versão usam SAVEPOINT (transação aninhada), então
    não desfazem o que já foi salvo no mesmo modelo/marca antes dela.
  - Se um item que falhou antes for processado com sucesso num run
    futuro, o registro de erro correspondente é apagado automaticamente
    — a tabela `scrape_erros` sempre reflete só o que está pendente agora.
  - Consulte os erros pendentes via GET /api/v1/scrape-erros ou direto
    no banco: SELECT url, etapa, tipo_erro, mensagem, tentativas FROM scrape_erros;
"""

import logging
import sys

# Garante que o root do projeto está no path ao rodar via `python -m scraper.sync`
sys.path.insert(0, ".")

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


def upsert_marca(db: Session, nome: str) -> Marca:
    marca = db.query(Marca).filter_by(nome=nome).first()
    if not marca:
        marca = Marca(nome=nome)
        db.add(marca)
        db.flush()
    return marca


def upsert_modelo(db: Session, marca_id: int, nome: str, url: str) -> Modelo:
    modelo = db.query(Modelo).filter_by(marca_id=marca_id, nome=nome).first()
    if not modelo:
        modelo = Modelo(marca_id=marca_id, nome=nome, url=url)
        db.add(modelo)
        db.flush()
    return modelo


def upsert_ano(db: Session, modelo_id: int, ano: int) -> ModeloAno:
    ma = db.query(ModeloAno).filter_by(modelo_id=modelo_id, ano=ano).first()
    if not ma:
        ma = ModeloAno(modelo_id=modelo_id, ano=ano)
        db.add(ma)
        db.flush()
    return ma


def _processar_versao(db: Session, scraper: FichaCompletaScraper, marca: Marca, modelo: Modelo, versao_raw: dict) -> bool:
    """
    Processa uma única versão dentro de um SAVEPOINT.
    Se falhar, só desfaz essa versão — não afeta o resto do modelo/marca
    já processado nesta mesma transação. Retorna True se inseriu com sucesso.
    """
    contexto = f"{marca.nome} > {modelo.nome} > {versao_raw['ano']} > {versao_raw['versao']}"

    try:
        with db.begin_nested():
            ano = upsert_ano(db, modelo.id, versao_raw["ano"])
            detalhes = scraper.detalhe_versao(versao_raw["url"])

            versao = Versao(
                modelo_ano_id=ano.id,
                versao=versao_raw["versao"],
                url=versao_raw["url"],
            )
            db.add(versao)
            db.flush()
            db.add(VersaoDetalhe(versao_id=versao.id, **detalhes))

        resolver_erro_se_existir(db, versao_raw["url"])
        logger.info("Novo: %s", contexto)
        return True

    except Exception as exc:
        registrar_erro(db, url=versao_raw["url"], etapa="detalhe_versao", exc=exc, contexto=contexto)
        return False


def sync() -> None:
    db: Session = SessionLocal()
    novos = 0
    falhas = 0

    try:
        with FichaCompletaScraper(delay=1.5) as scraper:
            marcas = scraper.listar_marcas()
            logger.info("Total de marcas encontradas: %d", len(marcas))

            for marca_raw in marcas:
                marca = upsert_marca(db, marca_raw["nome"])

                # ── Nível marca: listar modelos ─────────────────────────────
                try:
                    modelos = scraper.listar_modelos(marca_raw["url"])
                    resolver_erro_se_existir(db, marca_raw["url"])
                except Exception as exc:
                    registrar_erro(db, url=marca_raw["url"], etapa="listar_modelos", exc=exc, contexto=marca.nome)
                    db.commit()
                    falhas += 1
                    logger.warning("Pulando marca inteira '%s' — não deu pra listar os modelos.", marca.nome)
                    continue

                for modelo_raw in modelos:
                    modelo = upsert_modelo(db, marca.id, modelo_raw["nome"], modelo_raw["url"])

                    # ── Nível modelo: listar versões ────────────────────────
                    try:
                        versoes = scraper.listar_versoes(modelo_raw["url"])
                        resolver_erro_se_existir(db, modelo_raw["url"])
                    except Exception as exc:
                        registrar_erro(
                            db, url=modelo_raw["url"], etapa="listar_versoes", exc=exc,
                            contexto=f"{marca.nome} > {modelo.nome}",
                        )
                        db.commit()
                        falhas += 1
                        logger.warning(
                            "Pulando modelo '%s > %s' — não deu pra listar as versões.",
                            marca.nome, modelo.nome,
                        )
                        continue

                    # ── Nível versão: cada uma é isolada por SAVEPOINT ──────
                    for versao_raw in versoes:
                        existe = db.query(Versao).filter_by(url=versao_raw["url"]).first()
                        if existe:
                            continue

                        if _processar_versao(db, scraper, marca, modelo, versao_raw):
                            novos += 1
                        else:
                            falhas += 1

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
        novos, falhas, pendentes,
    )
    if pendentes:
        logger.info(
            "Consulte o motivo de cada um via GET /api/v1/scrape-erros "
            "ou: SELECT url, etapa, tipo_erro, mensagem, tentativas FROM scrape_erros;"
        )


if __name__ == "__main__":
    sync()
