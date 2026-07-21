from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ScrapeErroSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    url: str
    etapa: str
    contexto: str | None = None
    tipo_erro: str
    mensagem: str
    tentativas: int
    primeira_ocorrencia: datetime
    ultima_ocorrencia: datetime
