import re
import time
import unicodedata
from pathlib import Path

import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[2]

FINAL_DIR = BASE_DIR / "data" / "final"
REFERENCE_DIR = BASE_DIR / "data" / "reference"

FINAL_DIR.mkdir(parents=True, exist_ok=True)
REFERENCE_DIR.mkdir(parents=True, exist_ok=True)

ENTRADA = FINAL_DIR / "mapa_influencia_vereadores_top10.csv"

SAIDA_LOCAIS = FINAL_DIR / "locais_votacao_top10.csv"
SAIDA_GEOGRAFICO = FINAL_DIR / "mapa_influencia_geografico.csv"
CACHE_GEOCODIFICACAO = REFERENCE_DIR / "cache_geocodificacao_locais_top10.csv"


def normalizar_texto(valor):
    if pd.isna(valor):
        return ""

    texto = str(valor).strip().upper()
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    texto = re.sub(r"\s+", " ", texto)
    return texto


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

    raise ValueError(f"Não foi possível ler o arquivo: {caminho}")


def montar_chave_local(row):
    return "|".join(
        [
            normalizar_texto(row.get("municipio", "")),
            normalizar_texto(row.get("local_votacao", "")),
            normalizar_texto(row.get("endereco_local_votacao", "")),
        ]
    )


def limpar_endereco(endereco):
    if pd.isna(endereco):
        return ""

    texto = str(endereco).strip()
    texto = re.sub(r"\s+", " ", texto)
    return texto


def montar_consulta_geocoding(municipio, endereco, local):
    municipio = str(municipio).title()
    endereco = limpar_endereco(endereco)
    local = str(local).title().strip()

    if endereco and endereco.lower() not in ["nan", "none"]:
        return f"{endereco}, {municipio}, Alagoas, Brasil"

    return f"{local}, {municipio}, Alagoas, Brasil"


def criar_locais_unicos(mapa):
    mapa["votos"] = pd.to_numeric(mapa["votos"], errors="coerce").fillna(0).astype(int)

    locais = (
        mapa.groupby(
            [
                "municipio",
                "local_votacao",
                "endereco_local_votacao",
            ],
            as_index=False,
        )
        .agg(
            qtd_secoes=("secao", "nunique"),
            qtd_vereadores=("vereador", "nunique"),
            votos_totais=("votos", "sum"),
        )
    )

    locais["chave_local"] = locais.apply(montar_chave_local, axis=1)

    locais = locais.sort_values(
        ["municipio", "votos_totais"],
        ascending=[True, False],
    )

    return locais


def carregar_cache():
    if CACHE_GEOCODIFICACAO.exists():
        cache = ler_csv(CACHE_GEOCODIFICACAO)

        colunas = [
            "chave_local",
            "latitude",
            "longitude",
            "bairro",
            "distrito",
            "status_geocodificacao",
            "consulta_geocoding",
        ]

        for col in colunas:
            if col not in cache.columns:
                cache[col] = ""

        return cache[colunas].drop_duplicates(subset=["chave_local"])

    return pd.DataFrame(
        columns=[
            "chave_local",
            "latitude",
            "longitude",
            "bairro",
            "distrito",
            "status_geocodificacao",
            "consulta_geocoding",
        ]
    )


def salvar_cache(cache):
    cache.to_csv(
        CACHE_GEOCODIFICACAO,
        sep=";",
        index=False,
        encoding="utf-8-sig",
    )


def geocodificar_nominatim(locais, cache, limite=None):
    try:
        from geopy.geocoders import Nominatim
        from geopy.extra.rate_limiter import RateLimiter
    except ImportError:
        print("\nAVISO: biblioteca geopy não instalada.")
        print("Execute: pip install geopy")
        print("O script seguirá sem geocodificação automática.")
        return cache

    geolocator = Nominatim(
        user_agent="alagoas_political_intelligence_etl017"
    )

    geocode = RateLimiter(
        geolocator.geocode,
        min_delay_seconds=1.2,
        max_retries=2,
        error_wait_seconds=3,
        swallow_exceptions=True,
    )

    chaves_cache = set(cache["chave_local"].astype(str).tolist())

    pendentes = locais[~locais["chave_local"].isin(chaves_cache)].copy()

    if limite:
        pendentes = pendentes.head(limite)

    print(f"\nLocais únicos totais: {len(locais):,}".replace(",", "."))
    print(f"Locais já no cache: {len(chaves_cache):,}".replace(",", "."))
    print(f"Locais pendentes para geocodificar: {len(pendentes):,}".replace(",", "."))

    novos = []

    for idx, row in pendentes.iterrows():
        municipio = row["municipio"]
        local = row["local_votacao"]
        endereco = row["endereco_local_votacao"]

        consulta = montar_consulta_geocoding(municipio, endereco, local)

        print(f"Geocodificando: {municipio} | {local}")

        latitude = ""
        longitude = ""
        bairro = ""
        distrito = ""
        status = "NAO_ENCONTRADO"

        location = geocode(consulta, addressdetails=True, country_codes="br")

        if location:
            latitude = location.latitude
            longitude = location.longitude
            status = "ENCONTRADO"

            raw = location.raw or {}
            address = raw.get("address", {})

            bairro = (
                address.get("suburb")
                or address.get("neighbourhood")
                or address.get("city_district")
                or address.get("quarter")
                or ""
            )

            distrito = (
                address.get("district")
                or address.get("county")
                or address.get("municipality")
                or ""
            )

        novos.append(
            {
                "chave_local": row["chave_local"],
                "latitude": latitude,
                "longitude": longitude,
                "bairro": bairro,
                "distrito": distrito,
                "status_geocodificacao": status,
                "consulta_geocoding": consulta,
            }
        )

        cache_atualizado = pd.concat(
            [cache, pd.DataFrame(novos)],
            ignore_index=True,
        ).drop_duplicates(subset=["chave_local"], keep="last")

        salvar_cache(cache_atualizado)

        time.sleep(0.2)

    cache_final = pd.concat(
        [cache, pd.DataFrame(novos)],
        ignore_index=True,
    ).drop_duplicates(subset=["chave_local"], keep="last")

    salvar_cache(cache_final)

    return cache_final


