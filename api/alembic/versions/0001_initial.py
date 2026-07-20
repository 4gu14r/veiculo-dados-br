"""initial schema

Revision ID: 0001
Revises:
Create Date: 2025-01-01 00:00:00
"""

import sqlalchemy as sa
from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── marcas ────────────────────────────────────────────────────────────────
    op.create_table(
        "marcas",
        sa.Column("id",        sa.Integer(),                  primary_key=True, autoincrement=True),
        sa.Column("nome",      sa.String(100),                nullable=False),
        sa.Column("criado_em", sa.DateTime(timezone=True),    server_default=sa.func.now()),
        sa.UniqueConstraint("nome", name="uq_marcas_nome"),
    )
    op.create_index("ix_marcas_nome", "marcas", ["nome"])

    # ── modelos ───────────────────────────────────────────────────────────────
    op.create_table(
        "modelos",
        sa.Column("id",        sa.Integer(),                  primary_key=True, autoincrement=True),
        sa.Column("marca_id",  sa.Integer(),                  sa.ForeignKey("marcas.id",  ondelete="CASCADE"), nullable=False),
        sa.Column("nome",      sa.String(150),                nullable=False),
        sa.Column("url",       sa.Text(),                     nullable=False),
        sa.Column("criado_em", sa.DateTime(timezone=True),    server_default=sa.func.now()),
        sa.UniqueConstraint("marca_id", "nome", name="uq_modelos_marca_nome"),
    )
    op.create_index("ix_modelos_marca_id", "modelos", ["marca_id"])
    op.create_index("ix_modelos_nome",     "modelos", ["nome"])

    # ── modelos_anos ──────────────────────────────────────────────────────────
    op.create_table(
        "modelos_anos",
        sa.Column("id",        sa.Integer(),                  primary_key=True, autoincrement=True),
        sa.Column("modelo_id", sa.Integer(),                  sa.ForeignKey("modelos.id", ondelete="CASCADE"), nullable=False),
        sa.Column("ano",       sa.Integer(),                  nullable=False),
        sa.Column("criado_em", sa.DateTime(timezone=True),    server_default=sa.func.now()),
        sa.UniqueConstraint("modelo_id", "ano", name="uq_modelos_anos_modelo_ano"),
    )
    op.create_index("ix_modelos_anos_modelo_id", "modelos_anos", ["modelo_id"])
    op.create_index("ix_modelos_anos_ano",        "modelos_anos", ["ano"])

    # ── versoes ───────────────────────────────────────────────────────────────
    op.create_table(
        "versoes",
        sa.Column("id",            sa.Integer(),               primary_key=True, autoincrement=True),
        sa.Column("modelo_ano_id", sa.Integer(),               sa.ForeignKey("modelos_anos.id", ondelete="CASCADE"), nullable=False),
        sa.Column("versao",        sa.String(200),             nullable=False),
        sa.Column("url",           sa.Text(),                  nullable=False),
        sa.Column("criado_em",     sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("modelo_ano_id", "versao", name="uq_versoes_modelo_ano_versao"),
        sa.UniqueConstraint("url", name="uq_versoes_url"),
    )
    op.create_index("ix_versoes_modelo_ano_id", "versoes", ["modelo_ano_id"])

    # ── versoes_detalhes ──────────────────────────────────────────────────────
    op.create_table(
        "versoes_detalhes",
        sa.Column("id",        sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("versao_id", sa.Integer(), sa.ForeignKey("versoes.id", ondelete="CASCADE"), nullable=False, unique=True),

        # Combustível
        sa.Column("combustivel",               sa.String(50)),
        sa.Column("tanque_litros",             sa.Float()),

        # Consumo
        sa.Column("consumo_cidade_alcool",     sa.Float()),
        sa.Column("consumo_cidade_gasolina",   sa.Float()),
        sa.Column("consumo_estrada_alcool",    sa.Float()),
        sa.Column("consumo_estrada_gasolina",  sa.Float()),

        # Motor
        sa.Column("cilindrada_cm3",            sa.Integer()),
        sa.Column("cilindros",                 sa.String(50)),
        sa.Column("velocidade_max_kmh",        sa.Integer()),
        sa.Column("zero_a_cem_segundos",       sa.Float()),

        # Dimensões
        sa.Column("comprimento_mm",            sa.Integer()),
        sa.Column("largura_mm",                sa.Integer()),
        sa.Column("altura_mm",                 sa.Integer()),
        sa.Column("entre_eixos_mm",            sa.Integer()),
        sa.Column("peso_kg",                   sa.Integer()),
        sa.Column("porta_malas_litros",        sa.Integer()),

        # Transmissão
        sa.Column("cambio",                    sa.String(100)),
        sa.Column("tracao",                    sa.String(50)),

        # Suspensão
        sa.Column("suspensao_dianteira",       sa.String(150)),
        sa.Column("suspensao_traseira",        sa.String(150)),

        # Freios
        sa.Column("freio_dianteiro",           sa.String(100)),
        sa.Column("freio_traseiro",            sa.String(100)),

        sa.Column("atualizado_em", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("versoes_detalhes")
    op.drop_table("versoes")
    op.drop_table("modelos_anos")
    op.drop_table("modelos")
    op.drop_table("marcas")
