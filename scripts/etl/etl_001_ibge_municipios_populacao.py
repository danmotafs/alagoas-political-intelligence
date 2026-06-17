from pathlib import Path
from datetime import datetime
import pandas as pd
import requests


BASE_DIR = Path(__file__).resolve().parents[2]

RAW_DIR = BASE_DIR / "data" / "raw"
PROCESSED_DIR = BASE_DIR / "data" / "processed"

RAW_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)


UF = "AL"
ANO_POPULACAO = "2024"


def extrair_municipios_alagoas() -> pd.DataFrame:
    url = f"https://servicodados.ibge.gov.br/api/v1/localidades/estados/{UF}/municipios"

    response = requests.get(url, timeout=30)
    response.raise_for_status()

    dados = response.json()

    registros = []

    for item in dados:
        registros.append({
            "codigo_ibge": item["id"],
            "municipio": item["nome"],
            "uf": UF,
        })

    return pd.DataFrame(registros)


def extrair_populacao_sidra() -> pd.DataFrame:
    url = (
        "https://apisidra.ibge.gov.br/values/"
        f"t/6579/n6/all/v/9324/p/{ANO_POPULACAO}?formato=json"
    )

    response = requests.get(url, timeout=60)
    response.raise_for_status()

    dados = response.json()[1:]

    registros = []

    for item in dados:
        codigo = int(item["D1C"])
        valor = item["V"]

        populacao = None
        if valor not in ["-", "...", ""]:
            populacao = int(valor.replace(".", "").replace(",", ""))

        registros.append({
            "codigo_ibge": codigo,
            "populacao_estimada_2024": populacao,
        })

    return pd.DataFrame(registros)


def main():
    print("Iniciando ETL 001 — IBGE Municípios + População")

    municipios = extrair_municipios_alagoas()
    populacao = extrair_populacao_sidra()

    base = municipios.merge(
        populacao,
        on="codigo_ibge",
        how="left"
    )

    base["fonte_municipios"] = "IBGE API Localidades"
    base["fonte_populacao"] = "IBGE SIDRA Tabela 6579"
    base["ano_populacao"] = ANO_POPULACAO
    base["data_extracao"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    base["status_populacao"] = base["populacao_estimada_2024"].apply(
        lambda x: "Validado" if pd.notna(x) else "A validar"
    )

    base = base.sort_values("municipio").reset_index(drop=True)

    raw_path = RAW_DIR / "ibge_municipios_alagoas_raw.csv"
    processed_csv_path = PROCESSED_DIR / "municipios_alagoas_populacao_2024.csv"
    processed_xlsx_path = PROCESSED_DIR / "municipios_alagoas_populacao_2024.xlsx"

    municipios.to_csv(raw_path, index=False, encoding="utf-8-sig")
    base.to_csv(processed_csv_path, index=False, encoding="utf-8-sig")
    base.to_excel(processed_xlsx_path, index=False)

    print("ETL 001 finalizado com sucesso.")
    print(f"Municípios extraídos: {len(base)}")
    print(f"Arquivo raw: {raw_path}")
    print(f"Arquivo CSV processado: {processed_csv_path}")
    print(f"Arquivo Excel processado: {processed_xlsx_path}")


if __name__ == "__main__":
    main()