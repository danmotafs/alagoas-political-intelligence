# scripts/auditoria/gerar_plano_saneamento_geocodificacao.py

from pathlib import Path
import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[2]

DATA_REFERENCE = BASE_DIR / "data" / "reference"
AUDIT_DIR = BASE_DIR / "data" / "audit"
AUDIT_DIR.mkdir(parents=True, exist_ok=True)

CACHE_PATH = DATA_REFERENCE / "cache_geocodificacao_locais_top10.csv"
AUDITORIA_PATH = AUDIT_DIR / "auditoria_cache_geocodificacao_v2.csv"

OUT_PLANO = AUDIT_DIR / "plano_saneamento_geocodificacao.csv"
OUT_RESUMO = AUDIT_DIR / "resumo_plano_saneamento_geocodificacao.csv"


def carregar_csv(caminho: Path) -> pd.DataFrame:
    if not caminho.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {caminho}")

    try:
        return pd.read_csv(caminho, sep=None, engine="python", encoding="utf-8-sig")
    except UnicodeDecodeError:
        return pd.read_csv(caminho, sep=None, engine="python", encoding="latin1")


def separar_chave_local(chave: str):
    partes = str(chave).split("|")

    municipio = partes[0].strip() if len(partes) > 0 else ""
    local = partes[1].strip() if len(partes) > 1 else ""
    endereco = partes[2].strip() if len(partes) > 2 else ""

    return municipio, local, endereco


def classificar_prioridade(registros: int) -> str:
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
    print("GERAÇÃO DO PLANO DE SANEAMENTO DE GEOCODIFICAÇÃO")
    print("=" * 70)

    cache = carregar_csv(CACHE_PATH)
    auditoria = carregar_csv(AUDITORIA_PATH)

    cache[["municipio_cache", "local_cache", "endereco_cache"]] = cache["chave_local"].apply(
        lambda x: pd.Series(separar_chave_local(x))
    )

    cache_sem_geo = cache[
        cache["latitude"].isna() |
        cache["longitude"].isna()
    ].copy()

    plano = auditoria.merge(
        cache_sem_geo[
            [
                "chave_local",
                "municipio_cache",
                "local_cache",
                "endereco_cache",
                "consulta_geocoding",
                "status_geocodificacao",
            ]
        ],
        left_on=["municipio", "melhor_local_cache"],
        right_on=["municipio_cache", "local_cache"],
        how="left"
    )

    plano["prioridade"] = plano["registros_afetados"].apply(classificar_prioridade)

    plano["latitude_manual"] = ""
    plano["longitude_manual"] = ""
    plano["bairro_manual"] = ""
    plano["fonte_curadoria"] = ""
    plano["observacao_curadoria"] = ""

    colunas_saida = [
        "prioridade",
        "municipio",
        "local_sem_geo",
        "melhor_local_cache",
        "melhor_endereco_cache",
        "endereco_cache",
        "consulta_geocoding",
        "registros_afetados",
        "score_similaridade",
        "status_match",
        "status_geocodificacao",
        "latitude_manual",
        "longitude_manual",
        "bairro_manual",
        "fonte_curadoria",
        "observacao_curadoria",
    ]

    plano_saida = plano[colunas_saida].copy()

    plano_saida = plano_saida.sort_values(
        ["prioridade", "registros_afetados"],
        ascending=[True, False]
    )

    plano_saida.to_csv(OUT_PLANO, index=False, encoding="utf-8-sig")

    resumo = (
        plano_saida
        .groupby("prioridade")
        .agg(
            locais=("local_sem_geo", "count"),
            registros_afetados=("registros_afetados", "sum")
        )
        .reset_index()
        .sort_values("prioridade")
    )

    resumo.to_csv(OUT_RESUMO, index=False, encoding="utf-8-sig")

    print()
    print("RESUMO DO PLANO")
    print("-" * 70)
    print(resumo.to_string(index=False))

    print()
    print("TOP 20 PRIORIDADES")
    print("-" * 70)
    print(plano_saida.head(20).to_string(index=False))

    print()
    print("Arquivos gerados:")
    print(f"- {OUT_PLANO}")
    print(f"- {OUT_RESUMO}")

    print()
    print("PLANO DE SANEAMENTO CONCLUÍDO.")


if __name__ == "__main__":
    main()