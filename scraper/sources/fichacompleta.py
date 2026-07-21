"""
Scraper para https://www.fichacompleta.com.br/

Hierarquia atualizada do site:
  /carros/marcas/              → lista de marcas
  /carros/<marca>/             → lista de modelos
  /carros/<marca>/<modelo>/    → lista de versões e anos (unificado)
  /carros/<marca>/<versao-slug> → ficha técnica completa
"""

import logging
import re

from scraper.base import BaseScraper

logger = logging.getLogger(__name__)

# URL corrigida com HTTPS e WWW para evitar redirecionamentos
BASE_URL = "https://www.fichacompleta.com.br"


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
        soup = self.get(BASE_URL + "/carros/marcas/")
        marcas = []

        for a in soup.select("a[href*='/carros/']"):
            nome = _texto(a)
            url = a.get("href", "")

            if (
                url.endswith("/carros/")
                or url.endswith("/carros/marcas/")
                or "comparativo" in url.lower()
            ):
                continue

            if nome and url:
                marcas.append(
                    {
                        "nome": nome,
                        "url": url if url.startswith("http") else BASE_URL + url,
                    }
                )

        logger.info("Encontradas %d marcas", len(marcas))
        return marcas

    def listar_modelos(self, marca_url: str) -> list[dict]:
        soup = self.get(marca_url)
        modelos = []

        for a in soup.select("a[href*='/carros/']"):
            nome = _texto(a)
            url = a.get("href", "")
            if not url:
                continue

            abs_url = url if url.startswith("http") else BASE_URL + url

            if abs_url.startswith(marca_url) and abs_url != marca_url:
                if re.search(r"/\d{4}/?$", abs_url):
                    continue

                if nome:
                    modelos.append(
                        {
                            "nome": nome,
                            "url": abs_url,
                        }
                    )

        modelos_unicos = []
        urls_vistas = set()
        for m in modelos:
            if m["url"] not in urls_vistas:
                urls_vistas.add(m["url"])
                modelos_unicos.append(m)

        return modelos_unicos

    def listar_versoes(self, modelo_url: str) -> list[dict]:
        """
        Navega pela página do modelo e coleta de forma direta todas as
        versões e anos, filtrando duplicidades visuais do site.
        """
        soup = self.get(modelo_url)
        versoes = []
        chaves_vistas = set()

        for card in soup.select(".ver-list .ver-card"):
            link_tag = card.select_one("a.ver-card__link")
            year_tag = card.select_one(".ver-card__year")
            name_tag = card.select_one(".ver-card__name")

            if link_tag and year_tag and name_tag:
                href = link_tag.get("href", "")
                abs_href = href if href.startswith("http") else BASE_URL + href

                try:
                    ano = int(year_tag.get_text().strip())
                except ValueError:
                    continue

                versao_nome = name_tag.get_text().strip()

                chave_unicidade = (versao_nome.lower(), ano)

                if chave_unicidade not in chaves_vistas:
                    chaves_vistas.add(chave_unicidade)
                    versoes.append(
                        {
                            "versao": versao_nome,
                            "ano": ano,
                            "url": abs_href,
                        }
                    )
                else:
                    logger.debug("Ignorando link redundante no site: %s (%d)", versao_nome, ano)

        logger.info("Encontradas %d versões únicas para o modelo %s", len(versoes), modelo_url)
        return versoes

    def detalhe_versao(self, versao_url: str) -> dict:
        """
        Extrai a ficha técnica de uma versão utilizando a nova estrutura de
        grids e classes de especificação (.ent-spec-item).
        """
        soup = self.get(versao_url)

        def campo(label: str, grupo: str = None) -> str | None:
            """
            Busca de forma contextualizada o valor da especificação baseando-se
            no nome da label e opcionalmente no grupo (seção) correspondente.
            """
            for item in soup.select(".ent-spec-item"):
                lbl_tag = item.select_one(".ent-spec-label")
                val_tag = item.select_one(".ent-spec-value")

                if not lbl_tag or not val_tag:
                    continue

                lbl_texto = lbl_tag.get_text().strip().lower()
                if label.lower() not in lbl_texto:
                    continue

                # Se um grupo específico foi solicitado, valida o título da seção pai
                if grupo:
                    pai_grupo = item.find_parent(class_="ent-ficha-group")
                    if pai_grupo:
                        titulo_tag = pai_grupo.select_one(".ent-ficha-group__title")
                        if titulo_tag and grupo.lower() in titulo_tag.get_text().strip().lower():
                            return " ".join(val_tag.get_text().split()).strip()
                    continue

                return " ".join(val_tag.get_text().split()).strip()
            return None

        return {
            "combustivel": campo("Combustível"),
            "tanque_litros": _float(campo("Tanque de combustível")),
            "consumo_cidade_alcool": _float(campo("Urbano (A)", grupo="Consumo")),
            "consumo_cidade_gasolina": _float(campo("Urbano (G)", grupo="Consumo")),
            "consumo_estrada_alcool": _float(campo("Rodoviário (A)", grupo="Consumo")),
            "consumo_estrada_gasolina": _float(campo("Rodoviário (G)", grupo="Consumo")),
            "cilindrada_cm3": _int(campo("Cilindrada", grupo="Motor")),
            "cilindros": campo("Cilindros", grupo="Motor"),
            "velocidade_max_kmh": _int(campo("Velocidade máxima", grupo="Desempenho")),
            "zero_a_cem_segundos": _float(campo("Aceleração 0-100", grupo="Desempenho")),
            "comprimento_mm": _int(campo("Comprimento", grupo="Dimensões")),
            "largura_mm": _int(campo("Largura", grupo="Dimensões") or campo("Largura")),
            "altura_mm": _int(campo("Altura", grupo="Dimensões")),
            "entre_eixos_mm": _int(campo("Distância entre-eixos", grupo="Dimensões")),
            "peso_kg": _int(campo("Peso", grupo="Dimensões")),
            "porta_malas_litros": _int(campo("Porta-malas", grupo="Dimensões")),
            "cambio": campo("Câmbio", grupo="Transmissão"),
            "tracao": campo("Tração", grupo="Transmissão"),
            "suspensao_dianteira": campo("Dianteira", grupo="Suspensão"),
            "suspensao_traseira": campo("Traseira", grupo="Suspensão"),
            "freio_dianteiro": campo("Dianteiros", grupo="Freios"),
            "freio_traseiro": campo("Traseiros", grupo="Freios"),
        }
