# api/routers/importacao.py
from fastapi import APIRouter, Depends, status
from sqlmodel import Session, select
from database.database import get_session
from api.models import Marca, Modelo, ModeloAno, Versao, VersaoDetalhe
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter(prefix="/importar", tags=["Importação / Scraper"])

# ==========================================
# 📋 SCHEMAS DE ENTRADA (FORTEMENTE TIPADOS)
# ==========================================

class DetalheConsumo(BaseModel):
    alcool: Optional[float] = None
    gasolina: Optional[float] = None

class ConsumoSchema(BaseModel):
    cidade: Optional[DetalheConsumo] = None
    estrada: Optional[DetalheConsumo] = None

class MotorSchema(BaseModel):
    cilindrada_cm3: Optional[int] = None
    cilindros: Optional[str] = None
    velocidade_max_kmh: Optional[float] = None  # Aceita float com segurança
    zero_a_cem_segundos: Optional[float] = None

class DimensoesSchema(BaseModel):
    comprimento_mm: Optional[int] = None
    largura_mm: Optional[int] = None
    altura_mm: Optional[int] = None
    entre_eixos_mm: Optional[int] = None
    peso_kg: Optional[int] = None
    porta_malas_litros: Optional[int] = None

class TransmissaoSchema(BaseModel):
    cambio: Optional[str] = None
    tracao: Optional[str] = None

class SuspensaoSchema(BaseModel):
    dianteira: Optional[str] = None
    traseira: Optional[str] = None

class FreiosSchema(BaseModel):
    dianteiro: Optional[str] = None
    traseiro: Optional[str] = None

class DetalhesVersaoSchema(BaseModel):
    combustivel: Optional[str] = None
    tanque_litros: Optional[float] = None
    consumo: Optional[ConsumoSchema] = None
    motor: Optional[MotorSchema] = None
    dimensoes: Optional[DimensoesSchema] = None
    transmissao: Optional[TransmissaoSchema] = None
    suspensao: Optional[SuspensaoSchema] = None
    freios: Optional[FreiosSchema] = None

class VersaoImportSchema(BaseModel):
    id: Optional[int] = None
    versao: str
    url: Optional[str] = None
    detalhes: Optional[DetalhesVersaoSchema] = None

class AnoImportSchema(BaseModel):
    ano: int
    versoes: List[VersaoImportSchema]

class ModeloImportSchema(BaseModel):
    id: Optional[int] = None
    nome: str
    url: Optional[str] = None
    anos: List[AnoImportSchema]

class MarcaImportSchema(BaseModel):
    id: Optional[int] = None
    nome: str
    modelos: List[ModeloImportSchema]


# ==========================================
# 📋 SCHEMA DE RETORNO (RESPOSTA)
# ==========================================
class ImportacaoResponse(BaseModel):
    status: str
    mensagem: str


