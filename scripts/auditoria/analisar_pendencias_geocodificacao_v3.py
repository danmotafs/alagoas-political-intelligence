# scripts/auditoria/analisar_pendencias_geocodificacao_v3.py

from pathlib import Path
import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[2]

DATA_REFERENCE = BASE_DIR / "data" / "reference"
AUDIT_DIR = BASE_DIR / "data" / "audit"
CURADORIA_DIR = BASE_DIR / "data" / "curadoria"

AUDIT_DIR.mkdir(parents=True, exist_ok=True)
CURADORIA_DIR.mkdir(parents=True, exist_ok=True)

CACHE_V3_PATH = DATA_REFERENCE / "cache_geocodificacao_locais_top10_v3.csv"
PLANO_PATH = AUDIT_DIR / "plano_saneamento_geocodificacao.csv"

OUT_PENDENCIAS = AUDIT_DIR / "pendencias_geocodificacao_v3.csv"
OUT_RESUMO_MUNICIPIO = AUDIT_DIR / "resumo_pendencias_por_municipio_v3.csv"
OUT_RESUMO_TIPO = AUDIT_DIR / "resumo_pendencias_por_tipo_v3.csv"
OUT_TOP20 = AUDIT_DIR / "top20_pendencias_geocodificacao_v3.csv"
OUT_CURADORIA_FINAL = CURADORIA_DIR / "curadoria_geocodificacao_pendentes_v3.csv"


def carregar_csv(caminho: Path) -> pd.DataFrame:
    if not caminho.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {caminho}")

    try:
        return pd.read_csv(caminho, sep=None, engine="python", encoding="utf-8-sig")
    except UnicodeDecodeError:
        return pd.read_csv(caminho, sep=None, engine="python", encoding="latin1")


def separar_chave(chave: str):
    partes = str(chave).split("|")

    municipio = partes[0].strip() if len(partes) >= 1 else ""
    local = partes[1].strip() if len(partes) >= 2 else ""
    endereco = partes[2].strip() if len(partes) >= 3 else ""

    return municipio, local, endereco


def vazio_ou_nulo(serie: pd.Series) -> pd.Series:
    return serie.isna() | (serie.astype(str).str.strip() == "")


def classificar_tipo_pendencia(local: str, endereco: str) -> str:
    texto = f"{local} {endereco}".upper()

    if any(t in texto for t in ["POVOADO", "POV.", "POV "]):
        return "POVOADO"

    if any(t in texto for t in ["SITIO", "SÍTIO", "ST."]):
        return "SITIO"

    if any(t in texto for t in ["VILA", "VL."]):
        return "VILA"

    if any(t in texto for t in ["ASSENTAMENTO", "ASSENT.", "ACAMPAMENTO"]):
        return "ASSENTAMENTO"

    if any(t in texto for t in ["FAZENDA", "FAZ."]):
        return "FAZENDA"

    if any(t in texto for t in ["CONJUNTO", "CONJ.", "CJ "]):
        return "CONJUNTO_HABITACIONAL"

    if any(t in texto for t in ["LOTEAMENTO", "LOT."]):
        return "LOTEAMENTO"

    if any(t in texto for t in ["ESCOLA", "COLÉGIO", "COLEGIO", "GRUPO ESCOLAR", "E.E.", "E.M.", "ESC."]):
        if any(t in texto for t in ["POVOADO", "SITIO", "SÍTIO", "VILA", "ASSENTAMENTO", "FAZENDA"]):
            return "ESCOLA_RURAL"
        return "ESCOLA_URBANA_OU_SEDE"

    if any(t in texto for t in ["RUA", "AV.", "AVENIDA", "PRACA", "PRAÇA", "TRAVESSA"]):
        return "ENDERECO_URBANO"

    return "OUTROS"


def classificar_prioridade_por_registros(registros: int) -> str:
    if registros >= 300:
        return "PRIORIDADE_1"
    if registros >= 150:
        return "PRIORIDADE_2"
    if registros >= 50:
        return "PRIORIDADE_3"
    return "PRIORIDADE_4"


