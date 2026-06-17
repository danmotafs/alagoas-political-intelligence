from pathlib import Path

import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[2]

INPUT_FILE = (
    BASE_DIR
    / "data"
    / "final"
    / "inteligencia_politica_territorial_2024_2026.csv"
)

OUTPUT_CSV = (
    BASE_DIR
    / "data"
    / "final"
    / "base_liderancas_alagoas_2024.csv"
)

OUTPUT_XLSX = (
    BASE_DIR
    / "data"
    / "final"
    / "base_liderancas_alagoas_2024.xlsx"
)


def carregar_base() -> pd.DataFrame:
    if not INPUT_FILE.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {INPUT_FILE}")

    return pd.read_csv(INPUT_FILE)


def gerar_base_liderancas(df: pd.DataFrame) -> pd.DataFrame:
    colunas_necessarias = [
        "rank",
        "municipio",
        "prefeito",
        "vice_prefeito",
        "partido",
        "numero",
        "votos_prefeito",
        "percentual_prefeito",
        "eleitorado_2024",
        "indice_estrategico_pct",
        "prioridade_politica",
        "visitado_pre_campanha",
        "quantidade_visitas",
        "ultima_visita",
    ]

    faltantes = [c for c in colunas_necessarias if c not in df.columns]

    if faltantes:
        raise KeyError(f"Colunas ausentes: {faltantes}")

    base = df[colunas_necessarias].copy()

    base = base.rename(
        columns={
            "rank": "rank_estrategico",
            "prefeito": "lideranca_principal",
            "partido": "partido_lideranca",
            "numero": "numero_partido",
            "votos_prefeito": "votos_lideranca",
            "percentual_prefeito": "percentual_lideranca",
        }
    )

    base["cargo_lideranca"] = "Prefeito"
    base["tipo_lideranca"] = "Executivo Municipal"

    base["grupo_politico"] = ""
    base["relacao_davi"] = ""

    base["classificacao_relacao"] = ""
    base["observacoes_politicas"] = ""

    base["prioridade_articulacao"] = base.apply(
        classificar_prioridade_articulacao,
        axis=1,
    )

    base["acao_recomendada"] = base.apply(
        gerar_acao_recomendada,
        axis=1,
    )

    colunas_finais = [
        "rank_estrategico",
        "municipio",
        "lideranca_principal",
        "cargo_lideranca",
        "tipo_lideranca",
        "vice_prefeito",
        "partido_lideranca",
        "numero_partido",
        "votos_lideranca",
        "percentual_lideranca",
        "eleitorado_2024",
        "indice_estrategico_pct",
        "prioridade_politica",
        "visitado_pre_campanha",
        "quantidade_visitas",
        "ultima_visita",
        "grupo_politico",
        "relacao_davi",
        "classificacao_relacao",
        "prioridade_articulacao",
        "acao_recomendada",
        "observacoes_politicas",
    ]

    return base[colunas_finais].sort_values("rank_estrategico")


def classificar_prioridade_articulacao(row) -> str:
    rank = int(row["rank_estrategico"])
    visitado = bool(row["visitado_pre_campanha"])

    if rank <= 20 and not visitado:
        return "Prioridade máxima para agenda"

    if rank <= 20 and visitado:
        return "Manter articulação ativa"

    if rank <= 40 and not visitado:
        return "Prioridade média para aproximação"

    if rank <= 40 and visitado:
        return "Consolidar presença regional"

    return "Monitoramento"


def gerar_acao_recomendada(row) -> str:
    rank = int(row["rank_estrategico"])
    municipio = row["municipio"]
    lideranca = row["lideranca_principal"]
    partido = row["partido_lideranca"]
    visitado = bool(row["visitado_pre_campanha"])

    if rank <= 20 and not visitado:
        return (
            f"Priorizar visita a {municipio} e mapear agenda com "
            f"{lideranca} ({partido})."
        )

    if rank <= 20 and visitado:
        return (
            f"Registrar articulação já iniciada em {municipio} e manter "
            f"contato político com {lideranca} ({partido})."
        )

    if rank <= 40 and not visitado:
        return (
            f"Incluir {municipio} em rodada regional de aproximação política."
        )

    if rank <= 40 and visitado:
        return (
            f"Acompanhar continuidade da presença política em {municipio}."
        )

    return "Monitorar oportunidade de articulação futura."


def salvar_base(base: pd.DataFrame) -> None:
    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)

    base.to_csv(
        OUTPUT_CSV,
        index=False,
        encoding="utf-8-sig",
    )

    base.to_excel(
        OUTPUT_XLSX,
        index=False,
    )


def validar(base: pd.DataFrame) -> None:
    print("\nVALIDAÇÃO BASE DE LIDERANÇAS")
    print(f"Registros: {len(base)}")
    print(f"Municípios únicos: {base['municipio'].nunique()}")
    print(f"Lideranças com nome: {base['lideranca_principal'].notna().sum()}")

    print("\nTop 20 lideranças estratégicas:")
    print(
        base[
            [
                "rank_estrategico",
                "municipio",
                "lideranca_principal",
                "partido_lideranca",
                "votos_lideranca",
                "visitado_pre_campanha",
                "prioridade_articulacao",
            ]
        ]
        .head(20)
        .to_string(index=False)
    )


def main() -> None:
    print("Gerando base_liderancas_alagoas_2024.csv")

    df = carregar_base()
    base = gerar_base_liderancas(df)

    validar(base)
    salvar_base(base)

    print("\nArquivos gerados:")
    print(OUTPUT_CSV)
    print(OUTPUT_XLSX)

    print("\nBase de lideranças concluída.")


if __name__ == "__main__":
    main()