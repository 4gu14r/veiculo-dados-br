from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from api.core.database import get_db
from api.models.veiculo import Versao
from api.schemas.veiculo import VersaoCompleta, VersaoResumida

router = APIRouter()


@router.get(
    "",
    response_model=list[VersaoResumida],
    summary="Listar versões",
    description="Retorna versões com filtros opcionais por ano ou modelo.",
)
def listar_versoes(
    ano: int | None = Query(None, description="Filtrar por ano"),
    modelo_id: int | None = Query(None, description="Filtrar por ID do modelo"),
    limite: int = Query(100, ge=1, le=200),
    pagina: int = Query(1, ge=1),
    db: Session = Depends(get_db),
):
    stmt = select(Versao).order_by(Versao.versao)

    if ano or modelo_id:
        from api.models.veiculo import ModeloAno

        stmt = stmt.join(ModeloAno, Versao.modelo_ano_id == ModeloAno.id)
        if ano:
            stmt = stmt.where(ModeloAno.ano == ano)
        if modelo_id:
            stmt = stmt.where(ModeloAno.modelo_id == modelo_id)

    stmt = stmt.offset((pagina - 1) * limite).limit(limite)
    return db.scalars(stmt).all()


@router.get(
    "/{versao_id}",
    response_model=VersaoCompleta,
    summary="Ficha técnica completa de uma versão",
    description=(
        "Retorna todos os dados técnicos da versão: combustível, tanque, consumo, "
        "motor, dimensões, transmissão, suspensão e freios."
    ),
)
def detalhe_versao(versao_id: int, db: Session = Depends(get_db)):
    stmt = select(Versao).options(joinedload(Versao.detalhe)).where(Versao.id == versao_id)
    versao = db.scalars(stmt).first()
    if not versao:
        raise HTTPException(status_code=404, detail="Versão não encontrada.")
    return versao
