import pandas as pd
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[2]

INPUT_FILE = BASE_DIR / "data" / "reference" / "rede_poder_top30_enriquecida.csv"
OUTPUT_FILE = BASE_DIR / "data" / "reference" / "rede_poder_top30_classificada.csv"


CAMPOS_CLASSIFICACAO = [
    "grupo_politico",
    "relacao_davi",
    "peso_politico",
    "status_articulacao",
    "observacoes",
]


def main():
    print("CRIANDO REDE DE PODER TOP 30 CLASSIFICADA")
    print("=" * 60)

    if not INPUT_FILE.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {INPUT_FILE}")

    df = pd.read_csv(INPUT_FILE, encoding="utf-8-sig")

    print(f"Arquivo de entrada: {INPUT_FILE}")
    print(f"Registros carregados: {len(df)}")
    print()

    for campo in CAMPOS_CLASSIFICACAO:
        if campo not in df.columns:
            df[campo] = ""

    colunas_saida = [
        "rank_top30",
        "rank_estrategico",
        "municipio",
        "prefeito",
        "partido",
        "votos_prefeito",
        "percentual_prefeito",
        "segundo_colocado",
        "partido_segundo_colocado",
        "votos_segundo_colocado",
        "percentual_segundo_colocado",
        "margem_vitoria_votos",
        "margem_vitoria_pct",
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

    colunas_existentes = [col for col in colunas_saida if col in df.columns]
    df = df[colunas_existentes]

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")

    print("Arquivo gerado com sucesso:")
    print(OUTPUT_FILE)
    print()
    print(f"Total de municípios exportados: {len(df)}")
    print()
    print("Campos preparados para classificação política:")
    for campo in CAMPOS_CLASSIFICACAO:
        print(f"- {campo}")

    print()
    print("AMOSTRA:")
    print(
        df[
            [
                "rank_top30",
                "municipio",
                "prefeito",
                "partido",
                "votos_prefeito",
                "segundo_colocado",
                "margem_vitoria_votos",
                "margem_vitoria_pct",
                "grupo_politico",
                "relacao_davi",
                "peso_politico",
                "status_articulacao",
            ]
        ].head(10).to_string(index=False)
    )


if __name__ == "__main__":
    main()