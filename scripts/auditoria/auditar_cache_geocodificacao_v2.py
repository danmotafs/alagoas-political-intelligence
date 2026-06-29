# scripts/auditoria/auditar_cache_geocodificacao_v2.py

import re
import unicodedata
from pathlib import Path
from difflib import SequenceMatcher

import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[2]

DATA_FINAL = BASE_DIR / "data" / "final"
DATA_REFERENCE = BASE_DIR / "data" / "reference"
AUDIT_DIR = BASE_DIR / "data" / "audit"
AUDIT_DIR.mkdir(parents=True, exist_ok=True)

MAPA_PATH = DATA_FINAL / "mapa_influencia_geografico.csv"
CACHE_PATH = DATA_REFERENCE / "cache_geocodificacao_locais_top10.csv"

OUT_AUDITORIA = AUDIT_DIR / "auditoria_cache_geocodificacao_v2.csv"
OUT_RESUMO = AUDIT_DIR / "resumo_cache_geocodificacao_v2.csv"


def carregar_csv(caminho: Path) -> pd.DataFrame:
    if not caminho.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {caminho}")

    try:
        return pd.read_csv(caminho, sep=None, engine="python", encoding="utf-8-sig")
    except UnicodeDecodeError:
        return pd.read_csv(caminho, sep=None, engine="python", encoding="latin1")


def normalizar(valor) -> str:
    if pd.isna(valor):
        return ""

    texto = str(valor).upper().strip()
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(c for c in texto if not unicodedata.combining(c))

    substituicoes = {
        r"\bE\.E\.?\b": "ESCOLA ESTADUAL",
        r"\bEE\b": "ESCOLA ESTADUAL",
        r"\bE\.M\.?\b": "ESCOLA MUNICIPAL",
        r"\bEM\b": "ESCOLA MUNICIPAL",
        r"\bESC\.?\b": "ESCOLA",
        r"\bCOL\.?\b": "COLEGIO",
        r"\bDR\.?\b": "DOUTOR",
        r"\bDRA\.?\b": "DOUTORA",
        r"\bPROF\.?\b": "PROFESSOR",
        r"\bPROFA\.?\b": "PROFESSORA",
        r"\bPROFª\b": "PROFESSORA",
        r"\bMUN\.?\b": "MUNICIPAL",
        r"\bEST\.?\b": "ESTADUAL",
        r"\bENS\.?\b": "ENSINO",
        r"\bFUND\.?\b": "FUNDAMENTAL",
    }

    for padrao, novo in substituicoes.items():
        texto = re.sub(padrao, novo, texto)

    texto = re.sub(r"[^A-Z0-9 ]", " ", texto)
    texto = re.sub(r"\s+", " ", texto).strip()

    return texto


def detectar_coluna(df: pd.DataFrame, candidatos: list[str]) -> str:
    colunas_norm = {normalizar(col): col for col in df.columns}

    for candidato in candidatos:
        candidato_norm = normalizar(candidato)
        if candidato_norm in colunas_norm:
            return colunas_norm[candidato_norm]

    for col in df.columns:
        col_norm = normalizar(col)
        for candidato in candidatos:
            candidato_norm = normalizar(candidato)
            if candidato_norm in col_norm or col_norm in candidato_norm:
                return col

    raise ValueError(
        f"Coluna não encontrada. Candidatos: {candidatos}. "
        f"Colunas disponíveis: {list(df.columns)}"
    )


def vazio(serie: pd.Series) -> pd.Series:
    return serie.isna() | (serie.astype(str).str.strip() == "")


def similaridade(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a, b).ratio()


def classificar(score: float) -> str:
    if score >= 0.95:
        return "MATCH_FORTE"
    if score >= 0.85:
        return "MATCH_PROVAVEL"
    if score >= 0.75:
        return "MATCH_FRACO"
    return "SEM_MATCH"


def separar_chave_cache(valor):
    partes = str(valor).split("|")

    municipio = partes[0].strip() if len(partes) >= 1 else ""
    local = partes[1].strip() if len(partes) >= 2 else str(valor).strip()
    endereco = partes[2].strip() if len(partes) >= 3 else ""

    return municipio, local, endereco


