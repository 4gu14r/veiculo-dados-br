from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from api.core.database import get_db
from api.models.scrape_erro import ScrapeErro
from api.models.scrape_erro import ScrapeErroSchema

router = APIRouter()


@router.get(
    "",
    response_model=list[ScrapeErroSchema],
    summary="Listar erros pendentes do scraper",
    description=(
        "Itens que o scraper tentou processar e falhou, com o motivo exato "
        "(mensagem da exceção) e em qual etapa aconteceu. Um item some dessa "
        "lista automaticamente assim que for processado com sucesso num "
        "próximo run — ou seja, o que aparece aqui é sempre o que está "
        "pendente agora."
    ),
)
def listar_erros(
    etapa: str | None = Query(
        None,
        description="Filtrar por etapa: listar_modelos, listar_versoes ou detalhe_versao",
    ),
    limite: int = Query(100, ge=1, le=200),
    pagina: int = Query(1, ge=1),
    db: Session = Depends(get_db),
):
    stmt = select(ScrapeErro).order_by(ScrapeErro.ultima_ocorrencia.desc())
    if etapa:
        stmt = stmt.where(ScrapeErro.etapa == etapa)
    stmt = stmt.offset((pagina - 1) * limite).limit(limite)
    return db.scalars(stmt).all()
