import pandas as pd
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[2]

INPUT_FILE = BASE_DIR / "data" / "reference" / "classificacao_politica_alagoas_v2.csv"
OUTPUT_FILE = BASE_DIR / "data" / "reference" / "top30_liderancas_estrategicas.csv"


def main():
    print("EXTRAINDO TOP 30 LIDERANÇAS ESTRATÉGICAS DE ALAGOAS")
    print("=" * 60)

    if not INPUT_FILE.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {INPUT_FILE}")

    df = pd.read_csv(INPUT_FILE, encoding="utf-8-sig")

    colunas_necessarias = [
        "rank_estrategico",
        "municipio",
        "prefeito",
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
        "status_classificacao",
    ]

    colunas_faltantes = [col for col in colunas_necessarias if col not in df.columns]

    if colunas_faltantes:
        raise ValueError(
            "Colunas ausentes no arquivo de entrada:\n"
            + "\n".join(colunas_faltantes)
        )

    df["rank_estrategico"] = pd.to_numeric(df["rank_estrategico"], errors="coerce")

    top30 = (
        df.sort_values("rank_estrategico", ascending=True)
        .head(30)
        .copy()
    )

    top30.insert(0, "rank_top30", range(1, len(top30) + 1))

    colunas_saida = [
        "rank_top30",
        "rank_estrategico",
        "municipio",
        "prefeito",
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
        "status_classificacao",
    ]

    top30 = top30[colunas_saida]

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    top30.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")

    print()
    print("Arquivo gerado com sucesso:")
    print(OUTPUT_FILE)
    print()
    print(f"Total de municípios exportados: {len(top30)}")
    print()
    print("TOP 30 MUNICÍPIOS ESTRATÉGICOS:")
    print(
        top30[
            [
                "rank_top30",
                "municipio",
                "prefeito",
                "partido",
                "eleitorado_2024",
                "visitado_pre_campanha",
                "grupo_politico",
                "relacao_davi",
            ]
        ].to_string(index=False)
    )


if __name__ == "__main__":
    main()