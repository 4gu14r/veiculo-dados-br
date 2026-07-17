"""
Testes de integração dos endpoints da API.
Cada teste usa o banco SQLite in-memory via conftest.py.
"""

from api.models.veiculo import Marca, Modelo, ModeloAno, Versao, VersaoDetalhe


# ── Helpers ────────────────────────────────────────────────────────────────────

def criar_marca(db, nome="Fiat") -> Marca:
    m = Marca(nome=nome)
    db.add(m)
    db.flush()
    return m


def criar_modelo(db, marca_id: int, nome="Uno", url="http://exemplo.com/uno") -> Modelo:
    m = Modelo(marca_id=marca_id, nome=nome, url=url)
    db.add(m)
    db.flush()
    return m


def criar_ano(db, modelo_id: int, ano=2020) -> ModeloAno:
    ma = ModeloAno(modelo_id=modelo_id, ano=ano)
    db.add(ma)
    db.flush()
    return ma


def criar_versao(db, modelo_ano_id: int, versao="Fire 1.0", url="http://exemplo.com/fire") -> Versao:
    v = Versao(modelo_ano_id=modelo_ano_id, versao=versao, url=url)
    db.add(v)
    db.flush()
    return v


def criar_detalhe(db, versao_id: int) -> VersaoDetalhe:
    d = VersaoDetalhe(
        versao_id=versao_id,
        combustivel="Gasolina",
        tanque_litros=48.0,
        consumo_cidade_gasolina=11.5,
        consumo_estrada_gasolina=14.2,
        cilindrada_cm3=999,
        velocidade_max_kmh=160,
        peso_kg=920,
    )
    db.add(d)
    db.flush()
    return d


# ── Health ─────────────────────────────────────────────────────────────────────

def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


# ── Marcas ─────────────────────────────────────────────────────────────────────

def test_listar_marcas_vazio(client):
    r = client.get("/api/v1/marcas")
    assert r.status_code == 200
    assert r.json() == []


def test_listar_marcas(client, db):
    criar_marca(db, "Fiat")
    criar_marca(db, "Volkswagen")
    db.commit()
    r = client.get("/api/v1/marcas")
    assert r.status_code == 200
    nomes = [m["nome"] for m in r.json()]
    assert "Fiat" in nomes
    assert "Volkswagen" in nomes


def test_listar_marcas_filtro(client, db):
    criar_marca(db, "Fiat")
    criar_marca(db, "Ford")
    db.commit()
    r = client.get("/api/v1/marcas?q=fia")
    assert r.status_code == 200
    assert len(r.json()) == 1
    assert r.json()[0]["nome"] == "Fiat"


def test_detalhe_marca(client, db):
    marca = criar_marca(db)
    db.commit()
    r = client.get(f"/api/v1/marcas/{marca.id}")
    assert r.status_code == 200
    assert r.json()["nome"] == "Fiat"


def test_marca_nao_encontrada(client):
    r = client.get("/api/v1/marcas/9999")
    assert r.status_code == 404


def test_modelos_da_marca(client, db):
    marca = criar_marca(db)
    criar_modelo(db, marca.id, "Uno")
    criar_modelo(db, marca.id, "Palio")
    db.commit()
    r = client.get(f"/api/v1/marcas/{marca.id}/modelos")
    assert r.status_code == 200
    assert len(r.json()) == 2


# ── Modelos ────────────────────────────────────────────────────────────────────

def test_listar_modelos(client, db):
    marca = criar_marca(db)
    criar_modelo(db, marca.id)
    db.commit()
    r = client.get("/api/v1/modelos")
    assert r.status_code == 200
    assert len(r.json()) == 1


def test_detalhe_modelo(client, db):
    marca = criar_marca(db)
    modelo = criar_modelo(db, marca.id, "Gol")
    db.commit()
    r = client.get(f"/api/v1/modelos/{modelo.id}")
    assert r.status_code == 200
    assert r.json()["nome"] == "Gol"


def test_anos_do_modelo(client, db):
    marca = criar_marca(db)
    modelo = criar_modelo(db, marca.id)
    criar_ano(db, modelo.id, 2020)
    criar_ano(db, modelo.id, 2021)
    db.commit()
    r = client.get(f"/api/v1/modelos/{modelo.id}/anos")
    assert r.status_code == 200
    anos = [a["ano"] for a in r.json()]
    assert 2020 in anos
    assert 2021 in anos


# ── Anos ───────────────────────────────────────────────────────────────────────

def test_versoes_do_ano(client, db):
    marca = criar_marca(db)
    modelo = criar_modelo(db, marca.id)
    ano = criar_ano(db, modelo.id, 2022)
    criar_versao(db, ano.id, "1.0 Fire Flex", "http://a.com/1")
    criar_versao(db, ano.id, "1.4 Attractive", "http://a.com/2")
    db.commit()
    r = client.get(f"/api/v1/anos/{ano.id}/versoes")
    assert r.status_code == 200
    assert len(r.json()) == 2


# ── Versões ────────────────────────────────────────────────────────────────────

def test_detalhe_versao_com_ficha(client, db):
    marca  = criar_marca(db)
    modelo = criar_modelo(db, marca.id)
    ano    = criar_ano(db, modelo.id)
    versao = criar_versao(db, ano.id)
    criar_detalhe(db, versao.id)
    db.commit()

    r = client.get(f"/api/v1/versoes/{versao.id}")
    assert r.status_code == 200
    data = r.json()
    assert data["versao"] == "Fire 1.0"
    assert data["detalhe"]["combustivel"] == "Gasolina"
    assert data["detalhe"]["tanque_litros"] == 48.0
    assert data["detalhe"]["cilindrada_cm3"] == 999


def test_versao_nao_encontrada(client):
    r = client.get("/api/v1/versoes/9999")
    assert r.status_code == 404


def test_listar_versoes_por_ano(client, db):
    marca  = criar_marca(db)
    modelo = criar_modelo(db, marca.id)
    ano    = criar_ano(db, modelo.id, 2019)
    criar_versao(db, ano.id, "1.0", "http://x.com/1")
    db.commit()

    r = client.get("/api/v1/versoes?ano=2019")
    assert r.status_code == 200
    assert len(r.json()) == 1
