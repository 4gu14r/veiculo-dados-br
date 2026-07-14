# api/routers/modelos.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from typing import List

from database.database import get_session
# 🌟 IMPORTANTE: Adicionei "Versao" (ou o nome exato do seu model de versão) no import abaixo
from api.models import Modelo, Marca, Versao 

router = APIRouter(prefix="/modelos", tags=["Modelos"])

@router.get("/", response_model=List[Modelo])
def listar_modelos(session: Session = Depends(get_session)):
    """
    Lista todos os modelos de veículos cadastrados no banco.
    """
    modelos = session.exec(select(Modelo)).all()
    return modelos

@router.post("/", response_model=Modelo, status_code=status.HTTP_201_CREATED)
def cadastrar_modelo(modelo_payload: Modelo, session: Session = Depends(get_session)):
    """
    Cadastra um novo modelo de veículo vinculado a uma marca existente.
    """
    marca = session.get(Marca, modelo_payload.marca_id)
    if not marca:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Não é possível cadastrar o modelo. A Marca com ID {modelo_payload.marca_id} não existe."
        )

    novo_modelo = Modelo(
        nome=modelo_payload.nome,
        url=modelo_payload.url,
        marca_id=modelo_payload.marca_id
    )

    session.add(novo_modelo)
    session.commit()
    session.refresh(novo_modelo)
    return novo_modelo


# ==========================================
# 🌟 NOVA ROTA: LISTAR VERSÕES DE UM MODELO
# ==========================================
@router.get("/{modelo_id}/versoes", response_model=List[Versao], status_code=status.HTTP_200_OK)
def listar_versoes_de_um_modelo(modelo_id: int, session: Session = Depends(get_session)):
    """
    Retorna todas as versões cadastradas para um modelo específico.
    """
    # 1. Verifica se o modelo existe no banco
    modelo = session.get(Modelo, modelo_id)
    if not modelo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Modelo com ID {modelo_id} não foi encontrado no catálogo."
        )

    # 2. Busca as versões atreladas a ele
    versoes = session.exec(
        select(Versao).where(Versao.modelo_id == modelo_id).order_by(Versao.nome)
    ).all()

    return versoes