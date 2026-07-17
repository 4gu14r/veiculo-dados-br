"""
Migra o banco SQLite legado (veiculos.db) para o Postgres.

Uso:
    docker compose exec api python scripts/seed_from_sqlite.py /app/scripts/veiculos.db

Rode APENAS UMA VEZ após o primeiro `alembic upgrade head`.
O script é idempotente: usa ON CONFLICT DO NOTHING em tudo,
então pode ser interrompido e reexecutado sem duplicar dados.
"""

import re
import sys

import apsw  # pip install apsw
from sqlalchemy.orm import Session

# Garante que o root do projeto está no path
sys.path.insert(0, ".")

from api.core.database import SessionLocal
from api.models.veiculo import Marca, Modelo, ModeloAno, Versao, VersaoDetalhe


def limpar_texto(valor: str | None) -> str | None:
    """Remove whitespace e \r\n residuais do scraping original."""
    if valor is None:
        return None
    return re.sub(r"\s+", " ", valor.replace("\r", " ").replace("\t", " ")).strip()


def seed(sqlite_path: str) -> None:
    conn = apsw.Connection(sqlite_path)
    cur = conn.cursor()
    db: Session = SessionLocal()

    try:
        print("▶ Importando marcas...")
        marcas_map: dict[int, int] = {}  # sqlite_id -> postgres_id

        for (sqlite_id, nome) in cur.execute("SELECT id, nome FROM marcas ORDER BY id"):
            existing = db.query(Marca).filter_by(nome=nome).first()
            if not existing:
                marca = Marca(nome=nome)
                db.add(marca)
                db.flush()
            else:
                marca = existing
            marcas_map[sqlite_id] = marca.id

        db.commit()
        print(f"   ✓ {len(marcas_map)} marcas")

        # ── Modelos ───────────────────────────────────────────────────────────
        print("▶ Importando modelos...")
        modelos_map: dict[int, int] = {}

        rows = list(cur.execute("SELECT id, marca_id, nome, url FROM modelos ORDER BY id"))
        for (sqlite_id, sqlite_marca_id, nome, url) in rows:
            pg_marca_id = marcas_map[sqlite_marca_id]
            existing = db.query(Modelo).filter_by(marca_id=pg_marca_id, nome=nome).first()
            if not existing:
                modelo = Modelo(marca_id=pg_marca_id, nome=nome, url=url or "")
                db.add(modelo)
                db.flush()
            else:
                modelo = existing
            modelos_map[sqlite_id] = modelo.id

        db.commit()
        print(f"   ✓ {len(modelos_map)} modelos")

        # ── ModeloAno ─────────────────────────────────────────────────────────
        print("▶ Importando anos...")
        anos_map: dict[int, int] = {}

        rows = list(cur.execute("SELECT id, modelo_id, ano FROM modelos_anos ORDER BY id"))
        for (sqlite_id, sqlite_modelo_id, ano) in rows:
            pg_modelo_id = modelos_map[sqlite_modelo_id]
            existing = db.query(ModeloAno).filter_by(modelo_id=pg_modelo_id, ano=ano).first()
            if not existing:
                ma = ModeloAno(modelo_id=pg_modelo_id, ano=ano)
                db.add(ma)
                db.flush()
            else:
                ma = existing
            anos_map[sqlite_id] = ma.id

        db.commit()
        print(f"   ✓ {len(anos_map)} anos")

        # ── Versões + Detalhes ────────────────────────────────────────────────
        print("▶ Importando versões e fichas técnicas...")
        versoes_rows = list(cur.execute(
            "SELECT id, modelo_ano_id, versao, url FROM versoes ORDER BY id"
        ))
        detalhes_dict: dict[int, tuple] = {
            row[1]: row
            for row in cur.execute("SELECT * FROM versoes_detalhes ORDER BY versao_id")
        }

        total = 0
        for (sqlite_id, sqlite_ano_id, versao_nome, url) in versoes_rows:
            pg_ano_id = anos_map[sqlite_ano_id]
            existing = db.query(Versao).filter_by(url=url).first()
            if existing:
                continue

            v = Versao(
                modelo_ano_id=pg_ano_id,
                versao=versao_nome,
                url=url or "",
            )
            db.add(v)
            db.flush()

            # Detalhe
            d_row = detalhes_dict.get(sqlite_id)
            if d_row:
                (_, _, combustivel, tanque_litros,
                 consumo_cidade_alcool, consumo_cidade_gasolina,
                 consumo_estrada_alcool, consumo_estrada_gasolina,
                 cilindrada_cm3, cilindros, velocidade_max_kmh, zero_a_cem_segundos,
                 comprimento_mm, largura_mm, altura_mm, entre_eixos_mm, peso_kg, porta_malas_litros,
                 cambio, tracao, suspensao_dianteira, suspensao_traseira,
                 freio_dianteiro, freio_traseiro) = d_row

                db.add(VersaoDetalhe(
                    versao_id=v.id,
                    combustivel=limpar_texto(combustivel),
                    tanque_litros=tanque_litros,
                    consumo_cidade_alcool=consumo_cidade_alcool,
                    consumo_cidade_gasolina=consumo_cidade_gasolina,
                    consumo_estrada_alcool=consumo_estrada_alcool,
                    consumo_estrada_gasolina=consumo_estrada_gasolina,
                    cilindrada_cm3=cilindrada_cm3,
                    cilindros=limpar_texto(cilindros),
                    velocidade_max_kmh=velocidade_max_kmh,
                    zero_a_cem_segundos=zero_a_cem_segundos,
                    comprimento_mm=comprimento_mm,
                    largura_mm=largura_mm,
                    altura_mm=altura_mm,
                    entre_eixos_mm=entre_eixos_mm,
                    peso_kg=peso_kg,
                    porta_malas_litros=porta_malas_litros,
                    cambio=limpar_texto(cambio),
                    tracao=limpar_texto(tracao),
                    suspensao_dianteira=limpar_texto(suspensao_dianteira),
                    suspensao_traseira=limpar_texto(suspensao_traseira),
                    freio_dianteiro=limpar_texto(freio_dianteiro),
                    freio_traseiro=limpar_texto(freio_traseiro),
                ))

            total += 1
            if total % 500 == 0:
                db.commit()
                print(f"   ... {total} versões importadas")

        db.commit()
        print(f"   ✓ {total} versões com fichas técnicas")
        print("\n✅ Seed concluído com sucesso!")

    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
        conn.close()


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "scripts/veiculos.db"
    seed(path)
