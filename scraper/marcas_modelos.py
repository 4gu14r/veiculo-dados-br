import requests
import sqlite3
from bs4 import BeautifulSoup

BASE_URL = "https://combustivel.app/carros"
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


def salvar_marca(nome):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        "INSERT OR IGNORE INTO marcas (nome) VALUES (?)",
        (nome,)
    )
    conn.commit()
    cur.execute("SELECT id FROM marcas WHERE nome = ?", (nome,))
    marca_id = cur.fetchone()[0]
    conn.close()
    return marca_id


def salvar_modelo(marca_id, nome, url):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        """
        INSERT OR IGNORE INTO modelos (marca_id, nome, url)
        VALUES (?, ?, ?)
        """,
        (marca_id, nome, url)
    )
    conn.commit()
    conn.close()


def coletar_marcas_modelos():
    response = requests.get(BASE_URL, headers=HEADERS, timeout=30)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    cards = soup.select("div[id^='letter-']")

    total_modelos = 0

    for card in cards:
        marca_tag = card.select_one("h2")
        if not marca_tag:
            continue

        marca_nome = marca_tag.get_text(strip=True)
        marca_id = salvar_marca(marca_nome)

        for item in card.select("li.car-item"):
            nome_modelo = item.select_one("span.font-medium")
            link = item.select_one("a")

            if not nome_modelo or not link:
                continue

            salvar_modelo(
                marca_id,
                nome_modelo.get_text(strip=True),
                link["href"]
            )
            total_modelos += 1

    print(f"✔ Coleta finalizada: {total_modelos} modelos")


if __name__ == "__main__":
    criar_banco()
    coletar_marcas_modelos()
