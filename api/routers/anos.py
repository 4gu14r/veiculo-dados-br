from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from api.core.database import get_db
from api.models.veiculo import ModeloAno, Versao
from api.schemas.veiculo import AnoResumido, VersaoResumida

router = APIRouter()


@router.get(
    "/{ano_id}",
    response_model=AnoResumido,
    summary="Detalhe de um ano",
)
def detalhe_ano(ano_id: int, db: Session = Depends(get_db)):
    ano = db.get(ModeloAno, ano_id)
    if not ano:
        raise HTTPException(status_code=404, detail="Ano não encontrado.")
    return ano


@router.get(
    "/{ano_id}/versoes",
    response_model=list[VersaoResumida],
    summary="Versões de um modelo/ano",
    description="Retorna todas as versões disponíveis para este modelo no ano informado.",
)
def versoes_do_ano(
    ano_id:  int,
    limite:  int     = Query(100, ge=1, le=200),
    pagina:  int     = Query(1, ge=1),
    db:      Session = Depends(get_db),
):
    if not db.get(ModeloAno, ano_id):
        raise HTTPException(status_code=404, detail="Ano não encontrado.")

    stmt = (
        select(Versao)
        .where(Versao.modelo_ano_id == ano_id)
        .order_by(Versao.versao)
        .offset((pagina - 1) * limite)
        .limit(limite)
    )
    return db.scalars(stmt).all()
