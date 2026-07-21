# scraper/sources/testar_scraper.py
import logging

from scraper.sources.fichacompleta import FichaCompletaScraper

# Ativa o log para vermos as requisições acontecerem
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


# ── CÓDIGO DE TESTE ISOLADO ──────────────────────────────────────────────────
class ScraperCobaia(FichaCompletaScraper):
    def listar_versoes(self, modelo_url: str) -> list[dict]:
        """Lógica para o layout de listagem de versões"""
        soup = self.get(modelo_url)
        versoes = []
        BASE_URL = "https://www.fichacompleta.com.br"

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

                versoes.append(
                    {
                        "versao": name_tag.get_text().strip(),
                        "ano": ano,
                        "url": abs_href,
                    }
                )
        return versoes

    def detalhe_versao(self, versao_url: str) -> dict:
        """Lógica nova e unificada para capturar Informações e Ficha Técnica"""
        soup = self.get(versao_url)
        especificacoes = {}

        # O site padronizou tudo sob a classe .ent-spec-item
        for item in soup.select(".ent-spec-item"):
            label_tag = item.select_one(".ent-spec-label")
            value_tag = item.select_one(".ent-spec-value")

            if label_tag and value_tag:
                # Remove espaços extras do nome do campo (ex: "Combustível")
                chave = label_tag.get_text().strip()

                # Limpa quebras de linha e espaços múltiplos do valor (ajuda no caso do link da FIPE)
                valor = " ".join(value_tag.get_text().split()).strip()

                if chave:
                    especificacoes[chave] = valor

        return especificacoes


# ─────────────────────────────────────────────────────────────────────────────


def testar_fluxo_unico():
    MARCA_TESTE_URL = "https://www.fichacompleta.com.br/carros/audi/"

    with ScraperCobaia(delay=1.0) as scraper:
        print("\n--- STEP 1: TESTANDO MODELOS ---")
        modelos = scraper.listar_modelos(MARCA_TESTE_URL)
        print(f"Total de modelos encontrados: {len(modelos)}")

        if not modelos:
            print("❌ Nenhum modelo encontrado.")
            return

        primeiro_modelo = modelos[0]
        print(
            f"✓ Sucesso! Primeiro modelo encontrado: {primeiro_modelo['nome']} ({primeiro_modelo['url']})"
        )

        print("\n--- STEP 2: TESTANDO VERSÕES E ANOS ---")
        versoes = scraper.listar_versoes(primeiro_modelo["url"])
        print(f"Total de versões encontradas: {len(versoes)}")

        if not versoes:
            print("❌ Nenhuma versão encontrada.")
            return

        primeira_versao = versoes[0]
        print(
            f"✓ Sucesso! Primeira versão encontrada: {primeira_versao['versao']} | Ano: {primeira_versao['ano']}"
        )

        print("\n--- STEP 3: TESTANDO FICHA TÉCNICA ---")
        print(f"Acessando os detalhes em: {primeira_versao['url']}")
        detalhes = scraper.detalhe_versao(primeira_versao["url"])

        print(f"\n✓ Ficha Técnica extraída! Total de campos capturados: {len(detalhes)}")
        print("-" * 50)
        for chave, valor in detalhes.items():
            print(f"{chave:.<35}: {valor}")
        print("-" * 50)


if __name__ == "__main__":
    testar_fluxo_unico()
