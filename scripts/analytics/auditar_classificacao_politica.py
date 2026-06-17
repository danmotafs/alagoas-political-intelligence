from pathlib import Path
import unicodedata

import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[2]

ARQ_BASE = (
    BASE_DIR
    / "data"
    / "final"
    / "inteligencia_politica_territorial_2024_2026.csv"
)

ARQ_CLASSIFICACAO = (
    BASE_DIR
    / "data"
    / "reference"
    / "classificacao_politica_alagoas.csv"
)


def normalizar(texto):
    if pd.isna(texto):
        return ""

    texto = str(texto).strip().upper()

    texto = unicodedata.normalize("NFKD", texto)

    texto = "".join(
        c
        for c in texto
        if not unicodedata.combining(c)
    )

    return texto


def main():

    print("AUDITORIA DE CLASSIFICAÇÃO POLÍTICA\n")

    base = pd.read_csv(ARQ_BASE)
    classificacao = pd.read_csv(ARQ_CLASSIFICACAO)

    base["municipio_norm"] = (
        base["municipio"]
        .apply(normalizar)
    )

    classificacao["municipio_norm"] = (
        classificacao["municipio"]
        .apply(normalizar)
    )

    municipios_base = set(
        base["municipio_norm"]
    )

    municipios_classificacao = set(
        classificacao["municipio_norm"]
    )

    nao_encontrados = sorted(
        municipios_classificacao
        - municipios_base
    )

    nao_classificados = sorted(
        municipios_base
        - municipios_classificacao
    )

    print(
        f"Municípios na base principal: {len(municipios_base)}"
    )

    print(
        f"Municípios na classificação: {len(municipios_classificacao)}"
    )

    print(
        f"Municípios da classificação não encontrados: {len(nao_encontrados)}"
    )

    print(
        f"Municípios sem classificação: {len(nao_classificados)}"
    )

    print("\n==============================")
    print("NÃO ENCONTRADOS")
    print("==============================")

    for municipio in nao_encontrados:
        print(municipio)

    print("\n==============================")
    print("SEM CLASSIFICAÇÃO")
    print("==============================")

    for municipio in nao_classificados[:50]:
        print(municipio)

    print("\nAuditoria concluída.")


if __name__ == "__main__":
    main()