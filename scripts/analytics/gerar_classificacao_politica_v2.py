from pathlib import Path

import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[2]

INPUT_FILE = (
    BASE_DIR
    / "data"
    / "final"
    / "base_liderancas_alagoas_2024.csv"
)

OUTPUT_CSV = (
    BASE_DIR
    / "data"
    / "reference"
    / "classificacao_politica_alagoas_v2.csv"
)

OUTPUT_XLSX = (
    BASE_DIR
    / "data"
    / "reference"
    / "classificacao_politica_alagoas_v2.xlsx"
)


def carregar_base() -> pd.DataFrame:
    if not INPUT_FILE.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {INPUT_FILE}")

    return pd.read_csv(INPUT_FILE)


def gerar_classificacao_v2(df: pd.DataFrame) -> pd.DataFrame:
    colunas_necessarias = [
        "rank_estrategico",
        "municipio",
        "lideranca_principal",
        "cargo_lideranca",
        "partido_lideranca",
        "votos_lideranca",
        "percentual_lideranca",
        "eleitorado_2024",
        "indice_estrategico_pct",
        "prioridade_politica",
        "visitado_pre_campanha",
        "quantidade_visitas",
        "ultima_visita",
    ]

    faltantes = [c for c in colunas_necessarias if c not in df.columns]

    if faltantes:
        raise KeyError(f"Colunas ausentes na base de lideranças: {faltantes}")

    base = df[colunas_necessarias].copy()

    base = base.rename(
        columns={
            "rank_estrategico": "rank_estrategico",
            "municipio": "municipio",
            "lideranca_principal": "prefeito",
            "cargo_lideranca": "cargo",
            "partido_lideranca": "partido",
            "votos_lideranca": "votos_prefeito",
            "percentual_lideranca": "percentual_prefeito",
        }
    )

    base["grupo_politico"] = ""
    base["relacao_davi"] = ""
    base["peso_politico"] = ""
    base["status_articulacao"] = ""
    base["observacoes"] = ""

    base["fonte_dados"] = "TSE 2024 + IBGE 2024 + TSE Eleitorado 2024 + Instagram/Reels"
    base["status_classificacao"] = "pendente_revisao"

    colunas_finais = [
        "rank_estrategico",
        "municipio",
        "prefeito",
        "cargo",
        "partido",
        "votos_prefeito",
        "percentual_prefeito",
        "eleitorado_2024",
        "indice_estrategico_pct",
        "prioridade_politica",
        "visitado_pre_campanha",
        "quantidade_visitas",
        "ultima_visita",
        "grupo_politico",
        "relacao_davi",
        "peso_politico",
        "status_articulacao",
        "observacoes",
        "fonte_dados",
        "status_classificacao",
    ]

    return base[colunas_finais].sort_values("rank_estrategico")


def aplicar_classificacao_inicial(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    regras = {
        "Arapiraca": {
            "grupo_politico": "Calheiros",
            "relacao_davi": "aliado_forte",
            "peso_politico": "muito_alto",
            "status_articulacao": "prioritario",
            "observacoes": "Segundo maior colégio eleitoral de Alagoas.",
        },
        "Maceió": {
            "grupo_politico": "Independente",
            "relacao_davi": "adversario_potencial",
            "peso_politico": "muito_alto",
            "status_articulacao": "mapear",
            "observacoes": "Capital do estado e maior colégio eleitoral.",
        },
        "Quebrangulo": {
            "grupo_politico": "Base Davi Maia",
            "relacao_davi": "base_familiar",
            "peso_politico": "alto",
            "status_articulacao": "consolidado",
            "observacoes": "Município de origem política da família Maia.",
        },
    }

    for municipio, valores in regras.items():
        mask = df["municipio"].str.upper() == municipio.upper()

        for coluna, valor in valores.items():
            df.loc[mask, coluna] = valor

        df.loc[mask, "status_classificacao"] = "classificacao_inicial"

    return df


def salvar(df: pd.DataFrame) -> None:
    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)

    df.to_csv(
        OUTPUT_CSV,
        index=False,
        encoding="utf-8-sig",
    )

    df.to_excel(
        OUTPUT_XLSX,
        index=False,
    )


def validar(df: pd.DataFrame) -> None:
    print("\nVALIDAÇÃO CLASSIFICAÇÃO POLÍTICA V2")
    print(f"Registros: {len(df)}")
    print(f"Municípios únicos: {df['municipio'].nunique()}")
    print(f"Classificados: {(df['status_classificacao'] != 'pendente_revisao').sum()}")
    print(f"Pendentes: {(df['status_classificacao'] == 'pendente_revisao').sum()}")

    print("\nTop 30 para revisão política:")
    print(
        df[
            [
                "rank_estrategico",
                "municipio",
                "prefeito",
                "partido",
                "votos_prefeito",
                "visitado_pre_campanha",
                "grupo_politico",
                "relacao_davi",
                "status_classificacao",
            ]
        ]
        .head(30)
        .to_string(index=False)
    )


def main() -> None:
    print("Gerando classificacao_politica_alagoas_v2.csv")

    df = carregar_base()
    classificacao = gerar_classificacao_v2(df)
    classificacao = aplicar_classificacao_inicial(classificacao)

    validar(classificacao)
    salvar(classificacao)

    print("\nArquivos gerados:")
    print(OUTPUT_CSV)
    print(OUTPUT_XLSX)

    print("\nClassificação política V2 criada com sucesso.")


if __name__ == "__main__":
    main()