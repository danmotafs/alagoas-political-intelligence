import re
import unicodedata
from pathlib import Path

import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[2]

RAW_DIR = BASE_DIR / "data" / "raw"
TSE_DIR = RAW_DIR / "tse_2024"
FINAL_DIR = BASE_DIR / "data" / "final"

FINAL_DIR.mkdir(parents=True, exist_ok=True)

ARQUIVO_VOTACAO_SECAO = TSE_DIR / "votacao_secao_2024_AL.csv"

SAIDA_VOTACAO_SECAO = FINAL_DIR / "votacao_secao_vereadores_top10.csv"
SAIDA_MAPA_INFLUENCIA = FINAL_DIR / "mapa_influencia_vereadores_top10.csv"


TOP10_FALLBACK = [
    "MACEIO",
    "ARAPIRACA",
    "RIO LARGO",
    "PALMEIRA DOS INDIOS",
    "UNIAO DOS PALMARES",
    "MARECHAL DEODORO",
    "PENEDO",
    "SAO MIGUEL DOS CAMPOS",
    "CORURIPE",
    "DELMIRO GOUVEIA",
]


def normalizar_texto(valor):
    if pd.isna(valor):
        return ""
    texto = str(valor).strip().upper()
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    texto = re.sub(r"\s+", " ", texto)
    return texto


def localizar_arquivo(nome_arquivo):
    caminhos = [
        BASE_DIR / nome_arquivo,
        RAW_DIR / nome_arquivo,
        TSE_DIR / nome_arquivo,
        BASE_DIR / "data" / "processed" / nome_arquivo,
        BASE_DIR / "data" / "final" / nome_arquivo,
        BASE_DIR / "data" / "reference" / nome_arquivo,
    ]

    for caminho in caminhos:
        if caminho.exists():
            return caminho

    encontrados = list(BASE_DIR.rglob(nome_arquivo))
    return encontrados[0] if encontrados else None


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
                continue

    raise ValueError(f"Não foi possível ler o CSV corretamente: {caminho}")


def detectar_coluna(df, opcoes):
    mapa = {normalizar_texto(col): col for col in df.columns}

    for opcao in opcoes:
        chave = normalizar_texto(opcao)
        if chave in mapa:
            return mapa[chave]

    for col in df.columns:
        col_norm = normalizar_texto(col)
        for opcao in opcoes:
            if normalizar_texto(opcao) in col_norm:
                return col

    return None


def carregar_top10_municipios():
    arquivo = localizar_arquivo("ranking_estrategico_alagoas_2024.csv")

    if arquivo is None:
        print("AVISO: ranking_estrategico_alagoas_2024.csv não encontrado.")
        print("Usando lista TOP10_FALLBACK.")
        return [normalizar_texto(m) for m in TOP10_FALLBACK]

    ranking = ler_csv(arquivo)

    col_municipio = detectar_coluna(
        ranking,
        ["municipio", "município", "nm_municipio"],
    )

    if col_municipio is None:
        print("AVISO: coluna de município não encontrada no ranking.")
        print("Colunas encontradas:", list(ranking.columns))
        print("Usando lista TOP10_FALLBACK.")
        return [normalizar_texto(m) for m in TOP10_FALLBACK]

    col_score = detectar_coluna(
        ranking,
        [
            "ranking_estrategico",
            "pontuacao_estrategica",
            "score_estrategico",
            "indice_estrategico",
            "pontuacao",
            "score",
        ],
    )

    ranking["municipio_norm"] = ranking[col_municipio].apply(normalizar_texto)

    if col_score:
        ranking["_score"] = (
            ranking[col_score]
            .astype(str)
            .str.replace(".", "", regex=False)
            .str.replace(",", ".", regex=False)
        )
        ranking["_score"] = pd.to_numeric(ranking["_score"], errors="coerce").fillna(0)
        ranking = ranking.sort_values("_score", ascending=False)

    top10 = ranking["municipio_norm"].dropna().drop_duplicates().head(10).tolist()

    if len(top10) < 10:
        top10 = [normalizar_texto(m) for m in TOP10_FALLBACK]

    print("\nTOP 10 MUNICÍPIOS ESTRATÉGICOS:")
    for i, municipio in enumerate(top10, start=1):
        print(f"{i:02d}. {municipio}")

    return top10


