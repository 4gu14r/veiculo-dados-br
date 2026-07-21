from pydantic import BaseModel, ConfigDict

# ── Detalhe ────────────────────────────────────────────────────────────────────


class VersaoDetalheSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    combustivel: str | None = None
    tanque_litros: float | None = None

    consumo_cidade_alcool: float | None = None
    consumo_cidade_gasolina: float | None = None
    consumo_estrada_alcool: float | None = None
    consumo_estrada_gasolina: float | None = None

    cilindrada_cm3: int | None = None
    cilindros: str | None = None
    velocidade_max_kmh: int | None = None
    zero_a_cem_segundos: float | None = None

    comprimento_mm: int | None = None
    largura_mm: int | None = None
    altura_mm: int | None = None
    entre_eixos_mm: int | None = None
    peso_kg: int | None = None
    porta_malas_litros: int | None = None

    cambio: str | None = None
    tracao: str | None = None

    suspensao_dianteira: str | None = None
    suspensao_traseira: str | None = None

    freio_dianteiro: str | None = None
    freio_traseiro: str | None = None


# ── Versão ─────────────────────────────────────────────────────────────────────


class VersaoResumida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    versao: str
    url: str


class VersaoCompleta(VersaoResumida):
    detalhe: VersaoDetalheSchema | None = None


# ── Ano ───────────────────────────────────────────────────────────────────────


class AnoResumido(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ano: int
    modelo_id: int


class AnoComVersoes(AnoResumido):
    versoes: list[VersaoResumida] = []


# ── Modelo ─────────────────────────────────────────────────────────────────────


class ModeloResumido(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    url: str
    marca_id: int


class ModeloComAnos(ModeloResumido):
    anos: list[AnoResumido] = []


# ── Marca ──────────────────────────────────────────────────────────────────────


class MarcaResumida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str


class MarcaComModelos(MarcaResumida):
    modelos: list[ModeloResumido] = []


# ── Paginação ──────────────────────────────────────────────────────────────────


class Pagina(BaseModel):
    total: int
    pagina: int
    limite: int
    paginas: int
