import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from api.core.database import Base
from api.models import scrape_erro, veiculo  # noqa: F401 — registra todos os models

# Banco in-memory para testes — isolado, sem dependência de Postgres
TEST_DATABASE_URL = "sqlite://"

engine_test = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSession = sessionmaker(bind=engine_test, autocommit=False, autoflush=False)


@pytest.fixture(autouse=True)
def setup_banco():
    """Cria e destrói o schema a cada teste — garantia de isolamento."""
    Base.metadata.create_all(engine_test)
    yield
    Base.metadata.drop_all(engine_test)


@pytest.fixture
def db():
    session = TestingSession()
    try:
        yield session
    finally:
        session.close()


"""Testes do rastreamento de erros do scraper: scraper/erros.py"""

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