def main():
    print()
    print("=" * 70)
    print("AUDITORIA DO CACHE DE GEOCODIFICAÇÃO — V2")
    print("=" * 70)

    mapa = carregar_csv(MAPA_PATH)
    cache = carregar_csv(CACHE_PATH)

    col_municipio = detectar_coluna(mapa, ["municipio", "nm_municipio"])
    col_local = detectar_coluna(mapa, ["local_votacao", "nome_local", "local"])
    col_lat = detectar_coluna(mapa, ["latitude", "lat"])
    col_lon = detectar_coluna(mapa, ["longitude", "lon", "lng"])

    col_cache_chave = detectar_coluna(
        cache,
        ["chave_local", "local_votacao", "nome_local", "local"]
    )

    col_cache_lat = detectar_coluna(cache, ["latitude", "lat"])
    col_cache_lon = detectar_coluna(cache, ["longitude", "lon", "lng"])

    cache[["municipio_cache", "local_cache", "endereco_cache"]] = cache[col_cache_chave].apply(
        lambda x: pd.Series(separar_chave_cache(x))
    )

    mapa["_municipio_norm"] = mapa[col_municipio].apply(normalizar)
    mapa["_local_norm"] = mapa[col_local].apply(normalizar)

    cache["_municipio_norm"] = cache["municipio_cache"].apply(normalizar)
    cache["_local_norm"] = cache["local_cache"].apply(normalizar)

    sem_geo = mapa[
        vazio(mapa[col_lat]) |
        vazio(mapa[col_lon])
    ].copy()

    locais_sem_geo = (
        sem_geo
        .groupby(
            ["_municipio_norm", "_local_norm", col_municipio, col_local],
            dropna=False
        )
        .size()
        .reset_index(name="registros_afetados")
        .sort_values("registros_afetados", ascending=False)
    )

    resultados = []

    for _, row in locais_sem_geo.iterrows():
        municipio_norm = row["_municipio_norm"]
        local_norm = row["_local_norm"]

        candidatos = cache[cache["_municipio_norm"] == municipio_norm].copy()

        melhor_score = 0.0
        melhor_local = ""
        melhor_endereco = ""
        melhor_lat = ""
        melhor_lon = ""

        for _, cand in candidatos.iterrows():
            score = similaridade(local_norm, cand["_local_norm"])

            if score > melhor_score:
                melhor_score = score
                melhor_local = cand["local_cache"]
                melhor_endereco = cand["endereco_cache"]
                melhor_lat = cand[col_cache_lat]
                melhor_lon = cand[col_cache_lon]

        resultados.append({
            "municipio": row[col_municipio],
            "local_sem_geo": row[col_local],
            "local_sem_geo_normalizado": local_norm,
            "registros_afetados": int(row["registros_afetados"]),
            "melhor_local_cache": melhor_local,
            "melhor_endereco_cache": melhor_endereco,
            "score_similaridade": round(melhor_score, 4),
            "status_match": classificar(melhor_score),
            "latitude_sugerida": melhor_lat,
            "longitude_sugerida": melhor_lon,
        })

    resultado = pd.DataFrame(resultados)
    resultado.to_csv(OUT_AUDITORIA, index=False, encoding="utf-8-sig")

    resumo = (
        resultado
        .groupby("status_match", dropna=False)
        .agg(
            locais=("status_match", "count"),
            registros=("registros_afetados", "sum")
        )
        .reset_index()
        .sort_values("registros", ascending=False)
    )

    resumo.to_csv(OUT_RESUMO, index=False, encoding="utf-8-sig")

    print()
    print("RESUMO")
    print("-" * 70)
    print(resumo.to_string(index=False))

    print()
    print("TOP 20 LOCAIS COM MAIOR IMPACTO")
    print("-" * 70)
    print(
        resultado
        .sort_values("registros_afetados", ascending=False)
        .head(20)
        .to_string(index=False)
    )

    print()
    print("Arquivos gerados:")
    print(f"- {OUT_AUDITORIA}")
    print(f"- {OUT_RESUMO}")

    print()
    print("AUDITORIA V2 CONCLUÍDA.")


if __name__ == "__main__":
    main()