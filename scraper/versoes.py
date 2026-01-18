import time
import sqlite3
import requests
import unicodedata
from bs4 import BeautifulSoup

BASE_URL = "https://combustivel.app"
DB_PATH = "database/veiculos.db"

HEADERS = {
    "User-Agent": "VeiculoDadosBRBot/1.0 (educational use)"
}


# =========================
# Banco
# =========================

def criar_banco():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    with open("database/schema.sql", "r") as f:
        cur.executescript(f.read())
    conn.commit()
    conn.close()


def obter_modelos_anos():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        SELECT
            ma.id,
            m.url,
            m.nome AS modelo,
            ma.ano,
            mc.nome AS marca
        FROM modelos_anos ma
        JOIN modelos m ON m.id = ma.modelo_id
        JOIN marcas mc ON mc.id = m.marca_id
        ORDER BY mc.nome, m.nome, ma.ano
    """)

    dados = cur.fetchall()
    conn.close()
    return dados


def salvar_versao(modelo_ano_id, versao, url):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        INSERT OR IGNORE INTO versoes (
            modelo_ano_id,
            versao,
            url
        )
        VALUES (?, ?, ?)
    """, (modelo_ano_id, versao, url))

    conn.commit()
    conn.close()


# =========================
# Utils
# =========================

def slug_consumo(marca, modelo, ano):
    def limpar(txt):
        txt = unicodedata.normalize("NFD", txt)
        txt = txt.encode("ascii", "ignore").decode("utf-8")
        txt = txt.lower()
        return txt.replace(" ", "_")

    return f"Consumo_{limpar(marca)}_{limpar(modelo)}_{ano}"


def normalizar_modelo_url(modelo_url):
    modelo_url = modelo_url.replace(BASE_URL, "")
    modelo_url = modelo_url.rstrip("/")
    if modelo_url.endswith("/c"):
        modelo_url = modelo_url[:-2]
    return "/" + modelo_url.strip("/")


# =========================
# Scraper
# =========================

def coletar_versoes():
    registros = obter_modelos_anos()

    for modelo_ano_id, modelo_url, modelo, ano, marca in registros:

        modelo_url = normalizar_modelo_url(modelo_url)
        anchor_id = slug_consumo(marca, modelo, ano)

        url = f"{BASE_URL}{modelo_url}/c#{anchor_id}"

        print(f"🔍 {marca} {modelo} {ano}")
        print(f"   URL: {url}")

        try:
            resp = requests.get(url, headers=HEADERS, timeout=30)
            resp.raise_for_status()

            soup = BeautifulSoup(resp.text, "html.parser")

            section = soup.find("div", id=anchor_id)
            if not section:
                print("⚠️ Seção de consumo não encontrada")
                continue

            cards = section.select("div.card-hover")
            print(f"   → {len(cards)} versões encontradas")

            for card in cards:
                link = card.select_one("h3 a")
                if not link:
                    continue

                versao = link.get_text(strip=True)
                href = link.get("href")

                if not href:
                    continue

                # 🔥 CORREÇÃO DEFINITIVA DA URL
                if href.startswith("http"):
                    url_versao = href
                else:
                    url_versao = BASE_URL + href

                salvar_versao(modelo_ano_id, versao, url_versao)

            time.sleep(1)

        except Exception as e:
            print(f"❌ Erro ao processar {marca} {modelo} {ano}: {e}")


# =========================
# Main
# =========================

if __name__ == "__main__":
    criar_banco()
    coletar_versoes()
