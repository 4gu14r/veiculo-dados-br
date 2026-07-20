import logging
import time
from abc import ABC, abstractmethod

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "veiculos-dados-br/2.0 (+https://github.com/4gu14r/veiculo-dados-br)",
    "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


class BaseScraper(ABC):
    """
    Classe base para todos os scrapers.

    Implementa:
    - HTTP client configurado com headers e timeout adequados
    - Delay entre requisições para não sobrecarregar o site
    - Logging padronizado
    - Context manager para fechar o client corretamente
    """

    def __init__(self, delay: float = 1.5):
        self.delay = delay
        self.client = httpx.Client(
            headers=HEADERS,
            timeout=30,
            follow_redirects=True,
        )

    def get(self, url: str) -> BeautifulSoup:
        time.sleep(self.delay)
        logger.debug("GET %s", url)
        response = self.client.get(url)
        response.raise_for_status()
        return BeautifulSoup(response.text, "lxml")

    # ── Interface que cada scraper deve implementar ────────────────────────────

    @abstractmethod
    def listar_marcas(self) -> list[dict]:
        """Retorna lista de dicts com {nome, url}."""
        ...

    @abstractmethod
    def listar_modelos(self, marca_url: str) -> list[dict]:
        """Retorna lista de dicts com {nome, url}."""
        ...

    @abstractmethod
    def listar_versoes(self, modelo_url: str) -> list[dict]:
        """Retorna lista de dicts com {versao, ano, url}."""
        ...

    @abstractmethod
    def detalhe_versao(self, versao_url: str) -> dict:
        """Retorna dict com todos os campos da ficha técnica."""
        ...

    # ── Context manager ────────────────────────────────────────────────────────

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.client.close()
