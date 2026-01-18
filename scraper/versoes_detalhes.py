import sqlite3
import requests
import time
import re
from bs4 import BeautifulSoup

BASE_URL = "https://combustivel.app"
DB_PATH = "database/veiculos.db"

HEADERS = {
    "User-Agent": "VeiculoDadosBRBot/1.0 (educational use)"
}

# =========================
# Utils
# =========================

def criar_banco():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    with open("database/schema.sql", "r") as f:
        cur.executescript(f.read())
    conn.commit()
    conn.close()


def limpar_numero(txt):
    if not txt:
        return None
    txt = txt.replace(".", "").replace(",", ".")
    match = re.search(r"(\d+(\.\d+)?)", txt)
    return float(match.group(1)) if match else None


def normalizar_url(url):
    if not url:
        return None
    return url if url.startswith("http") else BASE_URL + url


# =========================
# CONSUMO (CORRETO)
# =========================

def extrair_consumo_por_id(soup, h2_id):
    resultado = {"alcool": None, "gasolina": None, "unico": None}

    h2 = soup.find("h2", id=h2_id)
    if not h2:
        return resultado

    container = h2.find_parent("div", class_="bg-white")
    if not container:
        return resultado

    texto = container.get_text(" ", strip=True)

    alcool = re.search(r"(\d+(?:,\d+)?)\s*km/L\s*\(A\)", texto, re.I)
    gasolina = re.search(r"(\d+(?:,\d+)?)\s*km/L\s*\(G\)", texto, re.I)

    if alcool:
        resultado["alcool"] = float(alcool.group(1).replace(",", "."))

    if gasolina:
        resultado["gasolina"] = float(gasolina.group(1).replace(",", "."))

    if not alcool and not gasolina:
        unico = re.search(r"(\d+(?:,\d+)?)\s*km/L", texto, re.I)
        if unico:
            resultado["unico"] = float(unico.group(1).replace(",", "."))

    return resultado


# =========================
# Banco
# =========================

def obter_versoes():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        SELECT id, versao, url
        FROM versoes
        WHERE id NOT IN (
            SELECT versao_id FROM versoes_detalhes
        )
        ORDER BY id
    """)
    rows = cur.fetchall()
    conn.close()
    return rows


def salvar_detalhes(versao_id, d):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        INSERT OR REPLACE INTO versoes_detalhes (
            versao_id,
            combustivel,
            tanque_litros,
            consumo_cidade_alcool,
            consumo_cidade_gasolina,
            consumo_estrada_alcool,
            consumo_estrada_gasolina,
            cilindrada_cm3,
            cilindros,
            velocidade_max_kmh,
            zero_a_cem_segundos,
            comprimento_mm,
            largura_mm,
            altura_mm,
            entre_eixos_mm,
            peso_kg,
            porta_malas_litros,
            cambio,
            tracao,
            suspensao_dianteira,
            suspensao_traseira,
            freio_dianteiro,
            freio_traseiro
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        versao_id,
        d.get("combustivel"),
        d.get("tanque_litros"),
        d.get("consumo_cidade_alcool"),
        d.get("consumo_cidade_gasolina"),
        d.get("consumo_estrada_alcool"),
        d.get("consumo_estrada_gasolina"),
        d.get("cilindrada_cm3"),
        d.get("cilindros"),
        d.get("velocidade_max_kmh"),
        d.get("zero_a_cem_segundos"),
        d.get("comprimento_mm"),
        d.get("largura_mm"),
        d.get("altura_mm"),
        d.get("entre_eixos_mm"),
        d.get("peso_kg"),
        d.get("porta_malas_litros"),
        d.get("cambio"),
        d.get("tracao"),
        d.get("suspensao_dianteira"),
        d.get("suspensao_traseira"),
        d.get("freio_dianteiro"),
        d.get("freio_traseiro")
    ))

    conn.commit()
    conn.close()


# =========================
# Scraper
# =========================

def coletar_detalhes():
    versoes = obter_versoes()

    for versao_id, nome, url in versoes:
        url = normalizar_url(url)

        print(f"\n🔍 {nome}")
        print(f"   URL: {url}")

        try:
            resp = requests.get(url, headers=HEADERS, timeout=30)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")

            dados = {}

            # ===== ESPECIFICAÇÕES =====
            for box in soup.select("div.bg-white"):
                h4 = box.find("h4")
                p = box.find("p")
                if not h4 or not p:
                    continue

                chave = h4.get_text(strip=True).lower()
                valor = p.get_text(strip=True)

                if len(valor) > 80:
                    continue

                if "combustível" in chave:
                    dados["combustivel"] = valor
                elif "tanque" in chave:
                    dados["tanque_litros"] = limpar_numero(valor)
                elif "cilindrada" in chave:
                    dados["cilindrada_cm3"] = limpar_numero(valor)
                elif "cilindros" in chave:
                    dados["cilindros"] = valor
                elif "velocidade máxima" in chave:
                    dados["velocidade_max_kmh"] = limpar_numero(valor)
                elif "0-100" in chave:
                    dados["zero_a_cem_segundos"] = limpar_numero(valor)
                elif "comprimento" in chave:
                    dados["comprimento_mm"] = limpar_numero(valor)
                elif "largura" in chave:
                    dados["largura_mm"] = limpar_numero(valor)
                elif "altura" in chave:
                    dados["altura_mm"] = limpar_numero(valor)
                elif "entre-eixos" in chave:
                    dados["entre_eixos_mm"] = limpar_numero(valor)
                elif "peso" in chave:
                    dados["peso_kg"] = limpar_numero(valor)
                elif "porta-malas" in chave:
                    dados["porta_malas_litros"] = limpar_numero(valor)
                elif "câmbio" in chave:
                    dados["cambio"] = valor
                elif "tração" in chave:
                    dados["tracao"] = valor
                elif "suspensão dianteira" in chave:
                    dados["suspensao_dianteira"] = valor
                elif "suspensão traseira" in chave:
                    dados["suspensao_traseira"] = valor
                elif "freios dianteiros" in chave:
                    dados["freio_dianteiro"] = valor
                elif "freios traseiros" in chave:
                    dados["freio_traseiro"] = valor

            # ===== CONSUMO =====
            cidade = extrair_consumo_por_id(soup, "Cidade_Urbano")
            estrada = extrair_consumo_por_id(soup, "Estrada_Rodovia")

            comb = (dados.get("combustivel") or "").lower()

            if "flex" in comb:
                dados["consumo_cidade_alcool"] = cidade["alcool"]
                dados["consumo_cidade_gasolina"] = cidade["gasolina"]
                dados["consumo_estrada_alcool"] = estrada["alcool"]
                dados["consumo_estrada_gasolina"] = estrada["gasolina"]

            elif "álcool" in comb or "alcool" in comb:
                dados["consumo_cidade_alcool"] = cidade["unico"]
                dados["consumo_estrada_alcool"] = estrada["unico"]

            elif "gasolina" in comb:
                dados["consumo_cidade_gasolina"] = cidade["unico"]
                dados["consumo_estrada_gasolina"] = estrada["unico"]

            salvar_detalhes(versao_id, dados)
            print("✅ Salvo com sucesso")
            time.sleep(1)

        except Exception as e:
            print(f"❌ Erro: {e}")


# =========================
# Main
# =========================

if __name__ == "__main__":
    criar_banco()
    coletar_detalhes()
