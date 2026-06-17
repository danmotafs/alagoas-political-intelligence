from pathlib import Path
import unicodedata

import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[2]

INPUT_INTELIGENCIA = (
    BASE_DIR
    / "data"
    / "final"
    / "inteligencia_politica_territorial_2024_2026.csv"
)

INPUT_CLASSIFICACAO = (
    BASE_DIR
    / "data"
    / "reference"
    / "classificacao_politica_alagoas.csv"
)

OUTPUT_CSV = (
    BASE_DIR
    / "data"
    / "final"
    / "inteligencia_politica_territorial_enriquecida.csv"
)

OUTPUT_XLSX = (
    BASE_DIR
    / "data"
    / "final"
    / "inteligencia_politica_territorial_enriquecida.xlsx"
)

OUTPUT_PRIORITARIOS = (
    BASE_DIR
    / "data"
    / "final"
    / "agenda_prioritaria_davi_maia.csv"
)


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


def preparar_inteligencia(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["municipio_normalizado"] = df["municipio"].apply(normalizar)
    return df


def preparar_classificacao(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["municipio_normalizado"] = df["municipio"].apply(normalizar)

    colunas = [
        "municipio_normalizado",
        "grupo_politico",
        "relacao_davi",
        "peso_politico",
        "status_articulacao",
        "observacoes",
    ]

    return df[colunas]


def calcular_score_articulacao(row) -> float:
    rank = row.get("rank", 999)
    indice = row.get("indice_estrategico_pct", 0)
    visitado = row.get("visitado_pre_campanha", False)
    relacao = str(row.get("relacao_davi", "")).lower()
    peso = str(row.get("peso_politico", "")).lower()

    try:
        rank = int(rank)
    except Exception:
        rank = 999

    try:
        indice = float(indice)
    except Exception:
        indice = 0

    score = 0

    if rank <= 10:
        score += 40
    elif rank <= 20:
        score += 30
    elif rank <= 40:
        score += 15
    else:
        score += 5

    score += indice

    if not visitado:
        score += 20

    if relacao in ["aliado_forte", "aliado"]:
        score += 20
    elif relacao == "potencial_aliado":
        score += 15
    elif relacao == "adversario_potencial":
        score += 10
    elif relacao == "adversario":
        score += 5

    if peso == "muito_alto":
        score += 15
    elif peso == "alto":
        score += 10
    elif peso == "medio":
        score += 5

    return round(score, 2)


def classificar_prioridade_final(row) -> str:
    score = row["score_articulacao"]

    if score >= 85:
        return "Prioridade Máxima"
    if score >= 65:
        return "Alta Prioridade"
    if score >= 45:
        return "Média Prioridade"
    return "Monitoramento"


def gerar_recomendacao(row) -> str:
    municipio = row["municipio"]
    prefeito = row.get("prefeito", "")
    partido = row.get("partido", "")
    visitado = row.get("visitado_pre_campanha", False)
    relacao = row.get("relacao_davi", "")
    prioridade = row.get("prioridade_final", "")

    if not visitado and prioridade in ["Prioridade Máxima", "Alta Prioridade"]:
        return (
            f"Priorizar agenda em {municipio} com {prefeito} ({partido}). "
            f"Relação política indicada: {relacao}."
        )

    if visitado:
        return (
            f"Manter acompanhamento da articulação em {municipio} com "
            f"{prefeito} ({partido})."
        )

    return (
        f"Monitorar oportunidade de aproximação em {municipio}."
    )


def enriquecer(inteligencia: pd.DataFrame, classificacao: pd.DataFrame) -> pd.DataFrame:
    df = inteligencia.merge(
        classificacao,
        on="municipio_normalizado",
        how="left",
        suffixes=("", "_classificacao"),
    )

    for coluna in [
        "grupo_politico",
        "relacao_davi",
        "peso_politico",
        "status_articulacao",
        "observacoes",
    ]:
        if coluna not in df.columns:
            df[coluna] = ""

        df[coluna] = df[coluna].fillna("não_classificado")

    df["score_articulacao"] = df.apply(calcular_score_articulacao, axis=1)
    df["prioridade_final"] = df.apply(classificar_prioridade_final, axis=1)
    df["recomendacao_estrategica"] = df.apply(gerar_recomendacao, axis=1)

    df = df.sort_values(
        by=["score_articulacao", "rank"],
        ascending=[False, True],
    ).reset_index(drop=True)

    return df


def gerar_agenda_prioritaria(df: pd.DataFrame) -> pd.DataFrame:
    agenda = df[
        (df["visitado_pre_campanha"] == False)
        & (df["prioridade_final"].isin(["Prioridade Máxima", "Alta Prioridade"]))
    ].copy()

    colunas = [
        "rank",
        "municipio",
        "prefeito",
        "partido",
        "votos_prefeito",
        "percentual_prefeito",
        "indice_estrategico_pct",
        "prioridade_politica",
        "grupo_politico",
        "relacao_davi",
        "peso_politico",
        "score_articulacao",
        "prioridade_final",
        "recomendacao_estrategica",
    ]

    colunas_existentes = [c for c in colunas if c in agenda.columns]

    return agenda[colunas_existentes]


def salvar(df: pd.DataFrame, agenda: pd.DataFrame) -> None:
    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)

    df.to_csv(OUTPUT_CSV, index=False, encoding="utf-8-sig")
    df.to_excel(OUTPUT_XLSX, index=False)

    agenda.to_csv(OUTPUT_PRIORITARIOS, index=False, encoding="utf-8-sig")


def validar(df: pd.DataFrame, agenda: pd.DataFrame) -> None:
    print("\nVALIDAÇÃO ETL 010")
    print(f"Municípios consolidados: {len(df)}")
    print(f"Municípios classificados: {(df['grupo_politico'] != 'não_classificado').sum()}")
    print(f"Agenda prioritária gerada: {len(agenda)} municípios")

    print("\nTop 20 por score de articulação:")
    print(
        df[
            [
                "municipio",
                "rank",
                "prefeito",
                "partido",
                "visitado_pre_campanha",
                "grupo_politico",
                "relacao_davi",
                "score_articulacao",
                "prioridade_final",
            ]
        ]
        .head(20)
        .to_string(index=False)
    )

    print("\nAgenda prioritária:")
    print(
        agenda.head(20).to_string(index=False)
    )


def main() -> None:
    print("Iniciando ETL 010 — Enriquecimento Político")

    inteligencia = preparar_inteligencia(carregar_csv(INPUT_INTELIGENCIA))
    classificacao = preparar_classificacao(carregar_csv(INPUT_CLASSIFICACAO))

    df_final = enriquecer(inteligencia, classificacao)
    agenda = gerar_agenda_prioritaria(df_final)

    validar(df_final, agenda)
    salvar(df_final, agenda)

    print("\nArquivos gerados:")
    print(OUTPUT_CSV)
    print(OUTPUT_XLSX)
    print(OUTPUT_PRIORITARIOS)

    print("\nETL 010 concluído com sucesso.")


if __name__ == "__main__":
    main()