def main():
    print()
    print("=" * 70)
    print("ANÁLISE DAS PENDÊNCIAS DE GEOCODIFICAÇÃO — V3")
    print("=" * 70)

    cache = carregar_csv(CACHE_V3_PATH)
    plano = carregar_csv(PLANO_PATH)

    cache[["municipio_cache", "local_cache", "endereco_cache"]] = cache["chave_local"].apply(
        lambda x: pd.Series(separar_chave(x))
    )

    pendentes_cache = cache[
        vazio_ou_nulo(cache["latitude"]) |
        vazio_ou_nulo(cache["longitude"])
    ].copy()

    pendentes_cache["tipo_pendencia"] = pendentes_cache.apply(
        lambda row: classificar_tipo_pendencia(
            row.get("local_cache", ""),
            row.get("endereco_cache", "")
        ),
        axis=1
    )

    base_plano = plano[
        [
            "prioridade",
            "municipio",
            "local_sem_geo",
            "melhor_local_cache",
            "endereco_cache",
            "consulta_geocoding",
            "registros_afetados",
            "score_similaridade",
            "status_match",
            "status_geocodificacao",
        ]
    ].copy()

    pendencias = base_plano.merge(
        pendentes_cache[
            [
                "chave_local",
                "municipio_cache",
                "local_cache",
                "endereco_cache",
                "consulta_geocoding",
                "status_geocodificacao",
                "tipo_pendencia",
            ]
        ],
        left_on=["municipio", "melhor_local_cache", "endereco_cache"],
        right_on=["municipio_cache", "local_cache", "endereco_cache"],
        how="inner",
        suffixes=("", "_cache")
    )

    if pendencias.empty:
        print()
        print("Nenhuma pendência encontrada após a V3.")
        return

    pendencias["prioridade_recalculada"] = pendencias["registros_afetados"].apply(
        classificar_prioridade_por_registros
    )

    pendencias["latitude_curadoria"] = ""
    pendencias["longitude_curadoria"] = ""
    pendencias["bairro_curadoria"] = ""
    pendencias["status_curadoria"] = "PENDENTE"
    pendencias["fonte_validacao"] = ""
    pendencias["observacao_curadoria"] = ""

    colunas_saida = [
        "prioridade",
        "prioridade_recalculada",
        "tipo_pendencia",
        "municipio",
        "local_sem_geo",
        "melhor_local_cache",
        "endereco_cache",
        "consulta_geocoding",
        "registros_afetados",
        "score_similaridade",
        "status_match",
        "status_geocodificacao",
        "latitude_curadoria",
        "longitude_curadoria",
        "bairro_curadoria",
        "status_curadoria",
        "fonte_validacao",
        "observacao_curadoria",
    ]

    pendencias_saida = pendencias[colunas_saida].copy()

    pendencias_saida = pendencias_saida.sort_values(
        ["registros_afetados", "municipio", "local_sem_geo"],
        ascending=[False, True, True]
    )

    pendencias_saida.to_csv(OUT_PENDENCIAS, index=False, encoding="utf-8-sig")

    resumo_municipio = (
        pendencias_saida
        .groupby("municipio", dropna=False)
        .agg(
            locais_pendentes=("local_sem_geo", "count"),
            registros_afetados=("registros_afetados", "sum"),
            prioridade_1=("prioridade", lambda s: (s == "PRIORIDADE_1").sum()),
            prioridade_2=("prioridade", lambda s: (s == "PRIORIDADE_2").sum()),
            prioridade_3=("prioridade", lambda s: (s == "PRIORIDADE_3").sum()),
            prioridade_4=("prioridade", lambda s: (s == "PRIORIDADE_4").sum()),
        )
        .reset_index()
        .sort_values("registros_afetados", ascending=False)
    )

    resumo_municipio.to_csv(OUT_RESUMO_MUNICIPIO, index=False, encoding="utf-8-sig")

    resumo_tipo = (
        pendencias_saida
        .groupby("tipo_pendencia", dropna=False)
        .agg(
            locais_pendentes=("local_sem_geo", "count"),
            registros_afetados=("registros_afetados", "sum"),
        )
        .reset_index()
        .sort_values("registros_afetados", ascending=False)
    )

    resumo_tipo.to_csv(OUT_RESUMO_TIPO, index=False, encoding="utf-8-sig")

    top20 = pendencias_saida.head(20).copy()
    top20.to_csv(OUT_TOP20, index=False, encoding="utf-8-sig")

    pendencias_saida.to_csv(OUT_CURADORIA_FINAL, index=False, encoding="utf-8-sig")

    print()
    print("RESUMO GERAL")
    print("-" * 70)
    print(f"Locais pendentes após V3: {len(pendencias_saida)}")
    print(f"Registros afetados pendentes: {pendencias_saida['registros_afetados'].sum()}")

    print()
    print("PENDÊNCIAS POR MUNICÍPIO")
    print("-" * 70)
    print(resumo_municipio.to_string(index=False))

    print()
    print("PENDÊNCIAS POR TIPO")
    print("-" * 70)
    print(resumo_tipo.to_string(index=False))

    print()
    print("TOP 20 PENDÊNCIAS")
    print("-" * 70)
    print(top20.to_string(index=False))

    print()
    print("Arquivos gerados:")
    print(f"- {OUT_PENDENCIAS}")
    print(f"- {OUT_RESUMO_MUNICIPIO}")
    print(f"- {OUT_RESUMO_TIPO}")
    print(f"- {OUT_TOP20}")
    print(f"- {OUT_CURADORIA_FINAL}")

    print()
    print("ANÁLISE DE PENDÊNCIAS V3 CONCLUÍDA.")


if __name__ == "__main__":
    main()