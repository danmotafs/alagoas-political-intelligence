import re
import unicodedata
from pathlib import Path

import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[2]
FINAL_DIR = BASE_DIR / "data" / "final"

ENTRADA = FINAL_DIR / "mapa_influencia_geografico.csv"

SAIDA_POLOS = FINAL_DIR / "polos_eleitorais_top10.csv"
SAIDA_REDUTOS = FINAL_DIR / "redutos_vereadores_top10.csv"


def ler_csv(caminho):
    for encoding in ["utf-8-sig", "latin1"]:
        for sep in [";", ","]:
            try:
                df = pd.read_csv(caminho, sep=sep, encoding=encoding, dtype=str, low_memory=False)
                if len(df.columns) > 1:
                    return df
            except Exception:
                pass
    raise ValueError(f"Não foi possível ler: {caminho}")


def preparar_mapa(mapa):
    colunas_texto = [
        "municipio", "vereador", "partido", "zona", "secao",
        "local_votacao", "endereco_local_votacao",
        "latitude", "longitude", "bairro", "distrito",
        "status_geocodificacao",
    ]

    for col in colunas_texto:
        if col not in mapa.columns:
            mapa[col] = ""
        mapa[col] = mapa[col].fillna("").astype(str)

    mapa["votos"] = pd.to_numeric(mapa["votos"], errors="coerce").fillna(0).astype(int)

    if "percentual" in mapa.columns:
        mapa["percentual"] = pd.to_numeric(mapa["percentual"], errors="coerce").fillna(0)
    else:
        mapa["percentual"] = 0

    return mapa


def classificar_local(indice, p90, p70):
    if indice >= p90:
        return "PRIORIDADE MÁXIMA"
    if indice >= p70:
        return "PRIORIDADE ALTA"
    return "PRIORIDADE NORMAL"


def classificar_agenda(classificacao, qtd_vereadores, votos_totais):
    if classificacao == "PRIORIDADE MÁXIMA":
        return "AGENDA IMEDIATA"
    if classificacao == "PRIORIDADE ALTA" and qtd_vereadores >= 15:
        return "AGENDA PRIORITÁRIA"
    if votos_totais >= 1000 and qtd_vereadores >= 10:
        return "AGENDA RECOMENDADA"
    return "MONITORAMENTO"


def calcular_polos(mapa):
    local_cols = [
        "municipio",
        "local_votacao",
        "endereco_local_votacao",
        "latitude",
        "longitude",
        "bairro",
        "distrito",
        "status_geocodificacao",
    ]

    polos = (
        mapa.groupby(local_cols, as_index=False, dropna=False)
        .agg(
            qtd_secoes=("secao", "nunique"),
            qtd_vereadores=("vereador", "nunique"),
            votos_totais=("votos", "sum"),
        )
    )

    lideres = (
        mapa.groupby(
            ["municipio", "local_votacao", "endereco_local_votacao", "vereador", "partido"],
            as_index=False,
            dropna=False,
        )
        .agg(votos_vereador_local=("votos", "sum"))
    )

    lideres = lideres.sort_values(
        ["municipio", "local_votacao", "endereco_local_votacao", "votos_vereador_local"],
        ascending=[True, True, True, False],
    )

    lideres["ranking_lider_local"] = (
        lideres.groupby(["municipio", "local_votacao", "endereco_local_votacao"], dropna=False)[
            "votos_vereador_local"
        ]
        .rank(method="first", ascending=False)
        .astype(int)
    )

    lideres_top1 = lideres[lideres["ranking_lider_local"] == 1].copy()

    polos = polos.merge(
        lideres_top1[
            [
                "municipio",
                "local_votacao",
                "endereco_local_votacao",
                "vereador",
                "partido",
                "votos_vereador_local",
            ]
        ],
        how="left",
        on=["municipio", "local_votacao", "endereco_local_votacao"],
    )

    polos = polos.rename(
        columns={
            "vereador": "vereador_principal",
            "partido": "partido_vereador_principal",
            "votos_vereador_local": "votos_vereador_principal",
        }
    )

    polos["votos_vereador_principal"] = pd.to_numeric(
        polos["votos_vereador_principal"], errors="coerce"
    ).fillna(0).astype(int)

    polos["percentual_dominancia"] = (
        polos["votos_vereador_principal"] / polos["votos_totais"] * 100
    ).round(2)

    max_votos = max(polos["votos_totais"].max(), 1)
    max_vereadores = max(polos["qtd_vereadores"].max(), 1)
    max_secoes = max(polos["qtd_secoes"].max(), 1)

    polos["indice_influencia_local"] = (
        (polos["votos_totais"] / max_votos * 100) * 0.50
        + (polos["qtd_vereadores"] / max_vereadores * 100) * 0.30
        + (polos["qtd_secoes"] / max_secoes * 100) * 0.20
    ).round(2)

    p90 = polos["indice_influencia_local"].quantile(0.90)
    p70 = polos["indice_influencia_local"].quantile(0.70)

    polos["classificacao_local"] = polos["indice_influencia_local"].apply(
        lambda x: classificar_local(x, p90, p70)
    )

    polos["potencial_agenda_davi"] = [
        classificar_agenda(c, int(qv), int(vt))
        for c, qv, vt in zip(
            polos["classificacao_local"],
            polos["qtd_vereadores"],
            polos["votos_totais"],
        )
    ]

    polos["ranking_polo_municipal"] = (
        polos.groupby("municipio", dropna=False)["indice_influencia_local"]
        .rank(method="first", ascending=False)
        .astype(int)
    )

    polos["ranking_polo_geral"] = (
        polos["indice_influencia_local"]
        .rank(method="first", ascending=False)
        .astype(int)
    )

    polos = polos.sort_values("ranking_polo_geral")

    return polos[
        [
            "municipio",
            "ranking_polo_municipal",
            "ranking_polo_geral",
            "local_votacao",
            "endereco_local_votacao",
            "latitude",
            "longitude",
            "bairro",
            "distrito",
            "status_geocodificacao",
            "qtd_secoes",
            "qtd_vereadores",
            "votos_totais",
            "vereador_principal",
            "partido_vereador_principal",
            "votos_vereador_principal",
            "percentual_dominancia",
            "indice_influencia_local",
            "classificacao_local",
            "potencial_agenda_davi",
        ]
    ]


