from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from api.core.database import get_db
from api.models.veiculo import Marca, Modelo
from api.schemas.veiculo import MarcaResumida, ModeloResumido

router = APIRouter()


@router.get(
    "",
    response_model=list[MarcaResumida],
    summary="Listar marcas",
    description="Retorna todas as marcas cadastradas. Suporta filtro por nome.",
)
def listar_marcas(
    q: str | None = Query(None, description="Filtrar por nome (parcial, case-insensitive)"),
    limite: int = Query(100, ge=1, le=200, description="Itens por página"),
    pagina: int = Query(1, ge=1, description="Número da página"),
    db: Session = Depends(get_db),
):
    stmt = select(Marca).order_by(Marca.nome)
    if q:
        stmt = stmt.where(Marca.nome.ilike(f"%{q}%"))
    stmt = stmt.offset((pagina - 1) * limite).limit(limite)
    return db.scalars(stmt).all()


@router.get(
    "/{marca_id}/modelos",
    response_model=list[ModeloResumido],
    summary="Modelos de uma marca",
    description="Retorna todos os modelos de uma determinada marca.",
)
def modelos_da_marca(
    marca_id: int,
    q: str | None = Query(None, description="Filtrar por nome do modelo"),
    limite: int = Query(100, ge=1, le=200),
    pagina: int = Query(1, ge=1),
    db: Session = Depends(get_db),
):
    if not db.get(Marca, marca_id):
        raise HTTPException(status_code=404, detail="Marca não encontrada.")

    stmt = (
        select(Modelo)
        .where(Modelo.marca_id == marca_id)
        .order_by(Modelo.nome)
        .offset((pagina - 1) * limite)
        .limit(limite)
    )
    if q:
        stmt = stmt.where(Modelo.nome.ilike(f"%{q}%"))
    return db.scalars(stmt).all()
