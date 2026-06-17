from pathlib import Path
import re
import unicodedata

import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[2]

INPUT_REELS = (
    BASE_DIR
    / "data"
    / "social"
    / "davi_maia_reels_pre_campanha_2026.csv"
)

INPUT_MUNICIPIOS = (
    BASE_DIR
    / "data"
    / "final"
    / "ranking_estrategico_alagoas_2024.csv"
)

OUTPUT_PRESENCA = (
    BASE_DIR
    / "data"
    / "social"
    / "presenca_territorial_davi_maia.csv"
)

OUTPUT_RESUMO = (
    BASE_DIR
    / "data"
    / "social"
    / "resumo_municipios_visitados.csv"
)


BAIRROS_MACEIO = [
    "JACINTINHO",
    "TABULEIRO",
    "TABULEIRO DO MARTINS",
    "BENEDITO BENTES",
    "VERGEL",
    "CLIMA BOM",
    "GRUTA",
    "PONTA VERDE",
    "PAJUCARA",
    "PAJUCARA",
    "JATIUCA",
    "FAROL",
    "TRAPICHE",
    "LEVADA",
    "BEBEDOURO",
]


def normalizar(texto):
    if pd.isna(texto):
        return ""

    texto = str(texto).upper().strip()

    texto = unicodedata.normalize("NFKD", texto)

    texto = "".join(
        c
        for c in texto
        if not unicodedata.combining(c)
    )

    return texto


def carregar_municipios():

    df = pd.read_csv(INPUT_MUNICIPIOS)

    municipios = (
        df["municipio"]
        .dropna()
        .astype(str)
        .tolist()
    )

    return municipios


def identificar_municipios(texto, municipios):

    encontrados = []

    texto_norm = normalizar(texto)

    for municipio in municipios:

        municipio_norm = normalizar(municipio)

        if municipio_norm in texto_norm:
            encontrados.append(municipio)

    for bairro in BAIRROS_MACEIO:

        if bairro in texto_norm:

            if "Maceió" not in encontrados:
                encontrados.append("Maceió")

    return sorted(list(set(encontrados)))


def extrair_liderancas(texto):

    liderancas = []

    padroes = [

        r"prefeito[a]?\s+([A-ZÀ-Ú][A-Za-zÀ-ú\s]{3,50})",

        r"vereador[a]?\s+([A-ZÀ-Ú][A-Za-zÀ-ú\s]{3,50})",

        r"deputado[a]?\s+([A-ZÀ-Ú][A-Za-zÀ-ú\s]{3,50})",

        r"senador[a]?\s+([A-ZÀ-Ú][A-Za-zÀ-ú\s]{3,50})",

        r"@([a-zA-Z0-9_.]+)",
    ]

    for padrao in padroes:

        encontrados = re.findall(
            padrao,
            texto,
            flags=re.IGNORECASE
        )

        for item in encontrados:

            item = str(item).strip()

            if len(item) > 2:
                liderancas.append(item)

    return sorted(list(set(liderancas)))


def main():

    if not INPUT_REELS.exists():
        raise FileNotFoundError(INPUT_REELS)

    municipios = carregar_municipios()

    reels = pd.read_csv(INPUT_REELS)

    registros = []

    print(
        f"Reels carregados: {len(reels)}"
    )

    for _, row in reels.iterrows():

        texto = str(
            row.get("texto", "")
        )

        municipios_encontrados = (
            identificar_municipios(
                texto,
                municipios
            )
        )

        liderancas = (
            extrair_liderancas(texto)
        )

        if not municipios_encontrados:
            continue

        for municipio in municipios_encontrados:

            registros.append(
                {
                    "data_postagem":
                        row.get(
                            "data_postagem",
                            ""
                        ),

                    "municipio":
                        municipio,

                    "liderancas":
                        "; ".join(
                            liderancas
                        ),

                    "reel_url":
                        row.get(
                            "reel_url",
                            ""
                        ),

                    "texto":
                        texto[:500]
                }
            )

    presenca = pd.DataFrame(registros)

    presenca.to_csv(
        OUTPUT_PRESENCA,
        index=False,
        encoding="utf-8-sig"
    )

    resumo = (
        presenca.groupby(
            "municipio"
        )
        .agg(
            quantidade_visitas=(
                "municipio",
                "count"
            ),

            ultima_visita=(
                "data_postagem",
                "max"
            )
        )
        .reset_index()
        .sort_values(
            "quantidade_visitas",
            ascending=False
        )
    )

    resumo.to_csv(
        OUTPUT_RESUMO,
        index=False,
        encoding="utf-8-sig"
    )

    print("\n================================")

    print(
        "ETL 005 CONCLUÍDO"
    )

    print("================================")

    print(
        f"Municípios identificados: {len(resumo)}"
    )

    print(
        f"Ocorrências territoriais: {len(presenca)}"
    )

    print(
        f"\nArquivo:"
    )

    print(
        OUTPUT_PRESENCA
    )

    print(
        OUTPUT_RESUMO
    )

    print(
        "\nTOP MUNICÍPIOS VISITADOS:"
    )

    print(
        resumo
        .head(20)
        .to_string(index=False)
    )


if __name__ == "__main__":
    main()