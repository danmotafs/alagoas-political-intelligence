from pathlib import Path
import unicodedata

import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[2]

INPUT_RANKING = BASE_DIR / "data" / "final" / "ranking_estrategico_alagoas_2024.csv"
INPUT_POLITICA = BASE_DIR / "data" / "final" / "base_politica_municipal_2024.csv"
INPUT_PRESENCA = BASE_DIR / "data" / "social" / "resumo_municipios_visitados.csv"

OUTPUT_CSV = BASE_DIR / "data" / "final" / "inteligencia_politica_territorial_2024_2026.csv"
OUTPUT_XLSX = BASE_DIR / "data" / "final" / "inteligencia_politica_territorial_2024_2026.xlsx"
OUTPUT_PRIORITARIOS_NAO_VISITADOS = BASE_DIR / "data" / "final" / "municipios_prioritarios_nao_visitados_davi_maia.csv"


def normalizar(texto: str) -> str:
    if pd.isna(texto):
        return ""

    texto = str(texto).strip().upper()
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    return texto


def carregar_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {path}")

    return pd.read_csv(path)


def preparar_ranking(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["municipio_normalizado"] = df["municipio"].apply(normalizar)

    return df[
        [
            "rank",
            "municipio",
            "municipio_normalizado",
            "populacao_estimada_2024",
            "eleitorado_2024",
            "participacao_eleitorado_pct",
            "indice_estrategico_pct",
            "prioridade_politica",
        ]
    ]


def preparar_politica(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["municipio_normalizado"] = df["municipio"].apply(normalizar)

    colunas = [
        "municipio_normalizado",
        "prefeito",
        "vice_prefeito",
        "partido",
        "numero",
        "votos_prefeito",
        "percentual_prefeito",
        "segundo_colocado",
        "partido_segundo_colocado",
        "votos_segundo_colocado",
        "percentual_segundo_colocado",
        "margem_vitoria_votos",
        "margem_vitoria_pct",
        "status_extracao",
    ]

    colunas_existentes = [c for c in colunas if c in df.columns]

    return df[colunas_existentes]


def preparar_presenca(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    if df.empty:
        return pd.DataFrame(
            columns=[
                "municipio_normalizado",
                "visitado_pre_campanha",
                "quantidade_visitas",
                "ultima_visita",
            ]
        )

    df["municipio_normalizado"] = df["municipio"].apply(normalizar)

    df["visitado_pre_campanha"] = True

    return df[
        [
            "municipio_normalizado",
            "visitado_pre_campanha",
            "quantidade_visitas",
            "ultima_visita",
        ]
    ]


def classificar_status_visitacao(row) -> str:
    if row["visitado_pre_campanha"]:
        return "Visitado"

    if row["rank"] <= 20:
        return "Prioritário não visitado"

    if row["rank"] <= 40:
        return "Médio potencial não visitado"

    return "Não visitado"


def calcular_capital_politico(row) -> float:
    votos = row.get("votos_prefeito", 0)
    indice = row.get("indice_estrategico_pct", 0)

    try:
        votos = float(votos)
    except Exception:
        votos = 0

    try:
        indice = float(indice)
    except Exception:
        indice = 0

    return votos * indice


def consolidar(ranking: pd.DataFrame, politica: pd.DataFrame, presenca: pd.DataFrame) -> pd.DataFrame:
    df = ranking.merge(
        politica,
        on="municipio_normalizado",
        how="left",
        validate="one_to_one",
    )

    df = df.merge(
        presenca,
        on="municipio_normalizado",
        how="left",
        validate="one_to_one",
    )

    df["visitado_pre_campanha"] = df["visitado_pre_campanha"].fillna(False)
    df["quantidade_visitas"] = df["quantidade_visitas"].fillna(0).astype(int)
    df["ultima_visita"] = df["ultima_visita"].fillna("")

    df["status_visitacao"] = df.apply(classificar_status_visitacao, axis=1)
    df["capital_politico_prefeito"] = df.apply(calcular_capital_politico, axis=1)

    df["grupo_politico"] = ""
    df["relacao_davi"] = ""

    colunas_finais = [
        "rank",
        "municipio",
        "populacao_estimada_2024",
        "eleitorado_2024",
        "participacao_eleitorado_pct",
        "indice_estrategico_pct",
        "prioridade_politica",
        "prefeito",
        "vice_prefeito",
        "partido",
        "numero",
        "votos_prefeito",
        "percentual_prefeito",
        "segundo_colocado",
        "partido_segundo_colocado",
        "votos_segundo_colocado",
        "percentual_segundo_colocado",
        "margem_vitoria_votos",
        "margem_vitoria_pct",
        "visitado_pre_campanha",
        "quantidade_visitas",
        "ultima_visita",
        "status_visitacao",
        "capital_politico_prefeito",
        "grupo_politico",
        "relacao_davi",
    ]

    colunas_existentes = [c for c in colunas_finais if c in df.columns]

    return df[colunas_existentes].sort_values("rank").reset_index(drop=True)


def validar(df: pd.DataFrame) -> None:
    print("\nVALIDAÇÃO ETL 008")
    print(f"Municípios consolidados: {len(df)}")
    print(f"Municípios visitados: {int(df['visitado_pre_campanha'].sum())}")
    print(f"Prioritários não visitados Top 20: {len(df[(df['rank'] <= 20) & (~df['visitado_pre_campanha'])])}")

    print("\nTop 20 com status de visitação:")
    print(
        df[
            [
                "rank",
                "municipio",
                "prefeito",
                "partido",
                "votos_prefeito",
                "visitado_pre_campanha",
                "ultima_visita",
                "status_visitacao",
            ]
        ]
        .head(20)
        .to_string(index=False)
    )


def salvar(df: pd.DataFrame) -> None:
    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)

    df.to_csv(OUTPUT_CSV, index=False, encoding="utf-8-sig")
    df.to_excel(OUTPUT_XLSX, index=False)

    prioritarios_nao_visitados = df[
        (df["rank"] <= 20)
        & (~df["visitado_pre_campanha"])
    ].copy()

    prioritarios_nao_visitados.to_csv(
        OUTPUT_PRIORITARIOS_NAO_VISITADOS,
        index=False,
        encoding="utf-8-sig",
    )

    print("\nArquivos gerados:")
    print(OUTPUT_CSV)
    print(OUTPUT_XLSX)
    print(OUTPUT_PRIORITARIOS_NAO_VISITADOS)


def main() -> None:
    print("Iniciando ETL 008 — Inteligência Política Territorial")

    ranking = preparar_ranking(carregar_csv(INPUT_RANKING))
    politica = preparar_politica(carregar_csv(INPUT_POLITICA))
    presenca = preparar_presenca(carregar_csv(INPUT_PRESENCA))

    df_final = consolidar(ranking, politica, presenca)

    validar(df_final)
    salvar(df_final)

    print("\nETL 008 concluído com sucesso.")


if __name__ == "__main__":
    main()