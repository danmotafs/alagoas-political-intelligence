from pathlib import Path
from zipfile import ZipFile
import requests
import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[2]

URL_TSE = "https://cdn.tse.jus.br/estatistica/sead/odsele/votacao_candidato_munzona/votacao_candidato_munzona_2024.zip"

RAW_DIR = BASE_DIR / "data" / "raw" / "tse_2024"
FINAL_DIR = BASE_DIR / "data" / "final"

ZIP_PATH = RAW_DIR / "votacao_candidato_munzona_2024.zip"
CSV_EXTRAIDO = RAW_DIR / "votacao_candidato_munzona_2024_BRASIL.csv"

BASE_MUNICIPIOS = FINAL_DIR / "inteligencia_politica_territorial_enriquecida.csv"

OUTPUT_VEREADORES = FINAL_DIR / "base_vereadores_alagoas_2024.csv"
OUTPUT_INTELIGENCIA = FINAL_DIR / "inteligencia_vereadores_alagoas_2024.csv"


def baixar_arquivo():
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    if ZIP_PATH.exists():
        print(f"ZIP já existe: {ZIP_PATH}")
        return

    print("Baixando base oficial do TSE...")
    response = requests.get(URL_TSE, timeout=120)
    response.raise_for_status()

    with open(ZIP_PATH, "wb") as f:
        f.write(response.content)

    print(f"Arquivo baixado: {ZIP_PATH}")


def extrair_zip():
    if CSV_EXTRAIDO.exists():
        print(f"CSV já extraído: {CSV_EXTRAIDO}")
        return

    print("Extraindo ZIP...")
    with ZipFile(ZIP_PATH, "r") as zip_ref:
        arquivos = zip_ref.namelist()

        csv_brasil = [
            nome for nome in arquivos
            if nome.endswith(".csv") and "BRASIL" in nome.upper()
        ]

        if not csv_brasil:
            raise FileNotFoundError("CSV BRASIL não encontrado dentro do ZIP do TSE.")

        arquivo_csv = csv_brasil[0]
        zip_ref.extract(arquivo_csv, RAW_DIR)

        origem = RAW_DIR / arquivo_csv
        origem.rename(CSV_EXTRAIDO)

    print(f"CSV extraído: {CSV_EXTRAIDO}")


def carregar_tse():
    print("Carregando base do TSE...")

    df = pd.read_csv(
        CSV_EXTRAIDO,
        sep=";",
        encoding="latin1",
        dtype=str,
        low_memory=False
    )

    print(f"Linhas carregadas do TSE: {len(df)}")
    return df


def normalizar_numero(valor):
    if pd.isna(valor):
        return 0

    valor = str(valor).strip().replace(",", ".")

    try:
        return float(valor)
    except ValueError:
        return 0


def filtrar_vereadores_alagoas(df):
    print("Filtrando vereadores de Alagoas...")

    df = df.copy()

    df = df[df["SG_UF"] == "AL"]
    df = df[df["DS_CARGO"].str.upper() == "VEREADOR"]

    df["situacao_total_turno"] = df["DS_SIT_TOT_TURNO"].fillna("").str.upper()

    df = df[
        df["situacao_total_turno"].str.contains("ELEITO", na=False)
    ]

    df["votos"] = df["QT_VOTOS_NOMINAIS"].apply(normalizar_numero).astype(int)

    colunas = {
    "NM_MUNICIPIO": "municipio",
    "CD_MUNICIPIO": "codigo_tse_municipio",
    "NR_CANDIDATO": "numero",
    "NM_CANDIDATO": "vereador",
    "NM_URNA_CANDIDATO": "nome_urna",
    "SG_PARTIDO": "partido",
    "NM_PARTIDO": "nome_partido",
    "DS_SIT_TOT_TURNO": "situacao",
    "votos": "votos",
}

    df_saida = df[list(colunas.keys())].rename(columns=colunas)

    df_saida["municipio"] = df_saida["municipio"].str.upper().str.strip()
    df_saida["vereador"] = df_saida["vereador"].str.upper().str.strip()
    df_saida["nome_urna"] = df_saida["nome_urna"].str.upper().str.strip()
    df_saida["partido"] = df_saida["partido"].str.upper().str.strip()

    df_saida = df_saida.sort_values(
        ["municipio", "votos"],
        ascending=[True, False]
    )

    df_saida["rank_vereador_municipio"] = (
        df_saida.groupby("municipio")["votos"]
        .rank(method="first", ascending=False)
        .astype(int)
    )

    print(f"Vereadores eleitos em AL: {len(df_saida)}")
    print(f"Municípios com vereadores: {df_saida['municipio'].nunique()}")

    return df_saida


