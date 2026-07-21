from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from api.core.database import Base


class ScrapeErro(Base):
    """
    Registra falhas ocorridas durante o scraping, para que:
      1. Fique visível o motivo de um veículo não ter sido adicionado
         (sem precisar vasculhar log de GitHub Actions, que expira).
      2. O próximo run saiba o que já falhou antes e quantas vezes.
      3. Quando o item finalmente for processado com sucesso, o registro
         de erro correspondente é removido automaticamente (ver scraper/erros.py).
    """

    __tablename__ = "scrape_erros"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    url: Mapped[str] = mapped_column(Text, nullable=False, unique=True, index=True)

    etapa: Mapped[str] = mapped_column(String(30), nullable=False)

    contexto: Mapped[str | None] = mapped_column(String(255))

    tipo_erro: Mapped[str] = mapped_column(String(100), nullable=False)
    mensagem: Mapped[str] = mapped_column(Text, nullable=False)

    tentativas: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    primeira_ocorrencia: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    ultima_ocorrencia: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