def main():
    print("=" * 70)
    print("ETL 017 — GEORREFERENCIAMENTO DAS SEÇÕES ELEITORAIS TOP 10")
    print("=" * 70)

    if not ENTRADA.exists():
        raise FileNotFoundError(
            f"Arquivo de entrada não encontrado: {ENTRADA}\n"
            "Execute antes o ETL 016."
        )

    print(f"\nLendo entrada: {ENTRADA}")
    mapa = ler_csv(ENTRADA)

    colunas_necessarias = [
        "municipio",
        "vereador",
        "partido",
        "zona",
        "secao",
        "votos",
        "percentual",
        "local_votacao",
        "endereco_local_votacao",
        "prioridade_territorial",
        "potencial_transferencia_local",
    ]

    faltantes = [col for col in colunas_necessarias if col not in mapa.columns]

    if faltantes:
        print("\nColunas encontradas:")
        for col in mapa.columns:
            print(f"- {col}")

        raise ValueError(f"Colunas obrigatórias ausentes: {faltantes}")

    print(f"Linhas carregadas: {len(mapa):,}".replace(",", "."))

    print("\nConsolidando locais únicos de votação...")
    locais = criar_locais_unicos(mapa)

    locais.to_csv(
        SAIDA_LOCAIS,
        sep=";",
        index=False,
        encoding="utf-8-sig",
    )

    print(f"Locais únicos gerados: {len(locais):,}".replace(",", "."))
    print(f"Arquivo gerado: {SAIDA_LOCAIS}")

    print("\nCarregando cache de geocodificação...")
    cache = carregar_cache()

    # Por segurança, esta primeira execução geocodifica no máximo 50 locais.
    # Depois que validar, altere limite=50 para limite=None.
    cache = geocodificar_nominatim(locais, cache, limite=None)

    locais_geo = locais.merge(
        cache,
        how="left",
        on="chave_local",
    )

    mapa["chave_local"] = mapa.apply(montar_chave_local, axis=1)

    mapa_geo = mapa.merge(
        locais_geo[
            [
                "chave_local",
                "latitude",
                "longitude",
                "bairro",
                "distrito",
                "status_geocodificacao",
                "consulta_geocoding",
                "qtd_secoes",
                "qtd_vereadores",
                "votos_totais",
            ]
        ],
        how="left",
        on="chave_local",
    )

    mapa_geo = mapa_geo.rename(
        columns={
            "qtd_secoes": "qtd_secoes_local",
            "qtd_vereadores": "qtd_vereadores_local",
            "votos_totais": "votos_totais_local",
        }
    )

    mapa_geo = mapa_geo[
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
            "latitude",
            "longitude",
            "bairro",
            "distrito",
            "status_geocodificacao",
            "consulta_geocoding",
            "qtd_secoes_local",
            "qtd_vereadores_local",
            "votos_totais_local",
            "total_votos_vereador_municipio",
            "total_secoes_com_votos",
        ]
    ]

    mapa_geo.to_csv(
        SAIDA_GEOGRAFICO,
        sep=";",
        index=False,
        encoding="utf-8-sig",
    )

    print("\n" + "=" * 70)
    print("ETL 017 CONCLUÍDO")
    print("=" * 70)
    print(f"Arquivo gerado: {SAIDA_LOCAIS}")
    print(f"Arquivo gerado: {SAIDA_GEOGRAFICO}")
    print(f"Cache gerado/atualizado: {CACHE_GEOCODIFICACAO}")
    print(f"Linhas no mapa geográfico: {len(mapa_geo):,}".replace(",", "."))

    if "status_geocodificacao" in mapa_geo.columns:
        print("\nStatus de geocodificação:")
        print(
            mapa_geo["status_geocodificacao"]
            .fillna("SEM_GEOCODIFICACAO")
            .value_counts()
            .to_string()
        )


if __name__ == "__main__":
    main()