# scripts/auditoria/auditar_correspondencia_locais.py

import pandas as pd
import unicodedata
import re
from pathlib import Path
from difflib import SequenceMatcher


BASE_DIR = Path(__file__).resolve().parents[2]

DATA_FINAL_DIR = BASE_DIR / "data" / "final"
AUDIT_DIR = BASE_DIR / "data" / "audit"
AUDIT_DIR.mkdir(parents=True, exist_ok=True)

MAPA_PATH = DATA_FINAL_DIR / "mapa_influencia_geografico.csv"

OUT_CORRESPONDENCIAS = AUDIT_DIR / "auditoria_correspondencia_locais.csv"
OUT_NAO_GEO_UNICOS = AUDIT_DIR / "locais_nao_georreferenciados_unicos.csv"
OUT_RESUMO = AUDIT_DIR / "resumo_correspondencia_locais.csv"


def carregar_csv(caminho: Path) -> pd.DataFrame:
    if not caminho.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {caminho}")

    try:
        return pd.read_csv(caminho, sep=None, engine="python", encoding="utf-8-sig")
    except UnicodeDecodeError:
        return pd.read_csv(caminho, sep=None, engine="python", encoding="latin1")


def normalizar_texto(valor) -> str:
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

    for padrao, troca in substituicoes.items():
        texto = re.sub(padrao, troca, texto)

    texto = re.sub(r"[^A-Z0-9 ]", " ", texto)
    texto = re.sub(r"\s+", " ", texto).strip()

    return texto


def detectar_coluna(df: pd.DataFrame, candidatos: list[str]) -> str:
    colunas_normalizadas = {normalizar_texto(col): col for col in df.columns}

    for candidato in candidatos:
        candidato_norm = normalizar_texto(candidato)
        if candidato_norm in colunas_normalizadas:
            return colunas_normalizadas[candidato_norm]

    for col in df.columns:
        col_norm = normalizar_texto(col)
        for candidato in candidatos:
            candidato_norm = normalizar_texto(candidato)
            if candidato_norm in col_norm or col_norm in candidato_norm:
                return col

    raise ValueError(
        f"Coluna não encontrada. Candidatos: {candidatos}. "
        f"Colunas disponíveis: {list(df.columns)}"
    )


def campo_vazio_ou_nulo(serie: pd.Series) -> pd.Series:
    return serie.isna() | (serie.astype(str).str.strip() == "")


def similaridade(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a, b).ratio()


def classificar_match(score: float) -> str:
    if score >= 0.95:
        return "MATCH_FORTE"
    if score >= 0.85:
        return "MATCH_PROVAVEL"
    if score >= 0.75:
        return "MATCH_FRACO"
    return "SEM_MATCH"


def main():
    print("\nAUDITORIA DE CORRESPONDÊNCIA DE LOCAIS")
    print("=" * 70)

    mapa = carregar_csv(MAPA_PATH)

    col_municipio = detectar_coluna(mapa, ["municipio", "nm_municipio"])
    col_local = detectar_coluna(mapa, ["local_votacao", "nome_local", "nm_local_votacao", "local"])
    col_lat = detectar_coluna(mapa, ["latitude", "lat"])
    col_lon = detectar_coluna(mapa, ["longitude", "lon", "lng"])

    mapa["_municipio_norm"] = mapa[col_municipio].apply(normalizar_texto)
    mapa["_local_norm"] = mapa[col_local].apply(normalizar_texto)

    sem_geo = mapa[
        campo_vazio_ou_nulo(mapa[col_lat]) |
        campo_vazio_ou_nulo(mapa[col_lon])
    ].copy()

    com_geo = mapa[
        ~campo_vazio_ou_nulo(mapa[col_lat]) &
        ~campo_vazio_ou_nulo(mapa[col_lon])
    ].copy()

    locais_nao_geo_unicos = (
        sem_geo
        .groupby(["_municipio_norm", "_local_norm", col_municipio, col_local], dropna=False)
        .size()
        .reset_index(name="qtd_registros_afetados")
        .sort_values("qtd_registros_afetados", ascending=False)
    )

    locais_geo_unicos = (
        com_geo
        .groupby(["_municipio_norm", "_local_norm", col_municipio, col_local, col_lat, col_lon], dropna=False)
        .size()
        .reset_index(name="qtd_registros_georreferenciados")
    )

    locais_nao_geo_unicos.to_csv(OUT_NAO_GEO_UNICOS, index=False, encoding="utf-8-sig")

    resultados = []

    for _, row in locais_nao_geo_unicos.iterrows():
        municipio_norm = row["_municipio_norm"]
        local_norm = row["_local_norm"]

        candidatos = locais_geo_unicos[
            locais_geo_unicos["_municipio_norm"] == municipio_norm
        ].copy()

        melhor_score = 0.0
        melhor_local = ""
        melhor_lat = ""
        melhor_lon = ""
        qtd_geo_ref = 0

        for _, cand in candidatos.iterrows():
            score = similaridade(local_norm, cand["_local_norm"])

            if score > melhor_score:
                melhor_score = score
                melhor_local = cand[col_local]
                melhor_lat = cand[col_lat]
                melhor_lon = cand[col_lon]
                qtd_geo_ref = cand["qtd_registros_georreferenciados"]

        resultados.append({
            "municipio": row[col_municipio],
            "local_nao_georreferenciado": row[col_local],
            "local_nao_georreferenciado_normalizado": local_norm,
            "qtd_registros_afetados": int(row["qtd_registros_afetados"]),
            "melhor_correspondencia_georreferenciada": melhor_local,
            "score_similaridade": round(melhor_score, 4),
            "status_match": classificar_match(melhor_score),
            "latitude_sugerida": melhor_lat,
            "longitude_sugerida": melhor_lon,
            "qtd_registros_do_local_sugerido": int(qtd_geo_ref) if qtd_geo_ref else 0,
        })

    correspondencias = pd.DataFrame(resultados)
    correspondencias.to_csv(OUT_CORRESPONDENCIAS, index=False, encoding="utf-8-sig")

    resumo = (
        correspondencias
        .groupby("status_match", dropna=False)
        .agg(
            qtd_locais=("status_match", "count"),
            registros_afetados=("qtd_registros_afetados", "sum")
        )
        .reset_index()
        .sort_values("registros_afetados", ascending=False)
    )

    resumo.to_csv(OUT_RESUMO, index=False, encoding="utf-8-sig")

    print("\nARQUIVOS GERADOS:")
    print(f"- {OUT_CORRESPONDENCIAS}")
    print(f"- {OUT_NAO_GEO_UNICOS}")
    print(f"- {OUT_RESUMO}")

    print("\nRESUMO DOS MATCHES:")
    print(resumo.to_string(index=False))

    print("\nTOP 20 LOCAIS SEM GEO COM MAIOR IMPACTO:")
    print(
        correspondencias
        .sort_values("qtd_registros_afetados", ascending=False)
        .head(20)
        .to_string(index=False)
    )

    print("\nAUDITORIA CONCLUÍDA.")


if __name__ == "__main__":
    main()