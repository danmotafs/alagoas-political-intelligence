from pathlib import Path

import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[2]
FINAL_DIR = BASE_DIR / "data" / "final"

ENTRADA = FINAL_DIR / "redutos_vereadores_top10.csv"

SAIDA_REDUTOS_QUALIFICADOS = FINAL_DIR / "redutos_qualificados_top10.csv"
SAIDA_AGENDA = FINAL_DIR / "agenda_territorial_davi_maia.csv"


MIN_VOTOS_TOTAL_VEREADOR = 300
MIN_VOTOS_LOCAL = 20
MIN_PERCENTUAL_LOCAL = 10


def ler_csv(caminho):
    for encoding in ["utf-8-sig", "latin1"]:
        for sep in [";", ","]:
            try:
                df = pd.read_csv(
                    caminho,
                    sep=sep,
                    encoding=encoding,
                    dtype=str,
                    low_memory=False,
                )
                if len(df.columns) > 1:
                    return df
            except Exception:
                pass

    raise ValueError(f"Não foi possível ler o CSV: {caminho}")


def preparar_base(df):
    colunas_texto = [
        "municipio",
        "vereador",
        "partido",
        "local_principal",
        "endereco_local_principal",
        "latitude",
        "longitude",
        "bairro",
        "distrito",
        "status_geocodificacao",
        "classificacao_reduto",
    ]

    for col in colunas_texto:
        if col not in df.columns:
            df[col] = ""
        df[col] = df[col].fillna("").astype(str)

    colunas_numericas = [
        "ranking_reduto_geral",
        "votos_local_principal",
        "votos_totais_vereador",
        "percentual_local_principal",
        "qtd_secoes_controladas",
        "total_secoes_vereador",
        "indice_reduto",
    ]

    for col in colunas_numericas:
        if col not in df.columns:
            df[col] = 0

        df[col] = (
            df[col]
            .astype(str)
            .str.replace(".", "", regex=False)
            .str.replace(",", ".", regex=False)
        )
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    return df


def classificar_nivel_reduto(row):
    votos_local = row["votos_local_principal"]
    percentual = row["percentual_local_principal"]

    if votos_local >= 100 and percentual >= 20:
        return "REDUTO ESTRATÉGICO"

    if votos_local >= 50 and percentual >= 15:
        return "REDUTO FORTE"

    if votos_local >= 20 and percentual >= 10:
        return "REDUTO RELEVANTE"

    return "NÃO QUALIFICADO"


def potencial_transferencia(nivel_reduto):
    if nivel_reduto == "REDUTO ESTRATÉGICO":
        return "ALTO"

    if nivel_reduto == "REDUTO FORTE":
        return "MÉDIO"

    if nivel_reduto == "REDUTO RELEVANTE":
        return "BAIXO"

    return "NÃO QUALIFICADO"


def prioridade_agenda(nivel_reduto):
    if nivel_reduto == "REDUTO ESTRATÉGICO":
        return "AGENDA IMEDIATA"

    if nivel_reduto == "REDUTO FORTE":
        return "CURTO PRAZO"

    if nivel_reduto == "REDUTO RELEVANTE":
        return "MÉDIO PRAZO"

    return "SEM PRIORIDADE"


def gerar_observacao(row):
    return (
        f"{row['vereador']} concentra {row['percentual_local_principal']:.2f}% "
        f"dos seus votos no local {row['local_principal']}, "
        f"com {int(row['votos_local_principal'])} votos registrados."
    )


