from pathlib import Path

import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[2]

INPUT_PATH = BASE_DIR / "data" / "final" / "alagoas_municipios_base_2024.csv"

FINAL_DIR = BASE_DIR / "data" / "final"
REPORTS_DIR = BASE_DIR / "reports"

OUTPUT_CSV = FINAL_DIR / "ranking_estrategico_alagoas_2024.csv"
OUTPUT_XLSX = FINAL_DIR / "ranking_estrategico_alagoas_2024.xlsx"
OUTPUT_TOP20_CSV = FINAL_DIR / "top20_municipios_prioritarios_alagoas_2024.csv"
OUTPUT_MD = REPORTS_DIR / "ranking_estrategico_alagoas_2024.md"


def carregar_base() -> pd.DataFrame:
    if not INPUT_PATH.exists():
        raise FileNotFoundError(f"Base consolidada não encontrada: {INPUT_PATH}")

    return pd.read_csv(INPUT_PATH)


def classificar_prioridade(rank: int) -> str:
    if rank <= 10:
        return "Prioridade Máxima"
    if rank <= 20:
        return "Alta Prioridade"
    if rank <= 40:
        return "Média Prioridade"
    return "Baixa Prioridade"


def preparar_ranking(df: pd.DataFrame) -> pd.DataFrame:
    colunas_obrigatorias = {
        "municipio",
        "populacao_estimada_2024",
        "eleitorado_2024",
        "taxa_eleitorado",
        "participacao_populacao",
        "participacao_eleitorado",
        "indice_estrategico_inicial",
    }

    faltantes = colunas_obrigatorias - set(df.columns)
    if faltantes:
        raise KeyError(f"Colunas obrigatórias ausentes: {faltantes}")

    ranking = df.copy()

    ranking = ranking.sort_values(
        by="indice_estrategico_inicial",
        ascending=False,
    ).reset_index(drop=True)

    ranking["rank"] = ranking.index + 1
    ranking["prioridade_politica"] = ranking["rank"].apply(classificar_prioridade)

    ranking["taxa_eleitorado_pct"] = ranking["taxa_eleitorado"] * 100
    ranking["participacao_populacao_pct"] = ranking["participacao_populacao"] * 100
    ranking["participacao_eleitorado_pct"] = ranking["participacao_eleitorado"] * 100
    ranking["indice_estrategico_pct"] = ranking["indice_estrategico_inicial"] * 100

    ranking = ranking[
        [
            "rank",
            "municipio",
            "populacao_estimada_2024",
            "eleitorado_2024",
            "taxa_eleitorado",
            "taxa_eleitorado_pct",
            "participacao_populacao",
            "participacao_populacao_pct",
            "participacao_eleitorado",
            "participacao_eleitorado_pct",
            "indice_estrategico_inicial",
            "indice_estrategico_pct",
            "prioridade_politica",
        ]
    ]

    return ranking


def validar_ranking(df: pd.DataFrame) -> None:
    total_municipios = len(df)
    eleitorado_total = df["eleitorado_2024"].sum()
    populacao_total = df["populacao_estimada_2024"].sum()

    municipios = set(df["municipio"].str.upper())

    print("\nVALIDAÇÃO RANKING")
    print(f"Municípios no ranking: {total_municipios}")
    print(f"População total: {populacao_total:,.0f}".replace(",", "."))
    print(f"Eleitorado total: {eleitorado_total:,.0f}".replace(",", "."))
    print(f"Maceió presente: {'MACEIÓ' in municipios or 'MACEIO' in municipios}")
    print(f"Arapiraca presente: {'ARAPIRACA' in municipios}")
    print(f"Quebrangulo presente: {'QUEBRANGULO' in municipios}")

    if total_municipios != 102:
        raise ValueError(f"Esperado: 102 municípios. Encontrado: {total_municipios}")

    if eleitorado_total <= 0:
        raise ValueError("Eleitorado total inválido.")

    if populacao_total <= 0:
        raise ValueError("População total inválida.")


