"""
Testes do rastreamento de erros do scraper: scraper/erros.py + GET /api/v1/scrape-erros.
"""

from api.models.scrape_erro import ScrapeErro
from scraper.erros import registrar_erro, resolver_erro_se_existir


class ErroFalso(Exception):
    pass


# ── registrar_erro ──────────────────────────────────────────────────────────────


def test_registrar_erro_cria_registro(db):
    registrar_erro(
        db,
        url="http://x.com/1",
        etapa="detalhe_versao",
        exc=ErroFalso("html mudou"),
        contexto="Fiat > Uno",
    )
    db.commit()

    erro = db.query(ScrapeErro).filter_by(url="http://x.com/1").first()
    assert erro is not None
    assert erro.etapa == "detalhe_versao"
    assert erro.tipo_erro == "ErroFalso"
    assert erro.mensagem == "html mudou"
    assert erro.contexto == "Fiat > Uno"
    assert erro.tentativas == 1


def test_registrar_erro_na_mesma_url_incrementa_tentativas(db):
    registrar_erro(db, url="http://x.com/1", etapa="detalhe_versao", exc=ErroFalso("erro 1"))
    registrar_erro(db, url="http://x.com/1", etapa="detalhe_versao", exc=ErroFalso("erro 2"))
    db.commit()

    erros = db.query(ScrapeErro).filter_by(url="http://x.com/1").all()
    assert len(erros) == 1  # não duplica, atualiza o mesmo registro
    assert erros[0].tentativas == 2
    assert erros[0].mensagem == "erro 2"  # sempre reflete o motivo mais recente


# ── resolver_erro_se_existir ──────────────────────────────────────────────────


def test_resolver_erro_remove_registro_apos_sucesso(db):
    registrar_erro(db, url="http://x.com/1", etapa="detalhe_versao", exc=ErroFalso("erro"))
    db.commit()

    resolver_erro_se_existir(db, "http://x.com/1")
    db.commit()

    assert db.query(ScrapeErro).filter_by(url="http://x.com/1").first() is None


def test_resolver_erro_sem_registro_previo_nao_lanca_excecao(db):
    resolver_erro_se_existir(db, "http://nunca-falhou.com")  # não deve lançar nada


# ── GET /api/v1/scrape-erros ──────────────────────────────────────────────────


def test_endpoint_lista_erros_pendentes(client, db):
    registrar_erro(
        db,
        url="http://x.com/1",
        etapa="listar_versoes",
        exc=ErroFalso("timeout"),
        contexto="Fiat > Uno",
    )
    db.commit()

    r = client.get("/api/v1/scrape-erros")
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 1
    assert data[0]["url"] == "http://x.com/1"
    assert data[0]["tipo_erro"] == "ErroFalso"
    assert data[0]["mensagem"] == "timeout"
    assert data[0]["contexto"] == "Fiat > Uno"


def test_endpoint_filtra_por_etapa(client, db):
    registrar_erro(db, url="http://x.com/1", etapa="listar_versoes", exc=ErroFalso("a"))
    registrar_erro(db, url="http://x.com/2", etapa="detalhe_versao", exc=ErroFalso("b"))
    db.commit()

    r = client.get("/api/v1/scrape-erros?etapa=detalhe_versao")
    assert r.status_code == 200
    assert len(r.json()) == 1
    assert r.json()[0]["url"] == "http://x.com/2"


def test_endpoint_vazio_quando_nao_ha_erros(client):
    r = client.get("/api/v1/scrape-erros")
    assert r.status_code == 200
    assert r.json() == []
