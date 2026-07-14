# api/models.py
from typing import List, Optional
from sqlmodel import Field, Relationship, SQLModel

# ==========================================
# 1. MARCA
# ==========================================
class MarcaBase(SQLModel):
    nome: str = Field(index=True, unique=True)

class Marca(MarcaBase, table=True):
    __tablename__ = "marcas"
    id: Optional[int] = Field(default=None, primary_key=True)
    
    modelos: List["Modelo"] = Relationship(back_populates="marca", cascade_delete=True)

class MarcaRead(MarcaBase):
    id: int

# ==========================================
# 2. MODELO
# ==========================================
class ModeloBase(SQLModel):
    nome: str = Field(index=True)
    url: Optional[str] = None
    marca_id: int = Field(foreign_key="marcas.id")

class Modelo(ModeloBase, table=True):
    __tablename__ = "modelos"
    id: Optional[int] = Field(default=None, primary_key=True)
    
    marca: Marca = Relationship(back_populates="modelos")
    anos: List["ModeloAno"] = Relationship(back_populates="modelo", cascade_delete=True)

class ModeloRead(ModeloBase):
    id: int

# ==========================================
# 3. MODELO ANO
# ==========================================
class ModeloAnoBase(SQLModel):
    ano: int = Field(index=True)
    modelo_id: int = Field(foreign_key="modelos.id")

class ModeloAno(ModeloAnoBase, table=True):
    __tablename__ = "modelos_anos"
    id: Optional[int] = Field(default=None, primary_key=True)
    
    modelo: Modelo = Relationship(back_populates="anos")
    versoes: List["Versao"] = Relationship(back_populates="modelo_ano", cascade_delete=True)

class ModeloAnoRead(ModeloAnoBase):
    id: int

# ==========================================
# 4. VERSÃO
# ==========================================
class VersaoBase(SQLModel):
    versao: str = Field(index=True)
    url: Optional[str] = None
    modelo_ano_id: int = Field(foreign_key="modelos_anos.id")

class Versao(VersaoBase, table=True):
    __tablename__ = "versoes"
    id: Optional[int] = Field(default=None, primary_key=True)
    
    modelo_ano: ModeloAno = Relationship(back_populates="versoes")
    detalhes: Optional["VersaoDetalhe"] = Relationship(back_populates="versao", cascade_delete=True)

class VersaoRead(VersaoBase):
    id: int

# ==========================================
# 5. DETALHES DA VERSÃO
# ==========================================
class VersaoDetalheBase(SQLModel):
    # Geral
    combustivel: Optional[str] = None
    tanque_litros: Optional[float] = None
    
    # Consumo
    consumo_cidade_alcool: Optional[float] = None
    consumo_cidade_gasolina: Optional[float] = None
    consumo_estrada_alcool: Optional[float] = None
    consumo_estrada_gasolina: Optional[float] = None
    
    # Motor
    cilindrada_cm3: Optional[int] = None
    cilindros: Optional[str] = None
    velocidade_max_kmh: Optional[int] = None
    zero_a_cem_segundos: Optional[float] = None
    
    # Dimensões
    comprimento_mm: Optional[int] = None
    largura_mm: Optional[int] = None
    altura_mm: Optional[int] = None
    entre_eixos_mm: Optional[int] = None
    peso_kg: Optional[int] = None
    porta_malas_litros: Optional[int] = None
    
    # Transmissão
    cambio: Optional[str] = None
    tracao: Optional[str] = None
    
    # Suspensão
    suspensao_dianteira: Optional[str] = None
    suspensao_traseira: Optional[str] = None
    
    # Freios
    freio_dianteiro: Optional[str] = None
    freio_traseiro: Optional[str] = None

class VersaoDetalhe(VersaoDetalheBase, table=True):
    __tablename__ = "versoes_detalhes"
    id: Optional[int] = Field(default=None, primary_key=True)
    versao_id: int = Field(foreign_key="versoes.id", unique=True)
    
    versao: Versao = Relationship(back_populates="detalhes")

class VersaoDetalheRead(VersaoDetalheBase):
    id: int
    versao_id: int

# ==========================================
# 🔄 EVITANDO LOOPINGS NAS RELAÇÕES (FORWARD REFS)
# ==========================================
# Definimos visualizações lineares. Nenhuma delas aponta "para trás"

class VersaoReadWithDetalhes(VersaoRead):
    detalhes: Optional[VersaoDetalheRead] = None

class ModeloAnoReadWithVersoes(ModeloAnoRead):
    versoes: List[VersaoReadWithDetalhes] = []

class ModeloReadWithAnos(ModeloRead):
    anos: List[ModeloAnoReadWithVersoes] = []

class MarcaReadWithModelos(MarcaRead):
    modelos: List[ModeloReadWithAnos] = []

# Diz para o Pydantic recalcular as referências de forma segura
MarcaReadWithModelos.model_rebuild()
ModeloReadWithAnos.model_rebuild()
ModeloAnoReadWithVersoes.model_rebuild()
VersaoReadWithDetalhes.model_rebuild()