def gerar_relatorio_markdown(df: pd.DataFrame) -> str:
    top10 = df.head(10)
    top20 = df.head(20)

    linhas_top10 = []
    for _, row in top10.iterrows():
        linhas_top10.append(
            f"| {int(row['rank'])} | {row['municipio']} | "
            f"{int(row['eleitorado_2024']):,} | "
            f"{row['participacao_eleitorado_pct']:.2f}% | "
            f"{row['indice_estrategico_pct']:.2f}% |"
        )

    linhas_top20 = []
    for _, row in top20.iterrows():
        linhas_top20.append(
            f"| {int(row['rank'])} | {row['municipio']} | "
            f"{int(row['populacao_estimada_2024']):,} | "
            f"{int(row['eleitorado_2024']):,} | "
            f"{row['prioridade_politica']} |"
        )

    relatorio = f"""
# Ranking Estratégico dos Municípios de Alagoas - 2024

## Objetivo

Este relatório apresenta um ranking inicial de relevância territorial e eleitoral dos 102 municípios de Alagoas, com base em população estimada e eleitorado municipal.

## Metodologia

O índice estratégico inicial foi calculado com a seguinte fórmula:

Índice Estratégico Inicial = 0,70 x Participação no Eleitorado Estadual + 0,30 x Participação na População Estadual

A ponderação prioriza o peso eleitoral municipal sem desconsiderar a relevância populacional.

## Classificação de Prioridade Política

- Top 10 = Prioridade Máxima
- Top 20 = Alta Prioridade
- Top 40 = Média Prioridade
- Demais = Baixa Prioridade

## Top 10 Municípios Estratégicos

| Rank | Município | Eleitorado 2024 | Participação Eleitoral | Índice Estratégico |
|---:|---|---:|---:|---:|
{chr(10).join(linhas_top10)}

## Top 20 Municípios Prioritários

| Rank | Município | População 2024 | Eleitorado 2024 | Prioridade |
|---:|---|---:|---:|---|
{chr(10).join(linhas_top20)}

## Leitura Estratégica Inicial

O ranking permite identificar os municípios com maior peso político-eleitoral no estado de Alagoas.

Para uma estratégia de expansão política 2026-2028, os municípios de maior prioridade devem ser analisados em conjunto com:

- presença política local;
- histórico eleitoral;
- alianças municipais;
- distância e conexão territorial com Quebrangulo;
- influência regional;
- potencial de agenda pública;
- aderência ao grupo político atual.

## Arquivos Gerados

- data/final/ranking_estrategico_alagoas_2024.csv
- data/final/ranking_estrategico_alagoas_2024.xlsx
- data/final/top20_municipios_prioritarios_alagoas_2024.csv
"""

    return relatorio


def salvar_resultados(df: pd.DataFrame) -> None:
    FINAL_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    df.to_csv(OUTPUT_CSV, index=False, encoding="utf-8-sig")
    df.to_excel(OUTPUT_XLSX, index=False)

    top20 = df.head(20)
    top20.to_csv(OUTPUT_TOP20_CSV, index=False, encoding="utf-8-sig")

    relatorio = gerar_relatorio_markdown(df)
    OUTPUT_MD.write_text(relatorio, encoding="utf-8")

    print("\nArquivos gerados:")
    print(OUTPUT_CSV)
    print(OUTPUT_XLSX)
    print(OUTPUT_TOP20_CSV)
    print(OUTPUT_MD)


def main() -> None:
    print("Iniciando ETL 004 — Ranking Estratégico Inicial")

    df_base = carregar_base()
    df_ranking = preparar_ranking(df_base)

    validar_ranking(df_ranking)
    salvar_resultados(df_ranking)

    print("\nTop 20 municípios prioritários:")
    print(
        df_ranking[
            [
                "rank",
                "municipio",
                "populacao_estimada_2024",
                "eleitorado_2024",
                "participacao_eleitorado_pct",
                "indice_estrategico_pct",
                "prioridade_politica",
            ]
        ]
        .head(20)
        .to_string(index=False)
    )

    print("\nETL 004 concluído com sucesso.")


if __name__ == "__main__":
    main()