def main():
    print("=" * 70)
    print("ETL 019 — REDUTOS QUALIFICADOS DOS VEREADORES")
    print("=" * 70)

    if not ENTRADA.exists():
        raise FileNotFoundError(
            f"Arquivo de entrada não encontrado: {ENTRADA}\n"
            "Execute antes o ETL 018."
        )

    print(f"\nLendo entrada: {ENTRADA}")
    df = ler_csv(ENTRADA)
    df = preparar_base(df)

    print(f"Redutos originais: {len(df):,}".replace(",", "."))

    df["status_reduto"] = "NÃO QUALIFICADO"

    mascara_base = (
        (df["votos_totais_vereador"] >= MIN_VOTOS_TOTAL_VEREADOR)
        & (df["votos_local_principal"] >= MIN_VOTOS_LOCAL)
        & (df["percentual_local_principal"] >= MIN_PERCENTUAL_LOCAL)
    )

    df.loc[mascara_base, "status_reduto"] = "QUALIFICADO"

    df["nivel_reduto"] = df.apply(classificar_nivel_reduto, axis=1)

    df.loc[df["status_reduto"] != "QUALIFICADO", "nivel_reduto"] = "NÃO QUALIFICADO"

    df["potencial_transferencia"] = df["nivel_reduto"].apply(potencial_transferencia)
    df["prioridade_agenda"] = df["nivel_reduto"].apply(prioridade_agenda)

    qualificados = df[df["status_reduto"] == "QUALIFICADO"].copy()

    ordem_nivel = {
        "REDUTO ESTRATÉGICO": 1,
        "REDUTO FORTE": 2,
        "REDUTO RELEVANTE": 3,
    }

    qualificados["ordem_nivel"] = qualificados["nivel_reduto"].map(ordem_nivel).fillna(99)

    qualificados = qualificados.sort_values(
        [
            "ordem_nivel",
            "votos_local_principal",
            "percentual_local_principal",
            "indice_reduto",
        ],
        ascending=[True, False, False, False],
    )

    qualificados["ranking_reduto_qualificado"] = range(1, len(qualificados) + 1)

    qualificados["observacao_estrategica"] = qualificados.apply(
        gerar_observacao,
        axis=1,
    )

    colunas_redutos = [
        "ranking_reduto_qualificado",
        "municipio",
        "vereador",
        "partido",
        "local_principal",
        "endereco_local_principal",
        "latitude",
        "longitude",
        "bairro",
        "distrito",
        "status_geocodificacao",
        "votos_local_principal",
        "votos_totais_vereador",
        "percentual_local_principal",
        "qtd_secoes_controladas",
        "total_secoes_vereador",
        "indice_reduto",
        "classificacao_reduto",
        "status_reduto",
        "nivel_reduto",
        "potencial_transferencia",
        "prioridade_agenda",
        "observacao_estrategica",
    ]

    qualificados[colunas_redutos].to_csv(
        SAIDA_REDUTOS_QUALIFICADOS,
        sep=";",
        index=False,
        encoding="utf-8-sig",
    )

    agenda = qualificados[
        [
            "ranking_reduto_qualificado",
            "municipio",
            "vereador",
            "partido",
            "local_principal",
            "bairro",
            "distrito",
            "endereco_local_principal",
            "latitude",
            "longitude",
            "votos_local_principal",
            "votos_totais_vereador",
            "percentual_local_principal",
            "nivel_reduto",
            "prioridade_agenda",
            "potencial_transferencia",
            "observacao_estrategica",
        ]
    ].copy()

    agenda = agenda.rename(
        columns={
            "local_principal": "local_prioritario",
            "endereco_local_principal": "endereco_local_prioritario",
        }
    )

    agenda.to_csv(
        SAIDA_AGENDA,
        sep=";",
        index=False,
        encoding="utf-8-sig",
    )

    print("\n" + "=" * 70)
    print("ETL 019 CONCLUÍDO COM SUCESSO")
    print("=" * 70)
    print(f"Redutos originais: {len(df):,}".replace(",", "."))
    print(f"Redutos qualificados: {len(qualificados):,}".replace(",", "."))
    print(f"Arquivo gerado: {SAIDA_REDUTOS_QUALIFICADOS}")
    print(f"Arquivo gerado: {SAIDA_AGENDA}")

    print("\nDistribuição por nível de reduto:")
    print(qualificados["nivel_reduto"].value_counts().to_string())

    print("\nDistribuição por prioridade de agenda:")
    print(qualificados["prioridade_agenda"].value_counts().to_string())

    print("\nTop 20 redutos qualificados:")
    top20 = qualificados.head(20)[
        [
            "ranking_reduto_qualificado",
            "municipio",
            "vereador",
            "local_principal",
            "votos_local_principal",
            "votos_totais_vereador",
            "percentual_local_principal",
            "nivel_reduto",
            "prioridade_agenda",
        ]
    ]

    print(top20.to_string(index=False))


if __name__ == "__main__":
    main()