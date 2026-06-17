import pandas as pd
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[2]

TOP30_FILE = BASE_DIR / "data" / "reference" / "top30_liderancas_estrategicas.csv"

POSSIVEIS_BASES_POLITICAS = [
    BASE_DIR / "data" / "processed" / "base_politica_municipal_2024.csv",
    BASE_DIR / "data" / "final" / "base_politica_municipal_2024.csv",
    BASE_DIR / "data" / "reference" / "base_politica_municipal_2024.csv",
    BASE_DIR / "data" / "raw" / "base_politica_municipal_2024.csv",
]

OUTPUT_FILE = BASE_DIR / "data" / "reference" / "rede_poder_top30_enriquecida.csv"


def localizar_base_politica():
    for caminho in POSSIVEIS_BASES_POLITICAS:
        if caminho.exists():
            return caminho
    return None


def normalizar_municipio(valor):
    if pd.isna(valor):
        return ""

    texto = str(valor).strip().upper()

    substituicoes = {
        "Á": "A", "À": "A", "Â": "A", "Ã": "A",
        "É": "E", "Ê": "E",
        "Í": "I",
        "Ó": "O", "Ô": "O", "Õ": "O",
        "Ú": "U",
        "Ç": "C",
    }

    for antigo, novo in substituicoes.items():
        texto = texto.replace(antigo, novo)

    return texto


def main():
    print("ENRIQUECENDO TOP 30 - REDE DE PODER MUNICIPAL")
    print("=" * 60)

    if not TOP30_FILE.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {TOP30_FILE}")

    base_politica_file = localizar_base_politica()

    if base_politica_file is None:
        raise FileNotFoundError(
            "Arquivo base_politica_municipal_2024.csv não encontrado.\n"
            "Locais verificados:\n"
            + "\n".join(str(path) for path in POSSIVEIS_BASES_POLITICAS)
        )

    print(f"Top 30: {TOP30_FILE}")
    print(f"Base política encontrada: {base_politica_file}")
    print()

    top30 = pd.read_csv(TOP30_FILE, encoding="utf-8-sig")
    politica = pd.read_csv(base_politica_file, encoding="utf-8-sig")

    top30["municipio_merge"] = top30["municipio"].apply(normalizar_municipio)
    politica["municipio_merge"] = politica["municipio"].apply(normalizar_municipio)

    print(f"Municípios no Top 30: {len(top30)}")
    print(f"Municípios na base política: {len(politica)}")
    print()

    colunas_base_politica = [
        "municipio_merge",
        "segundo_colocado",
        "partido_segundo_colocado",
        "votos_segundo_colocado",
        "percentual_segundo_colocado",
        "margem_vitoria_votos",
        "margem_vitoria_pct",
    ]

    colunas_faltantes = [
        col for col in colunas_base_politica if col not in politica.columns
    ]

    if colunas_faltantes:
        print("Colunas disponíveis na base política:")
        print(politica.columns.tolist())
        print()
        raise ValueError(
            "Colunas ausentes na base política municipal:\n"
            + "\n".join(colunas_faltantes)
        )

    rede = top30.merge(
        politica[colunas_base_politica],
        on="municipio_merge",
        how="left",
    )

    rede.drop(columns=["municipio_merge"], inplace=True)

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

    colunas_existentes = [col for col in colunas_saida if col in rede.columns]
    rede = rede[colunas_existentes]

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    rede.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")

    print("Arquivo gerado com sucesso:")
    print(OUTPUT_FILE)
    print()
    print(f"Total de municípios exportados: {len(rede)}")
    print()

    sem_segundo_colocado = rede[rede["segundo_colocado"].isna()]

    if len(sem_segundo_colocado) > 0:
        print("ATENÇÃO: municípios sem segundo colocado após o merge:")
        print(sem_segundo_colocado["municipio"].to_string(index=False))
    else:
        print("Merge validado: todos os municípios possuem segundo colocado.")

    print()
    print("AMOSTRA DA REDE DE PODER ENRIQUECIDA:")
    print(
        rede[
            [
                "rank_top30",
                "municipio",
                "prefeito",
                "partido",
                "votos_prefeito",
                "segundo_colocado",
                "votos_segundo_colocado",
                "margem_vitoria_votos",
                "margem_vitoria_pct",
            ]
        ].head(10).to_string(index=False)
    )


if __name__ == "__main__":
    main()