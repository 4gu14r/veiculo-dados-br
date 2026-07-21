from datetime import datetime

from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api.core.database import Base


class Marca(Base):
    __tablename__ = "marcas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nome: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    modelos: Mapped[list["Modelo"]] = relationship(
        back_populates="marca", cascade="all, delete-orphan"
    )


class Modelo(Base):
    __tablename__ = "modelos"
    __table_args__ = (UniqueConstraint("marca_id", "nome"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    marca_id: Mapped[int] = mapped_column(
        ForeignKey("marcas.id", ondelete="CASCADE"), nullable=False, index=True
    )
    nome: Mapped[str] = mapped_column(String(150), nullable=False, index=True)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    marca: Mapped["Marca"] = relationship(back_populates="modelos")
    anos: Mapped[list["ModeloAno"]] = relationship(
        back_populates="modelo", cascade="all, delete-orphan"
    )


class ModeloAno(Base):
    __tablename__ = "modelos_anos"
    __table_args__ = (UniqueConstraint("modelo_id", "ano"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    modelo_id: Mapped[int] = mapped_column(
        ForeignKey("modelos.id", ondelete="CASCADE"), nullable=False, index=True
    )
    ano: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    modelo: Mapped["Modelo"] = relationship(back_populates="anos")
    versoes: Mapped[list["Versao"]] = relationship(
        back_populates="modelo_ano", cascade="all, delete-orphan"
    )


class Versao(Base):
    __tablename__ = "versoes"
    __table_args__ = (UniqueConstraint("modelo_ano_id", "versao"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    modelo_ano_id: Mapped[int] = mapped_column(
        ForeignKey("modelos_anos.id", ondelete="CASCADE"), nullable=False, index=True
    )
    versao: Mapped[str] = mapped_column(String(200), nullable=False)
    url: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    modelo_ano: Mapped["ModeloAno"] = relationship(back_populates="versoes")
    detalhe: Mapped["VersaoDetalhe"] = relationship(
        back_populates="versao", uselist=False, cascade="all, delete-orphan"
    )


class VersaoDetalhe(Base):
    __tablename__ = "versoes_detalhes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    versao_id: Mapped[int] = mapped_column(
        ForeignKey("versoes.id", ondelete="CASCADE"), nullable=False, unique=True
    )

    # Combustível e tanque
    combustivel: Mapped[str | None] = mapped_column(String(50))
    tanque_litros: Mapped[float | None] = mapped_column(Float)

    # Consumo
    consumo_cidade_alcool: Mapped[float | None] = mapped_column(Float)
    consumo_cidade_gasolina: Mapped[float | None] = mapped_column(Float)
    consumo_estrada_alcool: Mapped[float | None] = mapped_column(Float)
    consumo_estrada_gasolina: Mapped[float | None] = mapped_column(Float)

    # Motor e desempenho
    cilindrada_cm3: Mapped[int | None] = mapped_column(Integer)
    cilindros: Mapped[str | None] = mapped_column(String(50))
    velocidade_max_kmh: Mapped[int | None] = mapped_column(Integer)
    zero_a_cem_segundos: Mapped[float | None] = mapped_column(Float)

    # Dimensões
    comprimento_mm: Mapped[int | None] = mapped_column(Integer)
    largura_mm: Mapped[int | None] = mapped_column(Integer)
    altura_mm: Mapped[int | None] = mapped_column(Integer)
    entre_eixos_mm: Mapped[int | None] = mapped_column(Integer)
    peso_kg: Mapped[int | None] = mapped_column(Integer)
    porta_malas_litros: Mapped[int | None] = mapped_column(Integer)

    # Transmissão e tração
    cambio: Mapped[str | None] = mapped_column(String(100))
    tracao: Mapped[str | None] = mapped_column(String(50))

    # Suspensão
    suspensao_dianteira: Mapped[str | None] = mapped_column(String(150))
    suspensao_traseira: Mapped[str | None] = mapped_column(String(150))

    # Freios
    freio_dianteiro: Mapped[str | None] = mapped_column(String(100))
    freio_traseiro: Mapped[str | None] = mapped_column(String(100))

    atualizado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    versao: Mapped["Versao"] = relationship(back_populates="detalhe")
