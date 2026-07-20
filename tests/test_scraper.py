"""
Testes de unidade e integração do Scraper FichaCompleta.
Garante que seletores HTML convertam os dados corretamente sem bater na rede.
"""

from unittest.mock import patch
import pytest
from bs4 import BeautifulSoup
from scraper.sources.fichacompleta import FichaCompletaScraper

# ── Fixture para instanciar o Scraper ──────────────────────────────────────────
@pytest.fixture
def scraper():
    """Retorna uma instância do scraper com delay zerado para testes rápidos."""
    return FichaCompletaScraper(delay=0.0)


# ── Testes: Listar Marcas ──────────────────────────────────────────────────────

def test_listar_marcas_sucesso(scraper):
    html_mock = """
    <div>
        <a href="/carros/audi/">Audi</a>
        <a href="/carros/bmw/">BMW</a>
        <a href="/carros/marcas/">Ignorar Link de Navegação</a>
        <a href="/carros/comparativo-audi-vs-bmw">Ignorar Comparativos</a>
    </div>
    """
    soup_mock = BeautifulSoup(html_mock, "html.parser")

    # Força o método self.get() a retornar o nosso HTML falso
    with patch.object(FichaCompletaScraper, "get", return_value=soup_mock):
        marcas = scraper.listar_marcas()

    assert len(marcas) == 2
    assert marcas[0] == {"nome": "Audi", "url": "https://www.fichacompleta.com.br/carros/audi/"}
    assert marcas[1] == {"nome": "BMW", "url": "https://www.fichacompleta.com.br/carros/bmw/"}


# ── Testes: Listar Modelos ─────────────────────────────────────────────────────

def test_listar_modelos_filtragem_e_unicidade(scraper):
    html_mock = """
    <div>
        <a href="/carros/audi/a3/">Audi A3</a>
        <a href="/carros/audi/a4/">Audi A4</a>
        <a href="/carros/audi/a4/">Audi A4 Duplicado</a>
        <a href="/carros/audi/a4/1996/">Ignorar Link de Ano Direto</a>
        <a href="/carros/bmw/320i">Ignorar Outra Marca</a>
    </div>
    """
    soup_mock = BeautifulSoup(html_mock, "html.parser")
    marca_url = "https://www.fichacompleta.com.br/carros/audi/"

    with patch.object(FichaCompletaScraper, "get", return_value=soup_mock):
        modelos = scraper.listar_modelos(marca_url)

    assert len(modelos) == 2
    assert modelos[0]["nome"] == "Audi A3"
    assert modelos[1]["nome"] == "Audi A4"


# ── Testes: Listar Versões ─────────────────────────────────────────────────────

def test_listar_versoes_com_deduplicação(scraper):
    html_mock = """
    <div class="ver-list">
        <div class="ver-card">
            <a class="ver-card__link" href="/carros/audi/a4-1-8-1996">Link 1</a>
            <span class="ver-card__year">1996</span>
            <span class="ver-card__name">1.8 20V</span>
        </div>
        <!-- Card duplicado (mesmo nome e ano, URL diferente que o site gera às vezes) -->
        <div class="ver-card">
            <a class="ver-card__link" href="/carros/audi/a4-1-8-1996-gasolina">Link 2</a>
            <span class="ver-card__year">1996</span>
            <span class="ver-card__name">1.8 20V</span>
        </div>
    </div>
    """
    soup_mock = BeautifulSoup(html_mock, "html.parser")
    modelo_url = "https://www.fichacompleta.com.br/carros/audi/a4/"

    with patch.object(FichaCompletaScraper, "get", return_value=soup_mock):
        versoes = scraper.listar_versoes(modelo_url)

    # Garante que a nossa lógica de unicidade barrou o segundo card idêntico
    assert len(versoes) == 1
    assert versoes[0]["versao"] == "1.8 20V"
    assert versoes[0]["ano"] == 1996
    assert versoes[0]["url"] == "https://www.fichacompleta.com.br/carros/audi/a4-1-8-1996"


# ── Testes: Detalhe da Versão (Ficha Técnica) ──────────────────────────────────

def test_detalhe_versao_parsing_completo(scraper):
    html_mock = """
    <div>
        <div class="ent-ficha-group">
            <div class="ent-ficha-group__title">Informações Básicas</div>
            <div class="ent-spec-item">
                <div class="ent-spec-label">Combustível</div>
                <div class="ent-spec-value">Gasolina</div>
            </div>
        </div>
        <div class="ent-ficha-group">
            <div class="ent-ficha-group__title">Motor</div>
            <div class="ent-spec-item">
                <div class="ent-spec-label">Cilindrada</div>
                <div class="ent-spec-value">2771 cm³</div>
            </div>
        </div>
        <div class="ent-ficha-group">
            <div class="ent-ficha-group__title">Dimensões</div>
            <div class="ent-spec-item">
                <div class="ent-spec-label">Comprimento</div>
                <div class="ent-spec-value">4790 mm</div>
            </div>
            <div class="ent-spec-item">
                <div class="ent-spec-label">Largura</div>
                <div class="ent-spec-value">1777 mm</div>
            </div>
        </div>
    </div>
    """
    soup_mock = BeautifulSoup(html_mock, "html.parser")
    versao_url = "https://www.fichacompleta.com.br/carros/audi/a4-detalhe"

    with patch.object(FichaCompletaScraper, "get", return_value=soup_mock):
        dados = scraper.detalhe_versao(versao_url)

    # Validações de conversão de tipos (strings, ints limpando caracteres especiais)
    assert dados["combustivel"] == "Gasolina"
    assert dados["cilindrada_cm3"] == 2771      # Limpou o ponto e converteu para int
    assert dados["comprimento_mm"] == 4790      # Converteu para int
    assert dados["largura_mm"] == 1777          # Validou o grupo de dimensões com sucesso
    assert dados["tanque_litros"] is None       # Campo ausente vira None de forma segura