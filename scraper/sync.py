"""
Scraping incremental — roda via GitHub Actions toda semana.

Lógica:
  1. Percorre marcas → modelos → anos/versões (só listagens, rápido)
  2. Para cada versão verifica pela URL se já existe no banco
  3. Se não existe → baixa a ficha técnica e insere
  4. Se existe     → pula (sem rebaixar a performance revisitando fichas antigas)
"""

import logging
import sys

# Garante que o root do projeto está no path ao rodar via `python -m scraper.sync`
sys.path.insert(0, ".")

from sqlalchemy.orm import Session

from api.core.database import SessionLocal
from api.models.veiculo import Marca, Modelo, ModeloAno, Versao, VersaoDetalhe
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


def sync() -> None:
    db: Session = SessionLocal()
    novos = 0
    erros = 0

    try:
        with FichaCompletaScraper(delay=1.5) as scraper:
            marcas = scraper.listar_marcas()
            logger.info("Total de marcas encontradas: %d", len(marcas))

            for marca_raw in marcas:
                marca = upsert_marca(db, marca_raw["nome"])

                modelos = scraper.listar_modelos(marca_raw["url"])
                for modelo_raw in modelos:
                    modelo = upsert_modelo(db, marca.id, modelo_raw["nome"], modelo_raw["url"])

                    versoes = scraper.listar_versoes(modelo_raw["url"])
                    for versao_raw in versoes:
                        # ── Verifica se já existe pela URL (chave estável) ────
                        existe = db.query(Versao).filter_by(url=versao_raw["url"]).first()
                        if existe:
                            continue

                        logger.info(
                            "Novo: %s › %s › %s › %s",
                            marca.nome, modelo.nome,
                            versao_raw["ano"], versao_raw["versao"],
                        )

                        try:
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
                            novos += 1

                        except Exception as exc:
                            logger.warning("Erro ao processar %s: %s", versao_raw["url"], exc)
                            erros += 1
                            db.rollback()
                            continue

                db.commit()

    except Exception:
        db.rollback()
        logger.exception("Erro fatal durante o sync")
        raise
    finally:
        db.close()

    logger.info("Sync concluído — %d novas versões inseridas | %d erros", novos, erros)


if __name__ == "__main__":
    sync()
