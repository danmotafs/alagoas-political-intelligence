import io
import zipfile
import unicodedata
from pathlib import Path

import pandas as pd
import requests


TSE_URL = "https://cdn.tse.jus.br/estatistica/sead/odsele/perfil_eleitorado/perfil_eleitorado_2024.zip"

UF = "AL"
ANO = 2024

BASE_DIR = Path(__file__).resolve().parents[2]
RAW_DIR = BASE_DIR / "data" / "raw"
PROCESSED_DIR = BASE_DIR / "data" / "processed"

RAW_ZIP_PATH = RAW_DIR / "perfil_eleitorado_2024.zip"
OUTPUT_CSV = PROCESSED_DIR / "municipios_alagoas_eleitorado_2024.csv"
OUTPUT_XLSX = PROCESSED_DIR / "municipios_alagoas_eleitorado_2024.xlsx"


def normalizar_texto(texto: str) -> str:
    if pd.isna(texto):
        return ""

    texto = str(texto).strip().upper()
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    return texto


def baixar_base_tse() -> bytes:
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    print("Baixando base oficial do TSE...")
    response = requests.get(TSE_URL, timeout=120)
    response.raise_for_status()

    RAW_ZIP_PATH.write_bytes(response.content)
    print(f"Arquivo salvo em: {RAW_ZIP_PATH}")

    return response.content


def localizar_csv_no_zip(zip_bytes: bytes) -> str:
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as z:
        arquivos_csv = [name for name in z.namelist() if name.lower().endswith(".csv")]

        if not arquivos_csv:
            raise FileNotFoundError("Nenhum arquivo CSV encontrado dentro do ZIP do TSE.")

        return arquivos_csv[0]


def carregar_csv_tse(zip_bytes: bytes, csv_name: str) -> pd.DataFrame:
    print(f"Lendo CSV interno: {csv_name}")

    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as z:
        with z.open(csv_name) as file:
            df = pd.read_csv(
                file,
                sep=";",
                encoding="latin1",
                dtype=str,
                low_memory=False,
            )

    df.columns = [normalizar_texto(col) for col in df.columns]
    return df


def encontrar_coluna(df: pd.DataFrame, candidatos: list[str]) -> str:
    colunas = list(df.columns)

    for candidato in candidatos:
        candidato_norm = normalizar_texto(candidato)
        if candidato_norm in colunas:
            return candidato_norm

    raise KeyError(
        f"Nenhuma das colunas esperadas foi encontrada: {candidatos}\n"
        f"Colunas disponíveis: {colunas}"
    )


def processar_eleitorado_municipal(df: pd.DataFrame) -> pd.DataFrame:
    coluna_uf = encontrar_coluna(df, ["SG_UF", "UF"])
    coluna_municipio = encontrar_coluna(df, ["NM_MUNICIPIO", "MUNICIPIO"])
    coluna_eleitores = encontrar_coluna(
        df,
        [
            "QT_ELEITORES_PERFIL",
            "QT_ELEITORES",
            "QTD_ELEITORES",
            "ELEITORES",
        ],
    )

    df_al = df[df[coluna_uf].str.upper() == UF].copy()

    if df_al.empty:
        raise ValueError(f"Nenhum registro encontrado para UF={UF}.")

    df_al[coluna_eleitores] = (
        df_al[coluna_eleitores]
        .astype(str)
        .str.replace(".", "", regex=False)
        .str.replace(",", ".", regex=False)
    )

    df_al[coluna_eleitores] = pd.to_numeric(df_al[coluna_eleitores], errors="coerce").fillna(0)

    resultado = (
        df_al.groupby(coluna_municipio, as_index=False)[coluna_eleitores]
        .sum()
        .rename(
            columns={
                coluna_municipio: "municipio",
                coluna_eleitores: "eleitorado_2024",
            }
        )
    )

    resultado["municipio"] = resultado["municipio"].str.title()
    resultado["municipio_normalizado"] = resultado["municipio"].apply(normalizar_texto)
    resultado["uf"] = UF
    resultado["ano"] = ANO

    resultado = resultado[
        [
            "uf",
            "ano",
            "municipio",
            "municipio_normalizado",
            "eleitorado_2024",
        ]
    ].sort_values("municipio")

    resultado["eleitorado_2024"] = resultado["eleitorado_2024"].astype(int)

    return resultado


def validar_resultado(df: pd.DataFrame) -> None:
    total_municipios = df["municipio_normalizado"].nunique()
    total_eleitorado = df["eleitorado_2024"].sum()

    municipios_obrigatorios = ["MACEIO", "ARAPIRACA", "QUEBRANGULO"]
    encontrados = set(df["municipio_normalizado"])

    print("\nVALIDAÇÃO")
    print(f"Municípios encontrados: {total_municipios}")
    print(f"Eleitorado total AL: {total_eleitorado:,}".replace(",", "."))
    print(f"Maceió presente: {'MACEIO' in encontrados}")
    print(f"Arapiraca presente: {'ARAPIRACA' in encontrados}")
    print(f"Quebrangulo presente: {'QUEBRANGULO' in encontrados}")

    if total_municipios != 102:
        raise ValueError(f"Esperado: 102 municípios. Encontrado: {total_municipios}.")

    for municipio in municipios_obrigatorios:
        if municipio not in encontrados:
            raise ValueError(f"Município obrigatório ausente: {municipio}")

    if total_eleitorado <= 0:
        raise ValueError("Eleitorado total inválido.")


def salvar_resultado(df: pd.DataFrame) -> None:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    df.to_csv(OUTPUT_CSV, index=False, encoding="utf-8-sig")
    df.to_excel(OUTPUT_XLSX, index=False)

    print("\nArquivos gerados:")
    print(OUTPUT_CSV)
    print(OUTPUT_XLSX)


def main() -> None:
    zip_bytes = baixar_base_tse()
    csv_name = localizar_csv_no_zip(zip_bytes)
    df_bruto = carregar_csv_tse(zip_bytes, csv_name)
    df_final = processar_eleitorado_municipal(df_bruto)

    validar_resultado(df_final)
    salvar_resultado(df_final)

    print("\nETL 002 concluído com sucesso.")


if __name__ == "__main__":
    main()