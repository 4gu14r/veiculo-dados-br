# api/routers/marcas.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from typing import List

from database.database import get_session
from api.models import Marca, MarcaBase, MarcaRead, MarcaReadWithModelos

router = APIRouter(prefix="/marcas", tags=["Marcas"])

@router.get("/", response_model=List[MarcaReadWithModelos])  # 🌟 Retorna a árvore completa sem loop!
def listar_marcas(session: Session = Depends(get_session)):
    marcas = session.exec(select(Marca)).all()
    return marcas

@router.post("/", response_model=MarcaRead, status_code=status.HTTP_201_CREATED)
def cadastrar_marca(marca_payload: MarcaBase, session: Session = Depends(get_session)):
    marca_existente = session.exec(
        select(Marca).where(Marca.nome == marca_payload.nome)
    ).first()
    
    if marca_existente:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Esta marca já está cadastrada."
        )
    
    nova_marca = Marca(nome=marca_payload.nome)
    session.add(nova_marca)
    session.commit()
    session.refresh(nova_marca)
    return nova_marca