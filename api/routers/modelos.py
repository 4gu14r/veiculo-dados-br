from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from api.core.database import get_db
from api.models.veiculo import Modelo, ModeloAno
from api.schemas.veiculo import AnoResumido, ModeloResumido

router = APIRouter()


@router.get(
    "",
    response_model=list[ModeloResumido],
    summary="Listar modelos",
    description="Retorna todos os modelos. Filtre por nome ou por marca.",
)
def listar_modelos(
    q:        str | None = Query(None, description="Filtrar por nome (parcial, case-insensitive)"),
    marca_id: int | None = Query(None, description="Filtrar por ID de marca"),
    limite:   int        = Query(100, ge=1, le=200),
    pagina:   int        = Query(1, ge=1),
    db:       Session    = Depends(get_db),
):
    stmt = select(Modelo).order_by(Modelo.nome)
    if q:
        stmt = stmt.where(Modelo.nome.ilike(f"%{q}%"))
    if marca_id:
        stmt = stmt.where(Modelo.marca_id == marca_id)
    stmt = stmt.offset((pagina - 1) * limite).limit(limite)
    return db.scalars(stmt).all()


@router.get(
    "/{modelo_id}/anos",
    response_model=list[AnoResumido],
    summary="Anos disponíveis de um modelo",
    description="Retorna todos os anos com versões cadastradas para este modelo.",
)
def anos_do_modelo(
    modelo_id: int,
    limite:    int     = Query(100, ge=1, le=200),
    pagina:    int     = Query(1, ge=1),
    db:        Session = Depends(get_db),
):
    if not db.get(Modelo, modelo_id):
        raise HTTPException(status_code=404, detail="Modelo não encontrado.")

    stmt = (
        select(ModeloAno)
        .where(ModeloAno.modelo_id == modelo_id)
        .order_by(ModeloAno.ano.desc())
        .offset((pagina - 1) * limite)
        .limit(limite)
    )
    return db.scalars(stmt).all()