def calcular_redutos(mapa):
    redutos_local = (
        mapa.groupby(
            [
                "municipio",
                "vereador",
                "partido",
                "local_votacao",
                "endereco_local_votacao",
                "latitude",
                "longitude",
                "bairro",
                "distrito",
                "status_geocodificacao",
            ],
            as_index=False,
            dropna=False,
        )
        .agg(
            votos_local=("votos", "sum"),
            qtd_secoes_local=("secao", "nunique"),
        )
    )

    total_vereador = (
        mapa.groupby(["municipio", "vereador"], as_index=False, dropna=False)
        .agg(
            votos_totais_vereador=("votos", "sum"),
            total_secoes_vereador=("secao", "nunique"),
        )
    )

    redutos_local = redutos_local.merge(
        total_vereador,
        how="left",
        on=["municipio", "vereador"],
    )

    redutos_local["percentual_local_principal"] = (
        redutos_local["votos_local"] / redutos_local["votos_totais_vereador"] * 100
    ).round(2)

    redutos_local["ranking_reduto_vereador"] = (
        redutos_local.groupby(["municipio", "vereador"], dropna=False)["votos_local"]
        .rank(method="first", ascending=False)
        .astype(int)
    )

    redutos = redutos_local[redutos_local["ranking_reduto_vereador"] == 1].copy()

    max_secoes = max(redutos["qtd_secoes_local"].max(), 1)
    max_votos = max(redutos["votos_local"].max(), 1)

    redutos["indice_reduto"] = (
        redutos["percentual_local_principal"] * 0.60
        + (redutos["qtd_secoes_local"] / max_secoes * 100) * 0.20
        + (redutos["votos_local"] / max_votos * 100) * 0.20
    ).round(2)

    redutos["classificacao_reduto"] = pd.cut(
        redutos["indice_reduto"],
        bins=[-1, 30, 60, 100],
        labels=["REDUTO BAIXO", "REDUTO MÉDIO", "REDUTO FORTE"],
    ).astype(str)

    redutos["ranking_reduto_geral"] = (
        redutos["indice_reduto"]
        .rank(method="first", ascending=False)
        .astype(int)
    )

    redutos = redutos.sort_values("ranking_reduto_geral")

    redutos = redutos.rename(
        columns={
            "local_votacao": "local_principal",
            "endereco_local_votacao": "endereco_local_principal",
            "votos_local": "votos_local_principal",
            "qtd_secoes_local": "qtd_secoes_controladas",
        }
    )

    return redutos[
        [
            "municipio",
            "vereador",
            "partido",
            "ranking_reduto_geral",
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
        ]
    ]


def main():
    print("=" * 70)
    print("ETL 018 — CONSOLIDAÇÃO TERRITORIAL POR LOCAL DE VOTAÇÃO")
    print("=" * 70)

    if not ENTRADA.exists():
        raise FileNotFoundError(f"Arquivo de entrada não encontrado: {ENTRADA}")

    print(f"\nLendo entrada: {ENTRADA}")
    mapa = ler_csv(ENTRADA)
    mapa = preparar_mapa(mapa)

    print(f"Linhas carregadas: {len(mapa):,}".replace(",", "."))
    print(f"Municípios: {mapa['municipio'].nunique()}")
    print(f"Vereadores: {mapa['vereador'].nunique()}")
    print(f"Locais de votação: {mapa['local_votacao'].nunique()}")

    print("\nCalculando polos eleitorais...")
    polos = calcular_polos(mapa)

    polos.to_csv(SAIDA_POLOS, sep=";", index=False, encoding="utf-8-sig")

    print(f"Arquivo gerado: {SAIDA_POLOS}")
    print(f"Polos eleitorais: {len(polos):,}".replace(",", "."))

    print("\nCalculando redutos principais dos vereadores...")
    redutos = calcular_redutos(mapa)

    redutos.to_csv(SAIDA_REDUTOS, sep=";", index=False, encoding="utf-8-sig")

    print(f"Arquivo gerado: {SAIDA_REDUTOS}")
    print(f"Redutos de vereadores: {len(redutos):,}".replace(",", "."))

    print("\n" + "=" * 70)
    print("ETL 018 CONCLUÍDO COM SUCESSO")
    print("=" * 70)

    print("\nTop 15 polos eleitorais gerais:")
    print(
        polos.head(15)[
            [
                "ranking_polo_geral",
                "municipio",
                "local_votacao",
                "votos_totais",
                "qtd_vereadores",
                "qtd_secoes",
                "indice_influencia_local",
                "classificacao_local",
                "potencial_agenda_davi",
            ]
        ].to_string(index=False)
    )

    print("\nTop 15 redutos de vereadores:")
    print(
        redutos.head(15)[
            [
                "ranking_reduto_geral",
                "municipio",
                "vereador",
                "local_principal",
                "votos_local_principal",
                "percentual_local_principal",
                "indice_reduto",
                "classificacao_reduto",
            ]
        ].to_string(index=False)
    )


if __name__ == "__main__":
    main()