def carregar_base_municipios():
    if not BASE_MUNICIPIOS.exists():
        raise FileNotFoundError(f"Base municipal não encontrada: {BASE_MUNICIPIOS}")

    df = pd.read_csv(BASE_MUNICIPIOS)

    colunas = [
        "municipio",
        "eleitorado_2024",
        "populacao_estimada_2024",
        "indice_estrategico_pct",
        "prioridade_final",
        "prefeito",
        "partido",
        "grupo_politico",
        "relacao_davi",
        "score_articulacao",
    ]

    colunas_existentes = [c for c in colunas if c in df.columns]
    df = df[colunas_existentes].copy()

    df["municipio"] = df["municipio"].str.upper().str.strip()

    return df


def classificar_potencial(percentual_votos_municipio, votos):
    if votos >= 2000 or percentual_votos_municipio >= 8:
        return "Muito Alto"

    if votos >= 1000 or percentual_votos_municipio >= 5:
        return "Alto"

    if votos >= 500 or percentual_votos_municipio >= 2.5:
        return "Médio"

    return "Baixo"


def enriquecer_vereadores(df_vereadores, df_municipios):
    print("Enriquecendo vereadores com inteligência territorial...")

    df = df_vereadores.merge(
        df_municipios,
        on="municipio",
        how="left",
        suffixes=("", "_municipio")
    )

    df["eleitorado_2024"] = pd.to_numeric(df["eleitorado_2024"], errors="coerce").fillna(0).astype(int)
    df["populacao_estimada_2024"] = pd.to_numeric(df["populacao_estimada_2024"], errors="coerce").fillna(0).astype(int)
    df["indice_estrategico_pct"] = pd.to_numeric(df["indice_estrategico_pct"], errors="coerce").fillna(0)
    df["score_articulacao"] = pd.to_numeric(df["score_articulacao"], errors="coerce").fillna(0)

    df["percentual_votos_municipio"] = df.apply(
        lambda row: round((row["votos"] / row["eleitorado_2024"]) * 100, 2)
        if row["eleitorado_2024"] > 0 else 0,
        axis=1
    )

    df["potencial_transferencia_conservador_20pct"] = (df["votos"] * 0.20).round().astype(int)
    df["potencial_transferencia_moderado_35pct"] = (df["votos"] * 0.35).round().astype(int)
    df["potencial_transferencia_alto_50pct"] = (df["votos"] * 0.50).round().astype(int)

    df["potencial_politico_vereador"] = df.apply(
        lambda row: classificar_potencial(
            row["percentual_votos_municipio"],
            row["votos"]
        ),
        axis=1
    )

    df["indice_influencia_vereador"] = (
        (df["percentual_votos_municipio"] * 0.55)
        + (df["indice_estrategico_pct"] * 0.30)
        + (df["score_articulacao"] * 0.15)
    ).round(2)

    df = df.sort_values(
        ["indice_influencia_vereador", "votos"],
        ascending=[False, False]
    )

    return df


def salvar_resultados(df_vereadores, df_inteligencia):
    FINAL_DIR.mkdir(parents=True, exist_ok=True)

    df_vereadores.to_csv(OUTPUT_VEREADORES, index=False, encoding="utf-8-sig")
    df_inteligencia.to_csv(OUTPUT_INTELIGENCIA, index=False, encoding="utf-8-sig")

    print("\nArquivos gerados:")
    print(f"- {OUTPUT_VEREADORES}")
    print(f"- {OUTPUT_INTELIGENCIA}")


def imprimir_resumo(df_inteligencia):
    print("\n" + "=" * 80)
    print("RESUMO — ETL 014 | BASE DE VEREADORES ALAGOAS 2024")
    print("=" * 80)

    print(f"Total de vereadores eleitos: {len(df_inteligencia)}")
    print(f"Municípios cobertos: {df_inteligencia['municipio'].nunique()}")
    print(f"Partidos identificados: {df_inteligencia['partido'].nunique()}")
    print(f"Total de votos nominais dos vereadores eleitos: {df_inteligencia['votos'].sum():,}".replace(",", "."))

    print("\nTop 15 vereadores por votos:")
    top = df_inteligencia.sort_values("votos", ascending=False).head(15)

    for _, row in top.iterrows():
        print(
            f"- {row['municipio']} | {row['nome_urna']} | "
            f"{row['partido']} | {row['votos']} votos | "
            f"Potencial: {row['potencial_politico_vereador']}"
        )

    print("\nDistribuição por potencial:")
    print(df_inteligencia["potencial_politico_vereador"].value_counts())

    print("\nETL 014 concluído com sucesso.")


def main():
    baixar_arquivo()
    extrair_zip()

    df_tse = carregar_tse()
    df_vereadores = filtrar_vereadores_alagoas(df_tse)

    df_municipios = carregar_base_municipios()
    df_inteligencia = enriquecer_vereadores(df_vereadores, df_municipios)

    salvar_resultados(df_vereadores, df_inteligencia)
    imprimir_resumo(df_inteligencia)


if __name__ == "__main__":
    main()