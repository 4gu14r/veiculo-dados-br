"""create scrape_erros table

Revision ID: 0002
Revises: 0001
Create Date: 2025-02-01 00:00:00
"""

import sqlalchemy as sa
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "scrape_erros",
        sa.Column("id",  sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("etapa", sa.String(30), nullable=False),
        sa.Column("contexto", sa.String(255)),
        sa.Column("tipo_erro", sa.String(100), nullable=False),
        sa.Column("mensagem", sa.Text(), nullable=False),
        sa.Column("tentativas", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("primeira_ocorrencia", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("ultima_ocorrencia",   sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("url", name="uq_scrape_erros_url"),
    )
    op.create_index("ix_scrape_erros_url", "scrape_erros", ["url"])


def downgrade() -> None:
    op.drop_table("scrape_erros")