def carregar_base_vereadores():
    candidatos = [
        "inteligencia_vereadores_alagoas_2024.csv",
        "base_vereadores_alagoas_2024.csv",
    ]

    arquivo = None
    for nome in candidatos:
        arquivo = localizar_arquivo(nome)
        if arquivo:
            break

    if arquivo is None:
        print("\nAVISO: base de vereadores não encontrada.")
        print("O ETL seguirá com todos os candidatos a vereador dos municípios TOP10.")
        return None

    df = ler_csv(arquivo)

    col_municipio = detectar_coluna(df, ["municipio", "município", "nm_municipio"])
    col_vereador = detectar_coluna(
        df,
        [
            "vereador",
            "nome_vereador",
            "nm_urna_candidato",
            "nm_votavel",
            "candidato",
            "nome",
        ],
    )
    col_partido = detectar_coluna(df, ["partido", "sg_partido", "sigla_partido"])
    col_numero = detectar_coluna(df, ["nr_votavel", "numero", "numero_candidato", "nr_candidato"])

    if col_municipio is None or col_vereador is None:
        print("\nAVISO: colunas essenciais não encontradas na base de vereadores.")
        print("Colunas encontradas:", list(df.columns))
        print("O ETL seguirá com todos os candidatos a vereador dos municípios TOP10.")
        return None

    saida = pd.DataFrame()
    saida["municipio_norm"] = df[col_municipio].apply(normalizar_texto)
    saida["vereador_norm"] = df[col_vereador].apply(normalizar_texto)
    saida["vereador_base"] = df[col_vereador].astype(str)

    saida["partido_base"] = df[col_partido].astype(str) if col_partido else ""
    saida["numero_norm"] = (
        df[col_numero].astype(str).str.extract(r"(\d+)")[0].fillna("")
        if col_numero
        else ""
    )

    saida = saida.drop_duplicates(
        subset=["municipio_norm", "vereador_norm", "numero_norm"]
    )

    print(f"\nBase de vereadores carregada: {arquivo}")
    print(f"Registros na base de vereadores: {len(saida):,}".replace(",", "."))

    return saida


def classificar_prioridade(ranking_secao, total_secoes):
    if total_secoes <= 0:
        return "BAIXA"

    limite_alta = max(1, round(total_secoes * 0.10))
    limite_media = max(limite_alta + 1, round(total_secoes * 0.30))

    if ranking_secao <= limite_alta:
        return "ALTA"
    if ranking_secao <= limite_media:
        return "MÉDIA"
    return "BAIXA"


def classificar_transferencia(percentual):
    if percentual >= 5:
        return "ALTO"
    if percentual >= 2:
        return "MÉDIO"
    return "BAIXO"


