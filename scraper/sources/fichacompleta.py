"""
Scraper para http://fichacompleta.com.br/

Hierarquia do site:
  /  → lista de marcas
  /marca/<slug>/  → lista de modelos
  /modelo/<slug>/  → lista de anos
  /modelo/<slug>/<ano>/  → lista de versões
  /modelo/<slug>/<ano>/<versao-slug>/  → ficha técnica completa
"""

import logging
import re

from bs4 import BeautifulSoup

from scraper.base import BaseScraper

logger = logging.getLogger(__name__)

BASE_URL = "http://fichacompleta.com.br"


def _texto(tag) -> str | None:
    if tag is None:
        return None
    return re.sub(r"\s+", " ", tag.get_text()).strip() or None


def _float(valor: str | None) -> float | None:
    if not valor:
        return None
    try:
        return float(re.sub(r"[^\d,\.]", "", valor).replace(",", "."))
    except ValueError:
        return None


def _int(valor: str | None) -> int | None:
    v = _float(valor)
    return int(v) if v is not None else None


class FichaCompletaScraper(BaseScraper):

    def listar_marcas(self) -> list[dict]:
        soup = self.get(BASE_URL + "/")
        marcas = []
        for a in soup.select("a[href*='/marca/']"):
            nome = _texto(a)
            url = a.get("href", "")
            if nome and url:
                marcas.append({
                    "nome": nome,
                    "url": url if url.startswith("http") else BASE_URL + url,
                })
        logger.info("Encontradas %d marcas", len(marcas))
        return marcas

    def listar_modelos(self, marca_url: str) -> list[dict]:
        soup = self.get(marca_url)
        modelos = []
        for a in soup.select("a[href*='/modelo/']"):
            nome = _texto(a)
            url = a.get("href", "")
            if nome and url:
                modelos.append({
                    "nome": nome,
                    "url": url if url.startswith("http") else BASE_URL + url,
                })
        return modelos

    def listar_versoes(self, modelo_url: str) -> list[dict]:
        """
        Navega pela página do modelo, coleta todos os anos disponíveis
        e para cada ano coleta as versões — retornando uma lista plana
        com {versao, ano, url}.
        """
        soup = self.get(modelo_url)
        versoes = []

        # Anos ficam em links dentro do bloco de anos
        for a_ano in soup.select("a[href*='/'][href]"):
            href = a_ano.get("href", "")
            # Tenta extrair o ano do href (ex: /modelo/gol/2023/)
            match = re.search(r"/(\d{4})/?$", href)
            if not match:
                continue
            ano = int(match.group(1))
            ano_url = href if href.startswith("http") else BASE_URL + href
            soup_ano = self.get(ano_url)

            for a_versao in soup_ano.select("a[href]"):
                versao_href = a_versao.get("href", "")
                # Versões têm padrão /modelo/<slug>/<ano>/<versao-slug>/
                if re.search(r"/\d{4}/.+", versao_href):
                    nome = _texto(a_versao)
                    if nome:
                        versoes.append({
                            "versao": nome,
                            "ano": ano,
                            "url": versao_href if versao_href.startswith("http") else BASE_URL + versao_href,
                        })

        return versoes

    def detalhe_versao(self, versao_url: str) -> dict:
        """
        Extrai a ficha técnica completa de uma versão.
        Todos os campos batem com as colunas de versoes_detalhes.
        """
        soup = self.get(versao_url)

        def campo(label: str) -> str | None:
            """Busca o valor de uma linha da ficha pelo label."""
            for row in soup.select("tr, li, .spec-row"):
                texto = row.get_text(" ", strip=True)
                if label.lower() in texto.lower():
                    partes = texto.split(":")
                    if len(partes) >= 2:
                        return partes[-1].strip()
            return None

        return {
            "combustivel":               campo("Combustível"),
            "tanque_litros":             _float(campo("Tanque")),
            "consumo_cidade_alcool":     _float(campo("Cidade (Álcool)")),
            "consumo_cidade_gasolina":   _float(campo("Cidade (Gasolina)")),
            "consumo_estrada_alcool":    _float(campo("Estrada (Álcool)")),
            "consumo_estrada_gasolina":  _float(campo("Estrada (Gasolina)")),
            "cilindrada_cm3":            _int(campo("Cilindrada")),
            "cilindros":                 campo("Cilindros"),
            "velocidade_max_kmh":        _int(campo("Velocidade máxima")),
            "zero_a_cem_segundos":       _float(campo("0 a 100")),
            "comprimento_mm":            _int(campo("Comprimento")),
            "largura_mm":                _int(campo("Largura")),
            "altura_mm":                 _int(campo("Altura")),
            "entre_eixos_mm":            _int(campo("Entre-eixos")),
            "peso_kg":                   _int(campo("Peso")),
            "porta_malas_litros":        _int(campo("Porta-malas")),
            "cambio":                    campo("Câmbio"),
            "tracao":                    campo("Tração"),
            "suspensao_dianteira":       campo("Suspensão dianteira"),
            "suspensao_traseira":        campo("Suspensão traseira"),
            "freio_dianteiro":           campo("Freio dianteiro"),
            "freio_traseiro":            campo("Freio traseiro"),
        }
