from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[2]

INPUT_FILE = (
    BASE_DIR
    / "data"
    / "final"
    / "inteligencia_vereadores_alagoas_2024.csv"
)

OUTPUT_FILE = (
    BASE_DIR
    / "data"
    / "final"
    / "inteligencia_municipal_vereadores.csv"
)


def classificar_potencial(votos):
    if votos >= 30000:
        return "Muito Alto"

    if votos >= 15000:
        return "Alto"

    if votos >= 7000:
        return "Médio"

    return "Baixo"


def gerar_base():

    print("Carregando inteligência de vereadores...")

    df = pd.read_csv(INPUT_FILE)

    df["votos"] = pd.to_numeric(
        df["votos"],
        errors="coerce"
    ).fillna(0)

    df["indice_influencia_vereador"] = pd.to_numeric(
        df["indice_influencia_vereador"],
        errors="coerce"
    ).fillna(0)

    municipios = []

    for municipio, grupo in df.groupby("municipio"):

        grupo = grupo.sort_values(
            "votos",
            ascending=False
        )

        principal_lideranca = grupo.iloc[0]

        total_votos_vereadores = int(
            grupo["votos"].sum()
        )

        media_votos = int(
            grupo["votos"].mean()
        )

        vereadores_eleitos = int(
            len(grupo)
        )

        potencial_transferencia_conservador = int(
            grupo["potencial_transferencia_conservador_20pct"].sum()
        )

        potencial_transferencia_moderado = int(
            grupo["potencial_transferencia_moderado_35pct"].sum()
        )

        potencial_transferencia_alto = int(
            grupo["potencial_transferencia_alto_50pct"].sum()
        )

        indice_influencia_municipal = round(
            grupo["indice_influencia_vereador"].mean(),
            2
        )

        municipios.append({
            "municipio": municipio,

            "vereadores_eleitos": vereadores_eleitos,

            "total_votos_vereadores":
                total_votos_vereadores,

            "media_votos_vereador":
                media_votos,

            "principal_lideranca":
                principal_lideranca["nome_urna"],

            "principal_lideranca_partido":
                principal_lideranca["partido"],

            "principal_lideranca_votos":
                principal_lideranca["votos"],

            "potencial_transferencia_conservador":
                potencial_transferencia_conservador,

            "potencial_transferencia_moderado":
                potencial_transferencia_moderado,

            "potencial_transferencia_alto":
                potencial_transferencia_alto,

            "indice_influencia_municipal":
                indice_influencia_municipal,

            "potencial_politico_municipio":
                classificar_potencial(
                    total_votos_vereadores
                )
        })

    df_saida = pd.DataFrame(municipios)

    df_saida = df_saida.sort_values(
        "total_votos_vereadores",
        ascending=False
    )

    df_saida.insert(
        0,
        "rank_municipal",
        range(
            1,
            len(df_saida) + 1
        )
    )

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    df_saida.to_csv(
        OUTPUT_FILE,
        index=False,
        encoding="utf-8-sig"
    )

    print("\nArquivo gerado:")
    print(OUTPUT_FILE)

    print("\nTOP 20 MUNICÍPIOS POR FORÇA DE VEREADORES\n")

    print(
        df_saida[
            [
                "rank_municipal",
                "municipio",
                "vereadores_eleitos",
                "total_votos_vereadores",
                "principal_lideranca",
                "potencial_politico_municipio"
            ]
        ].head(20)
    )

    print("\nResumo")

    print(
        f"Municípios: {len(df_saida)}"
    )

    print(
        f"Total de vereadores: "
        f"{df_saida['vereadores_eleitos'].sum()}"
    )

    print(
        f"Maior base municipal: "
        f"{df_saida.iloc[0]['municipio']}"
    )

    print(
        "\nProcessamento concluído."
    )


if __name__ == "__main__":
    gerar_base()