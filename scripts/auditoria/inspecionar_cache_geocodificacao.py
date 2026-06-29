# scripts/auditoria/inspecionar_cache_geocodificacao.py

from pathlib import Path
import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[2]

DATA_REFERENCE = BASE_DIR / "data" / "reference"
AUDIT_DIR = BASE_DIR / "data" / "audit"
AUDIT_DIR.mkdir(parents=True, exist_ok=True)

CACHE_PATH = DATA_REFERENCE / "cache_geocodificacao_locais_top10.csv"

OUT_COLUNAS = AUDIT_DIR / "inspecao_colunas_cache_geocodificacao.csv"
OUT_AMOSTRA = AUDIT_DIR / "amostra_cache_geocodificacao.csv"


def carregar_csv(caminho: Path) -> pd.DataFrame:
    if not caminho.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {caminho}")

    try:
        return pd.read_csv(caminho, sep=None, engine="python", encoding="utf-8-sig")
    except UnicodeDecodeError:
        return pd.read_csv(caminho, sep=None, engine="python", encoding="latin1")


def main():
    print()
    print("=" * 70)
    print("INSPEÇÃO DO CACHE DE GEOCODIFICAÇÃO")
    print("=" * 70)

    cache = carregar_csv(CACHE_PATH)

    print()
    print(f"Arquivo: {CACHE_PATH}")
    print(f"Total de registros: {len(cache)}")
    print(f"Total de colunas: {len(cache.columns)}")

    print()
    print("COLUNAS ENCONTRADAS:")
    print("-" * 70)

    linhas = []

    for col in cache.columns:
        vazios = cache[col].isna().sum() + (cache[col].astype(str).str.strip() == "").sum()
        preenchidos = len(cache) - vazios

        linhas.append({
            "coluna": col,
            "tipo": str(cache[col].dtype),
            "preenchidos": preenchidos,
            "vazios": vazios,
            "percentual_preenchido": round((preenchidos / len(cache)) * 100, 2) if len(cache) else 0,
            "exemplo_1": cache[col].dropna().astype(str).head(1).iloc[0] if cache[col].dropna().shape[0] else "",
            "exemplo_2": cache[col].dropna().astype(str).head(2).iloc[-1] if cache[col].dropna().shape[0] >= 2 else "",
        })

    df_colunas = pd.DataFrame(linhas)
    df_colunas.to_csv(OUT_COLUNAS, index=False, encoding="utf-8-sig")

    print(df_colunas.to_string(index=False))

    cache.head(50).to_csv(OUT_AMOSTRA, index=False, encoding="utf-8-sig")

    print()
    print("AMOSTRA DOS 10 PRIMEIROS REGISTROS:")
    print("-" * 70)
    print(cache.head(10).to_string(index=False))

    print()
    print("Arquivos gerados:")
    print(f"- {OUT_COLUNAS}")
    print(f"- {OUT_AMOSTRA}")

    print()
    print("INSPEÇÃO CONCLUÍDA.")


if __name__ == "__main__":
    main()