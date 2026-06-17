from pathlib import Path
import unicodedata

import pandas as pd


ANO = 2024
UF = "AL"

BASE_DIR = Path(__file__).resolve().parents[2]

POPULACAO_PATH = BASE_DIR / "data" / "processed" / "municipios_alagoas_populacao_2024.csv"
ELEITORADO_PATH = BASE_DIR / "data" / "processed" / "municipios_alagoas_eleitorado_2024.csv"

FINAL_DIR = BASE_DIR / "data" / "final"
OUTPUT_CSV = FINAL_DIR / "alagoas_municipios_base_2024.csv"
OUTPUT_XLSX = FINAL_DIR / "alagoas_municipios_base_2024.xlsx"


def normalizar_texto(texto: str) -> str:
    if pd.isna(texto):
        return ""

    texto = str(texto).strip().upper()
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    return texto


def carregar_bases() -> tuple[pd.DataFrame, pd.DataFrame]:
    if not POPULACAO_PATH.exists():
        raise FileNotFoundError(f"Arquivo de população não encontrado: {POPULACAO_PATH}")

    if not ELEITORADO_PATH.exists():
        raise FileNotFoundError(f"Arquivo de eleitorado não encontrado: {ELEITORADO_PATH}")

    df_pop = pd.read_csv(POPULACAO_PATH, dtype=str)
    df_ele = pd.read_csv(ELEITORADO_PATH, dtype=str)

    return df_pop, df_ele


def preparar_populacao(df: pd.DataFrame) -> pd.DataFrame:
    colunas_esperadas = {"codigo_ibge", "municipio", "populacao_estimada_2024"}

    faltantes = colunas_esperadas - set(df.columns)
    if faltantes:
        raise KeyError(f"Colunas ausentes na base de população: {faltantes}")

    df = df.copy()

    df["municipio_normalizado"] = df["municipio"].apply(normalizar_texto)
    df["populacao_estimada_2024"] = pd.to_numeric(
        df["populacao_estimada_2024"],
        errors="coerce",
    )

    return df[
        [
            "codigo_ibge",
            "municipio",
            "municipio_normalizado",
            "populacao_estimada_2024",
        ]
    ]


def preparar_eleitorado(df: pd.DataFrame) -> pd.DataFrame:
    colunas_esperadas = {"municipio_normalizado", "eleitorado_2024"}

    faltantes = colunas_esperadas - set(df.columns)
    if faltantes:
        raise KeyError(f"Colunas ausentes na base de eleitorado: {faltantes}")

    df = df.copy()

    df["municipio_normalizado"] = df["municipio_normalizado"].apply(normalizar_texto)
    df["eleitorado_2024"] = pd.to_numeric(
        df["eleitorado_2024"],
        errors="coerce",
    )

    return df[
        [
            "municipio_normalizado",
            "eleitorado_2024",
        ]
    ]


def consolidar_bases(df_pop: pd.DataFrame, df_ele: pd.DataFrame) -> pd.DataFrame:
    df = df_pop.merge(
        df_ele,
        on="municipio_normalizado",
        how="left",
        validate="one_to_one",
    )

    if df["eleitorado_2024"].isna().any():
        municipios_sem_eleitorado = df[df["eleitorado_2024"].isna()]["municipio"].tolist()
        raise ValueError(f"Municípios sem eleitorado após merge: {municipios_sem_eleitorado}")

    populacao_total = df["populacao_estimada_2024"].sum()
    eleitorado_total = df["eleitorado_2024"].sum()

    df["taxa_eleitorado"] = df["eleitorado_2024"] / df["populacao_estimada_2024"]
    df["participacao_populacao"] = df["populacao_estimada_2024"] / populacao_total
    df["participacao_eleitorado"] = df["eleitorado_2024"] / eleitorado_total

    df["indice_estrategico_inicial"] = (
        0.70 * df["participacao_eleitorado"]
        + 0.30 * df["participacao_populacao"]
    )

    df["uf"] = UF
    df["ano"] = ANO

    df = df[
        [
            "uf",
            "ano",
            "codigo_ibge",
            "municipio",
            "municipio_normalizado",
            "populacao_estimada_2024",
            "eleitorado_2024",
            "taxa_eleitorado",
            "participacao_populacao",
            "participacao_eleitorado",
            "indice_estrategico_inicial",
        ]
    ]

    df = df.sort_values(
        by="indice_estrategico_inicial",
        ascending=False,
    ).reset_index(drop=True)

    df.insert(0, "rank_estrategico_inicial", df.index + 1)

    return df


def validar_resultado(df: pd.DataFrame) -> None:
    total_municipios = df["municipio_normalizado"].nunique()
    total_populacao = df["populacao_estimada_2024"].sum()
    total_eleitorado = df["eleitorado_2024"].sum()

    encontrados = set(df["municipio_normalizado"])

    print("\nVALIDAÇÃO ETL 003")
    print(f"Municípios consolidados: {total_municipios}")
    print(f"População total AL: {total_populacao:,.0f}".replace(",", "."))
    print(f"Eleitorado total AL: {total_eleitorado:,.0f}".replace(",", "."))
    print(f"Maceió presente: {'MACEIO' in encontrados}")
    print(f"Arapiraca presente: {'ARAPIRACA' in encontrados}")
    print(f"Quebrangulo presente: {'QUEBRANGULO' in encontrados}")

    if total_municipios != 102:
        raise ValueError(f"Esperado: 102 municípios. Encontrado: {total_municipios}")

    for municipio in ["MACEIO", "ARAPIRACA", "QUEBRANGULO"]:
        if municipio not in encontrados:
            raise ValueError(f"Município obrigatório ausente: {municipio}")

    if df["populacao_estimada_2024"].isna().any():
        raise ValueError("Há municípios com população ausente.")

    if df["eleitorado_2024"].isna().any():
        raise ValueError("Há municípios com eleitorado ausente.")


def salvar_resultado(df: pd.DataFrame) -> None:
    FINAL_DIR.mkdir(parents=True, exist_ok=True)

    df.to_csv(OUTPUT_CSV, index=False, encoding="utf-8-sig")
    df.to_excel(OUTPUT_XLSX, index=False)

    print("\nArquivos gerados:")
    print(OUTPUT_CSV)
    print(OUTPUT_XLSX)


def main() -> None:
    print("Iniciando ETL 003 — Merge População + Eleitorado")

    df_pop, df_ele = carregar_bases()

    df_pop = preparar_populacao(df_pop)
    df_ele = preparar_eleitorado(df_ele)

    df_final = consolidar_bases(df_pop, df_ele)

    validar_resultado(df_final)
    salvar_resultado(df_final)

    print("\nTop 20 municípios por índice estratégico inicial:")
    print(
        df_final[
            [
                "rank_estrategico_inicial",
                "municipio",
                "populacao_estimada_2024",
                "eleitorado_2024",
                "indice_estrategico_inicial",
            ]
        ]
        .head(20)
        .to_string(index=False)
    )

    print("\nETL 003 concluído com sucesso.")


if __name__ == "__main__":
    main()