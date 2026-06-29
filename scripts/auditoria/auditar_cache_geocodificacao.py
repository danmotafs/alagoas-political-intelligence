# scripts/auditoria/auditar_cache_geocodificacao.py

import pandas as pd
import unicodedata
import re
from pathlib import Path
from difflib import SequenceMatcher


BASE_DIR = Path(__file__).resolve().parents[2]

DATA_FINAL = BASE_DIR / "data" / "final"
DATA_REFERENCE = BASE_DIR / "data" / "reference"

AUDIT_DIR = BASE_DIR / "data" / "audit"
AUDIT_DIR.mkdir(parents=True, exist_ok=True)

MAPA_PATH = DATA_FINAL / "mapa_influencia_geografico.csv"
CACHE_PATH = DATA_REFERENCE / "cache_geocodificacao_locais_top10.csv"

OUT_RECUPERACAO = AUDIT_DIR / "auditoria_cache_geocodificacao.csv"
OUT_RESUMO = AUDIT_DIR / "resumo_cache_geocodificacao.csv"


def carregar_csv(caminho):
    try:
        return pd.read_csv(
            caminho,
            sep=None,
            engine="python",
            encoding="utf-8-sig"
        )
    except UnicodeDecodeError:
        return pd.read_csv(
            caminho,
            sep=None,
            engine="python",
            encoding="latin1"
        )


def normalizar(texto):

    if pd.isna(texto):
        return ""

    texto = str(texto).upper().strip()

    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(
        c for c in texto
        if not unicodedata.combining(c)
    )

    substituicoes = {
        r"\bE\.E\.?\b": "ESCOLA ESTADUAL",
        r"\bEE\b": "ESCOLA ESTADUAL",
        r"\bE\.M\.?\b": "ESCOLA MUNICIPAL",
        r"\bEM\b": "ESCOLA MUNICIPAL",
        r"\bESC\.?\b": "ESCOLA",
        r"\bCOL\.?\b": "COLEGIO",
        r"\bPROF\.?\b": "PROFESSOR",
        r"\bDR\.?\b": "DOUTOR",
        r"\bDRA\.?\b": "DOUTORA",
    }

    for padrao, novo in substituicoes.items():
        texto = re.sub(padrao, novo, texto)

    texto = re.sub(r"[^A-Z0-9 ]", " ", texto)
    texto = re.sub(r"\s+", " ", texto)

    return texto.strip()


def similaridade(a, b):
    return SequenceMatcher(None, a, b).ratio()


def detectar_coluna(df, candidatos):

    cols = {normalizar(c): c for c in df.columns}

    for candidato in candidatos:
        chave = normalizar(candidato)

        if chave in cols:
            return cols[chave]

    for col in df.columns:

        col_norm = normalizar(col)

        for candidato in candidatos:

            candidato_norm = normalizar(candidato)

            if candidato_norm in col_norm:
                return col

    raise ValueError(
        f"Coluna não encontrada. "
        f"Candidatos: {candidatos}\n"
        f"Disponíveis: {list(df.columns)}"
    )


def vazio(coluna):
    return (
        coluna.isna()
        | (coluna.astype(str).str.strip() == "")
    )


def classificar(score):

    if score >= 0.95:
        return "MATCH_FORTE"

    if score >= 0.85:
        return "MATCH_PROVAVEL"

    if score >= 0.75:
        return "MATCH_FRACO"

    return "SEM_MATCH"


def main():

    print()
    print("=" * 70)
    print("AUDITORIA DO CACHE DE GEOCODIFICAÇÃO")
    print("=" * 70)

    mapa = carregar_csv(MAPA_PATH)
    cache = carregar_csv(CACHE_PATH)

    print()
    print("Mapa:", len(mapa))
    print("Cache:", len(cache))

    col_municipio = detectar_coluna(
        mapa,
        ["municipio"]
    )

    col_local = detectar_coluna(
        mapa,
        ["local_votacao", "nome_local", "local"]
    )

    col_lat = detectar_coluna(
        mapa,
        ["latitude"]
    )

    col_lon = detectar_coluna(
        mapa,
        ["longitude"]
    )

    cache_local = detectar_coluna(
        cache,
        ["local_votacao", "nome_local", "local"]
    )

    mapa["_municipio_norm"] = mapa[col_municipio].apply(normalizar)
    mapa["_local_norm"] = mapa[col_local].apply(normalizar)

    cache["_local_norm"] = cache[cache_local].apply(normalizar)

    sem_geo = mapa[
        vazio(mapa[col_lat]) |
        vazio(mapa[col_lon])
    ].copy()

    locais_sem_geo = (
        sem_geo
        .groupby(
            [
                "_municipio_norm",
                "_local_norm",
                col_municipio,
                col_local
            ]
        )
        .size()
        .reset_index(name="registros_afetados")
        .sort_values(
            "registros_afetados",
            ascending=False
        )
    )

    resultados = []

    for _, row in locais_sem_geo.iterrows():

        local_norm = row["_local_norm"]

        melhor_score = 0
        melhor_local = ""

        for _, c in cache.iterrows():

            score = similaridade(
                local_norm,
                c["_local_norm"]
            )

            if score > melhor_score:
                melhor_score = score
                melhor_local = c[cache_local]

        resultados.append({

            "municipio": row[col_municipio],
            "local_sem_geo": row[col_local],
            "registros_afetados": row["registros_afetados"],

            "melhor_correspondencia_cache":
                melhor_local,

            "score_similaridade":
                round(melhor_score, 4),

            "status_match":
                classificar(melhor_score)
        })

    resultado = pd.DataFrame(resultados)

    resultado.to_csv(
        OUT_RECUPERACAO,
        index=False,
        encoding="utf-8-sig"
    )

    resumo = (
        resultado
        .groupby("status_match")
        .agg(
            locais=("status_match", "count"),
            registros=("registros_afetados", "sum")
        )
        .reset_index()
        .sort_values(
            "registros",
            ascending=False
        )
    )

    resumo.to_csv(
        OUT_RESUMO,
        index=False,
        encoding="utf-8-sig"
    )

    print()
    print("RESUMO")
    print("-" * 70)

    print(resumo.to_string(index=False))

    print()
    print("TOP 20 RECUPERÁVEIS")
    print("-" * 70)

    print(
        resultado
        .sort_values(
            "registros_afetados",
            ascending=False
        )
        .head(20)
        .to_string(index=False)
    )

    print()
    print("Arquivos gerados:")
    print(OUT_RECUPERACAO)
    print(OUT_RESUMO)


if __name__ == "__main__":
    main()