# ==========================================
# 🚀 ROTA DE IMPORTAÇÃO RESILIENTE (UPSERT)
# ==========================================
@router.post("/", status_code=status.HTTP_201_CREATED, response_model=ImportacaoResponse)
def importar_dados_scraper(payload: List[MarcaImportSchema], session: Session = Depends(get_session)):
    """
    Recebe o JSON aninhado do scraper e popula o banco de dados de forma resiliente.
    Usa a estratégia de Upsert (atualiza se já existir) para evitar erros de restrição de chave única.
    """
    contagem_marcas = 0
    contagem_versoes = 0

    for marca_data in payload:
        marca_nome = marca_data.nome
        if not marca_nome:
            continue
        
        # 1. Busca ou cria a Marca
        marca = session.exec(select(Marca).where(Marca.nome == marca_nome)).first()
        if not marca:
            marca = Marca(nome=marca_nome)
            session.add(marca)
            session.flush()
            contagem_marcas += 1

        for modelo_data in marca_data.modelos:
            modelo_nome = modelo_data.nome
            # 2. Busca ou cria o Modelo dentro da Marca
            modelo = session.exec(
                select(Modelo).where(Modelo.nome == modelo_nome, Modelo.marca_id == marca.id)
            ).first()
            if not modelo:
                modelo = Modelo(nome=modelo_nome, url=modelo_data.url, marca_id=marca.id)
                session.add(modelo)
                session.flush()

            for ano_data in modelo_data.anos:
                ano_val = ano_data.ano
                # 3. Busca ou cria o Ano do Modelo
                modelo_ano = session.exec(
                    select(ModeloAno).where(ModeloAno.ano == ano_val, ModeloAno.modelo_id == modelo.id)
                ).first()
                if not modelo_ano:
                    modelo_ano = ModeloAno(ano=ano_val, modelo_id=modelo.id)
                    session.add(modelo_ano)
                    session.flush()

                for versao_data in ano_data.versoes:
                    versao_nome = versao_data.versao
                    # 4. Busca ou cria a Versão
                    versao = session.exec(
                        select(Versao).where(Versao.versao == versao_nome, Versao.modelo_ano_id == modelo_ano.id)
                    ).first()
                    if not versao:
                        versao = Versao(versao=versao_nome, url=versao_data.url, modelo_ano_id=modelo_ano.id)
                        session.add(versao)
                        session.flush()
                        contagem_versoes += 1

                    # 5. Estratégia de Upsert para a Ficha Técnica (Evita erros 500 de conflito)
                    detalhes_data = versao_data.detalhes
                    if detalhes_data:
                        consumo = detalhes_data.consumo
                        motor = detalhes_data.motor
                        dimensoes = detalhes_data.dimensoes
                        transmissao = detalhes_data.transmissao
                        suspensao = detalhes_data.suspensao
                        freios = detalhes_data.freios

                        # Mapeia todos os campos coletados do JSON
                        campos_detalhe = {
                            "combustivel": detalhes_data.combustivel,
                            "tanque_litros": detalhes_data.tanque_litros,
                            
                            "consumo_cidade_alcool": consumo.cidade.alcool if (consumo and consumo.cidade) else None,
                            "consumo_cidade_gasolina": consumo.cidade.gasolina if (consumo and consumo.cidade) else None,
                            "consumo_estrada_alcool": consumo.estrada.alcool if (consumo and consumo.estrada) else None,
                            "consumo_estrada_gasolina": consumo.estrada.gasolina if (consumo and consumo.estrada) else None,
                            
                            "cilindrada_cm3": motor.cilindrada_cm3 if motor else None,
                            "cilindros": motor.cilindros if motor else None,
                            "velocidade_max_kmh": int(round(motor.velocidade_max_kmh)) if (motor and motor.velocidade_max_kmh is not None) else None,
                            "zero_a_cem_segundos": motor.zero_a_cem_segundos if motor else None,
                            
                            "comprimento_mm": dimensoes.comprimento_mm if dimensoes else None,
                            "largura_mm": dimensoes.largura_mm if dimensoes else None,
                            "altura_mm": dimensoes.altura_mm if dimensoes else None,
                            "entre_eixos_mm": dimensoes.entre_eixos_mm if dimensoes else None,
                            "peso_kg": dimensoes.peso_kg if dimensoes else None,
                            "porta_malas_litros": dimensoes.porta_malas_litros if dimensoes else None,
                            
                            "cambio": transmissao.cambio if transmissao else None,
                            "tracao": transmissao.tracao if transmissao else None,
                            
                            "suspensao_dianteira": suspensao.dianteira if suspensao else None,
                            "suspensao_traseira": suspensao.traseira if suspensao else None,
                            
                            "freio_dianteiro": freios.dianteiro if freios else None,
                            "freio_traseiro": freios.traseiro if freios else None
                        }

                        # Verifica se a ficha técnica já existe para esta versão
                        detalhe_existente = session.exec(
                            select(VersaoDetalhe).where(VersaoDetalhe.versao_id == versao.id)
                        ).first()

                        if detalhe_existente:
                            # 🌟 UPDATE: Atualiza os campos do registro existente sem alterar a chave primária
                            for chave, valor in campos_detalhe.items():
                                setattr(detalhe_existente, chave, valor)
                            session.add(detalhe_existente)
                        else:
                            # 🌟 INSERT: Cria do zero se não existia
                            novo_detalhe = VersaoDetalhe(versao_id=versao.id, **campos_detalhe)
                            session.add(novo_detalhe)

    session.commit()
    return ImportacaoResponse(
        status="sucesso",
        mensagem=f"Importação concluída! {contagem_marcas} novas marcas e {contagem_versoes} novas versões processadas."
    )