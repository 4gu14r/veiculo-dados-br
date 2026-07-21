"""
Rastreamento de erros do scraper.

Cada falha vira uma linha em `scrape_erros`, identificada pela URL do
recurso que falhou. Se o mesmo recurso falhar de novo no próximo run,
a linha é atualizada (incrementa `tentativas`, atualiza a mensagem) em
vez de duplicar. Quando o recurso finalmente é processado com sucesso,
a linha é apagada — ou seja, a tabela sempre reflete só os problemas
que ainda estão pendentes.
"""

import logging

from sqlalchemy.orm import Session

from api.models.scrape_erro import ScrapeErro

logger = logging.getLogger(__name__)


def registrar_erro(
    db: Session,
    *,
    url: str,
    etapa: str,
    exc: Exception,
    contexto: str | None = None,
) -> None:
    """Cria ou atualiza o registro de erro para essa URL."""
    erro = db.query(ScrapeErro).filter_by(url=url).first()

    if erro:
        erro.tentativas += 1
        erro.mensagem = str(exc)
        erro.tipo_erro = type(exc).__name__
        erro.etapa = etapa
        if contexto:
            erro.contexto = contexto
    else:
        erro = ScrapeErro(
            url=url,
            etapa=etapa,
            contexto=contexto,
            tipo_erro=type(exc).__name__,
            mensagem=str(exc),
            tentativas=1,
        )
        db.add(erro)

    db.flush()
    logger.warning(
        "[%s] %s | tentativa nº%d | %s: %s",
        etapa,
        contexto or url,
        erro.tentativas,
        erro.tipo_erro,
        erro.mensagem,
    )


def resolver_erro_se_existir(db: Session, url: str) -> None:
    """Remove o registro de erro de uma URL que finalmente deu certo."""
    erro = db.query(ScrapeErro).filter_by(url=url).first()
    if erro:
        logger.info("Erro anterior resolvido: %s (levou %d tentativas)", url, erro.tentativas)
        db.delete(erro)
        db.flush()