def main():
    print("=" * 70)
    print("ETL 016 — VOTAÇÃO POR SEÇÃO DOS VEREADORES TOP 10")
    print("=" * 70)

    arquivo_votacao = ARQUIVO_VOTACAO_SECAO

    if not arquivo_votacao.exists():
        encontrado = localizar_arquivo("votacao_secao_2024_AL.csv")
        if encontrado is None:
            raise FileNotFoundError(
                "Arquivo votacao_secao_2024_AL.csv não encontrado. "
                "Caminho esperado: data/raw/tse_2024/votacao_secao_2024_AL.csv"
            )
        arquivo_votacao = encontrado

    print("\nArquivo de votação localizado:")
    print(arquivo_votacao)

    votos = ler_csv(arquivo_votacao)

    print(f"\nRegistros totais na base TSE: {len(votos):,}".replace(",", "."))

    colunas_obrigatorias = [
        "NM_MUNICIPIO",
        "NR_ZONA",
        "NR_SECAO",
        "DS_CARGO",
        "NR_VOTAVEL",
        "NM_VOTAVEL",
        "QT_VOTOS",
    ]

    faltantes = [col for col in colunas_obrigatorias if col not in votos.columns]
    if faltantes:
        print("\nColunas encontradas na base TSE:")
        for col in votos.columns:
            print(f"- {col}")
        raise ValueError(f"Colunas obrigatórias ausentes: {faltantes}")

    votos = votos[votos["DS_CARGO"].apply(normalizar_texto) == "VEREADOR"].copy()

    votos["municipio"] = votos["NM_MUNICIPIO"].apply(normalizar_texto)
    votos["vereador"] = votos["NM_VOTAVEL"].apply(normalizar_texto)
    votos["numero"] = votos["NR_VOTAVEL"].astype(str).str.extract(r"(\d+)")[0].fillna("")
    votos["zona_eleitoral"] = votos["NR_ZONA"].astype(str).str.extract(r"(\d+)")[0].fillna("").str.zfill(4)
    votos["secao_eleitoral"] = votos["NR_SECAO"].astype(str).str.extract(r"(\d+)")[0].fillna("").str.zfill(4)
    votos["votos"] = pd.to_numeric(votos["QT_VOTOS"], errors="coerce").fillna(0).astype(int)

    votos = votos[~votos["vereador"].isin(["VOTO BRANCO", "VOTO NULO"])]
    votos = votos[votos["votos"] > 0].copy()

    votos["local_votacao"] = votos["NM_LOCAL_VOTACAO"].astype(str) if "NM_LOCAL_VOTACAO" in votos.columns else ""
    votos["endereco_local_votacao"] = (
        votos["DS_LOCAL_VOTACAO_ENDERECO"].astype(str)
        if "DS_LOCAL_VOTACAO_ENDERECO" in votos.columns
        else ""
    )

    print(f"Registros de vereador com votos positivos: {len(votos):,}".replace(",", "."))
    print(f"Municípios na base de votação: {votos['municipio'].nunique()}")

    top10 = carregar_top10_municipios()

    votos = votos[votos["municipio"].isin(top10)].copy()

    print(f"\nRegistros após filtro TOP10 municípios: {len(votos):,}".replace(",", "."))
    print(f"Municípios TOP10 encontrados na votação: {votos['municipio'].nunique()}")

    if len(votos) == 0:
        raise ValueError(
            "Filtro TOP10 retornou zero registros. "
            "Verifique a lista TOP10 ou a coluna NM_MUNICIPIO."
        )

    vereadores = carregar_base_vereadores()

    if vereadores is not None:
        vereadores_top10 = vereadores[vereadores["municipio_norm"].isin(top10)].copy()

        cruzamento_nome = votos.merge(
            vereadores_top10,
            how="inner",
            left_on=["municipio", "vereador"],
            right_on=["municipio_norm", "vereador_norm"],
        )

        cruzamento_numero = votos.merge(
            vereadores_top10,
            how="inner",
            left_on=["municipio", "numero"],
            right_on=["municipio_norm", "numero_norm"],
        )

        if len(cruzamento_nome) >= len(cruzamento_numero):
            votos = cruzamento_nome.copy()
            print("Cruzamento utilizado: município + nome do vereador")
        else:
            votos = cruzamento_numero.copy()
            print("Cruzamento utilizado: município + número do candidato")

        if len(votos) == 0:
            print("\nAVISO: cruzamento com vereadores eleitos retornou zero.")
            print("O ETL seguirá com todos os candidatos a vereador dos municípios TOP10.")
            votos = votos.copy()
            votos["partido"] = ""
            votos["vereador_nome_base"] = votos["vereador"]
        else:
            votos["partido"] = votos["partido_base"].fillna("")
            votos["vereador_nome_base"] = votos["vereador_base"].fillna(votos["vereador"])
            print(f"Registros após cruzamento com vereadores eleitos: {len(votos):,}".replace(",", "."))
    else:
        votos["partido"] = ""
        votos["vereador_nome_base"] = votos["vereador"]

    agrupado = (
        votos.groupby(
            [
                "municipio",
                "vereador",
                "vereador_nome_base",
                "partido",
                "numero",
                "zona_eleitoral",
                "secao_eleitoral",
                "local_votacao",
                "endereco_local_votacao",
            ],
            as_index=False,
        )["votos"]
        .sum()
    )

    total_vereador = (
        agrupado.groupby(["municipio", "vereador"], as_index=False)["votos"]
        .sum()
        .rename(columns={"votos": "total_votos_vereador_municipio"})
    )

    agrupado = agrupado.merge(total_vereador, on=["municipio", "vereador"], how="left")

    agrupado["percentual_no_municipio"] = (
        agrupado["votos"] / agrupado["total_votos_vereador_municipio"] * 100
    ).round(4)

    agrupado["ranking_secao"] = (
        agrupado.groupby(["municipio", "vereador"])["votos"]
        .rank(method="first", ascending=False)
        .astype(int)
    )

    agrupado = agrupado.sort_values(
        ["municipio", "vereador", "ranking_secao"],
        ascending=[True, True, True],
    )

    votacao_secao = agrupado[
        [
            "municipio",
            "vereador_nome_base",
            "partido",
            "zona_eleitoral",
            "secao_eleitoral",
            "votos",
            "percentual_no_municipio",
            "ranking_secao",
            "local_votacao",
            "endereco_local_votacao",
            "total_votos_vereador_municipio",
        ]
    ].rename(columns={"vereador_nome_base": "vereador"})

    votacao_secao.to_csv(
        SAIDA_VOTACAO_SECAO,
        sep=";",
        index=False,
        encoding="utf-8-sig",
    )

    total_secoes = (
        votacao_secao.groupby(["municipio", "vereador"], as_index=False)["secao_eleitoral"]
        .nunique()
        .rename(columns={"secao_eleitoral": "total_secoes_com_votos"})
    )

    mapa = votacao_secao.merge(total_secoes, on=["municipio", "vereador"], how="left")

    mapa["prioridade_territorial"] = mapa.apply(
        lambda row: classificar_prioridade(
            int(row["ranking_secao"]),
            int(row["total_secoes_com_votos"]),
        ),
        axis=1,
    )

    mapa["potencial_transferencia_local"] = mapa["percentual_no_municipio"].apply(
        classificar_transferencia
    )

    mapa = mapa.rename(
        columns={
            "zona_eleitoral": "zona",
            "secao_eleitoral": "secao",
            "percentual_no_municipio": "percentual",
        }
    )

    mapa = mapa[
        [
            "municipio",
            "vereador",
            "partido",
            "zona",
            "secao",
            "votos",
            "percentual",
            "ranking_secao",
            "prioridade_territorial",
            "potencial_transferencia_local",
            "local_votacao",
            "endereco_local_votacao",
            "total_votos_vereador_municipio",
            "total_secoes_com_votos",
        ]
    ]

    mapa.to_csv(
        SAIDA_MAPA_INFLUENCIA,
        sep=";",
        index=False,
        encoding="utf-8-sig",
    )

    print("\n" + "=" * 70)
    print("ETL 016 CONCLUÍDO COM SUCESSO")
    print("=" * 70)
    print(f"Arquivo gerado: {SAIDA_VOTACAO_SECAO}")
    print(f"Arquivo gerado: {SAIDA_MAPA_INFLUENCIA}")
    print(f"Linhas em votacao_secao_vereadores_top10: {len(votacao_secao):,}".replace(",", "."))
    print(f"Linhas em mapa_influencia_vereadores_top10: {len(mapa):,}".replace(",", "."))

    print("\nResumo por município:")
    resumo = (
        mapa.groupby("municipio")
        .agg(
            vereadores=("vereador", "nunique"),
            secoes=("secao", "nunique"),
            votos=("votos", "sum"),
        )
        .reset_index()
        .sort_values("votos", ascending=False)
    )

    print(resumo.to_string(index=False))


if __name__ == "__main__":
    main()