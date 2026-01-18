import time
import requests
import sqlite3
import unicodedata
import re
from bs4 import BeautifulSoup

BASE_URL = "https://combustivel.app"
DB_PATH = "database/veiculos.db"

HEADERS = {
    "User-Agent": "VeiculoDadosBRBot/1.0 (educational use)"
}

def criar_banco():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    with open("database/schema.sql", "r") as f:
        cur.executescript(f.read())
    conn.commit()
    conn.close()


def slugify(texto: str) -> str:
    texto = unicodedata.normalize("NFKD", texto)
    texto = texto.encode("ascii", "ignore").decode("ascii")
    texto = texto.lower()
    texto = re.sub(r"[^a-z0-9]+", "-", texto)
    return texto.strip("-")


def obter_modelos():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT id, nome FROM modelos")
    modelos = cur.fetchall()
    conn.close()
    return modelos


def salvar_ano(modelo_id, ano):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        """
        INSERT OR IGNORE INTO modelos_anos (modelo_id, ano)
        VALUES (?, ?)
        """,
        (modelo_id, ano)
    )
    conn.commit()
    conn.close()


def coletar_anos_modelo(modelo_nome):
    slug = slugify(modelo_nome)
    url = f"{BASE_URL}/{slug}/c"

    response = requests.get(url, headers=HEADERS, timeout=30)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    anos = []

    for span in soup.select("a span.font-medium"):
        texto = span.get_text(strip=True)
        if texto.isdigit() and len(texto) == 4:
            anos.append(int(texto))

    return list(set(anos))


def executar():
    modelos = obter_modelos()
    total = 0

    for modelo_id, nome in modelos:
        print(f"🔍 Coletando anos do modelo: {nome}")
        try:
            anos = coletar_anos_modelo(nome)
            for ano in anos:
                salvar_ano(modelo_id, ano)
                total += 1
            time.sleep(1)
        except Exception as e:
            print(f"❌ Erro em {nome}: {e}")

    print(f"✔ Coleta finalizada: {total} anos salvos")


if __name__ == "__main__":
    criar_banco()
    executar()
