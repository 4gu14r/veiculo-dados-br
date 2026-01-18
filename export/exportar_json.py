import sqlite3
import json
import os

DB_PATH = "database/veiculos.db"
OUTPUT_DIR = "data"
OUTPUT_JSON = os.path.join(OUTPUT_DIR, "veiculos_raw.json")


def exportar_json():
    # Garante que a pasta data/ existe
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    resultado = {"marcas": []}

    # =========================
    # Marcas
    # =========================
    cur.execute("SELECT * FROM marcas ORDER BY nome")
    marcas = cur.fetchall()

    for marca in marcas:
        marca_dict = {
            "id": marca["id"],
            "nome": marca["nome"],
            "modelos": []
        }

        # =========================
        # Modelos
        # =========================
        cur.execute("""
            SELECT * FROM modelos
            WHERE marca_id = ?
            ORDER BY nome
        """, (marca["id"],))
        modelos = cur.fetchall()

        for modelo in modelos:
            modelo_dict = {
                "id": modelo["id"],
                "nome": modelo["nome"],
                "url": modelo["url"],
                "anos": []
            }

            # =========================
            # Anos
            # =========================
            cur.execute("""
                SELECT * FROM modelos_anos
                WHERE modelo_id = ?
                ORDER BY ano
            """, (modelo["id"],))
            anos = cur.fetchall()

            for ano in anos:
                ano_dict = {
                    "ano": ano["ano"],
                    "versoes": []
                }

                # =========================
                # Versões
                # =========================
                cur.execute("""
                    SELECT * FROM versoes
                    WHERE modelo_ano_id = ?
                    ORDER BY versao
                """, (ano["id"],))
                versoes = cur.fetchall()

                for versao in versoes:
                    versao_dict = {
                        "id": versao["id"],
                        "versao": versao["versao"],
                        "url": versao["url"],
                        "detalhes": None
                    }

                    # =========================
                    # Detalhes
                    # =========================
                    cur.execute("""
                        SELECT * FROM versoes_detalhes
                        WHERE versao_id = ?
                    """, (versao["id"],))
                    detalhes = cur.fetchone()

                    if detalhes:
                        versao_dict["detalhes"] = {
                            "combustivel": detalhes["combustivel"],
                            "tanque_litros": detalhes["tanque_litros"],

                            "consumo": {
                                "cidade": {
                                    "alcool": detalhes["consumo_cidade_alcool"],
                                    "gasolina": detalhes["consumo_cidade_gasolina"]
                                },
                                "estrada": {
                                    "alcool": detalhes["consumo_estrada_alcool"],
                                    "gasolina": detalhes["consumo_estrada_gasolina"]
                                }
                            },

                            "motor": {
                                "cilindrada_cm3": detalhes["cilindrada_cm3"],
                                "cilindros": detalhes["cilindros"],
                                "velocidade_max_kmh": detalhes["velocidade_max_kmh"],
                                "zero_a_cem_segundos": detalhes["zero_a_cem_segundos"]
                            },

                            "dimensoes": {
                                "comprimento_mm": detalhes["comprimento_mm"],
                                "largura_mm": detalhes["largura_mm"],
                                "altura_mm": detalhes["altura_mm"],
                                "entre_eixos_mm": detalhes["entre_eixos_mm"],
                                "peso_kg": detalhes["peso_kg"],
                                "porta_malas_litros": detalhes["porta_malas_litros"]
                            },

                            "transmissao": {
                                "cambio": detalhes["cambio"],
                                "tracao": detalhes["tracao"]
                            },

                            "suspensao": {
                                "dianteira": detalhes["suspensao_dianteira"],
                                "traseira": detalhes["suspensao_traseira"]
                            },

                            "freios": {
                                "dianteiro": detalhes["freio_dianteiro"],
                                "traseiro": detalhes["freio_traseiro"]
                            }
                        }

                    ano_dict["versoes"].append(versao_dict)

                modelo_dict["anos"].append(ano_dict)

            marca_dict["modelos"].append(modelo_dict)

        resultado["marcas"].append(marca_dict)

    conn.close()

    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(resultado, f, ensure_ascii=False, indent=2)

    print(f"✅ JSON exportado com sucesso em: {OUTPUT_JSON}")


if __name__ == "__main__":
    exportar_json()
