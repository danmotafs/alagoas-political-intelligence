from pathlib import Path

import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[2]

RAW_DIR = BASE_DIR / "data" / "raw"
FINAL_DIR = BASE_DIR / "data" / "final"

INPUT_FILE = RAW_DIR / "resultado_prefeitos_al_2024.csv"

OUTPUT_CSV = FINAL_DIR / "base_politica_municipal_2024.csv"
OUTPUT_XLSX = FINAL_DIR / "base_politica_municipal_2024.xlsx"


COLUNAS_CANDIDATAS = {
    "municipio": [
        "NM_MUNICIPIO",
        "municipio",
        "Municipio",
    ],
    "nome": [
        "NM_CANDIDATO",
        "nome",
        "Nome",
    ],
    "partido": [
        "SG_PARTIDO",
        "partido",
        "Partido",
    ],
    "votos": [
        "QT_VOTOS_NOMINAIS",
        "votos",
        "Votos",
    ],
    "percentual": [
        "PERCENTUAL_VOTOS",
        "percentual",
        "Percentual",
    ],
    "situacao": [
        "DS_SIT_TOT_TURNO",
        "situacao",
        "Situacao",
    ],
    "cargo": [
        "DS_CARGO",
        "cargo",
        "Cargo",
    ],
}


def localizar_coluna(df, lista_nomes):

    for nome in lista_nomes:

        if nome in df.columns:
            return nome

    return None


def carregar_base():

    if not INPUT_FILE.exists():

        raise FileNotFoundError(
            f"Arquivo não encontrado:\n{INPUT_FILE}"
        )

    print("Carregando base TSE...")

    return pd.read_csv(
        INPUT_FILE,
        sep=";",
        encoding="latin1",
        low_memory=False
    )


def preparar_base(df):

    mapa = {}

    for chave, candidatos in COLUNAS_CANDIDATAS.items():

        coluna = localizar_coluna(df, candidatos)

        if coluna:
            mapa[chave] = coluna

    obrigatorias = [
        "municipio",
        "nome",
        "partido",
        "votos"
    ]

    faltantes = [
        c
        for c in obrigatorias
        if c not in mapa
    ]

    if faltantes:

        raise Exception(
            f"Colunas obrigatórias não encontradas: {faltantes}"
        )

    base = pd.DataFrame()

    base["municipio"] = df[mapa["municipio"]]
    base["prefeito_eleito"] = df[mapa["nome"]]
    base["partido"] = df[mapa["partido"]]
    base["votos"] = df[mapa["votos"]]

    if "percentual" in mapa:
        base["percentual_votos"] = df[mapa["percentual"]]
    else:
        base["percentual_votos"] = None

    if "situacao" in mapa:
        base["situacao"] = df[mapa["situacao"]]
    else:
        base["situacao"] = None

    if "cargo" in mapa:
        base["cargo"] = df[mapa["cargo"]]
    else:
        base["cargo"] = "Prefeito"

    if "situacao" in base.columns:

        base = base[
            base["situacao"]
            .astype(str)
            .str.upper()
            .str.contains(
                "ELEITO",
                na=False
            )
        ]

    base["grupo_politico"] = ""
    base["relacao_davi"] = ""

    return base


def salvar(base):

    FINAL_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    base.to_csv(
        OUTPUT_CSV,
        index=False,
        encoding="utf-8-sig"
    )

    base.to_excel(
        OUTPUT_XLSX,
        index=False
    )

    print("\nArquivos gerados:")

    print(OUTPUT_CSV)
    print(OUTPUT_XLSX)


def validar(base):

    print("\nVALIDAÇÃO ETL 007")

    print(
        f"Registros: {len(base)}"
    )

    print(
        f"Municípios únicos: "
        f"{base['municipio'].nunique()}"
    )

    print(
        "\nTop 20 prefeitos por votação:"
    )

    print(
        base.sort_values(
            "votos",
            ascending=False
        )
        .head(20)
        [
            [
                "municipio",
                "prefeito_eleito",
                "partido",
                "votos"
            ]
        ]
        .to_string(index=False)
    )


def main():

    print(
        "Iniciando ETL 007 — Base Política Municipal"
    )

    df = carregar_base()

    base = preparar_base(df)

    validar(base)

    salvar(base)

    print(
        "\nETL 007 concluído com sucesso."
    )


if __name__ == "__main__":
    main()