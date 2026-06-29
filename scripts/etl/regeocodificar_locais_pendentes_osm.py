# scripts/etl/regeocodificar_locais_pendentes_osm.py

import time
import requests
import pandas as pd
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[2]

DATA_REFERENCE = BASE_DIR / "data" / "reference"
CURADORIA_DIR = BASE_DIR / "data" / "curadoria"
AUDIT_DIR = BASE_DIR / "data" / "audit"

CURADORIA_DIR.mkdir(parents=True, exist_ok=True)
AUDIT_DIR.mkdir(parents=True, exist_ok=True)

CACHE_PATH = DATA_REFERENCE / "cache_geocodificacao_locais_top10.csv"

OUT_CACHE_V2 = DATA_REFERENCE / "cache_geocodificacao_locais_top10_v2.csv"
OUT_RESULTADO = CURADORIA_DIR / "resultado_regeocodificacao_osm.csv"
OUT_LOG = AUDIT_DIR / "log_regeocodificacao_osm.csv"


NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"

HEADERS = {
    "User-Agent": "alagoas-political-intelligence/1.0 (curadoria territorial eleitoral)"
}


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


def montar_consultas(municipio: str, local: str, endereco: str) -> list[str]:
    consultas = []

    if local and endereco and municipio:
        consultas.append(f"{local}, {endereco}, {municipio}, Alagoas, Brasil")

    if local and municipio:
        consultas.append(f"{local}, {municipio}, Alagoas, Brasil")

    if endereco and municipio:
        consultas.append(f"{endereco}, {municipio}, Alagoas, Brasil")

    if local:
        consultas.append(f"{local}, Alagoas, Brasil")

    return consultas


def consultar_nominatim(query: str):
    params = {
        "q": query,
        "format": "json",
        "limit": 1,
        "addressdetails": 1,
        "countrycodes": "br",
    }

    try:
        response = requests.get(
            NOMINATIM_URL,
            params=params,
            headers=HEADERS,
            timeout=30
        )

        if response.status_code != 200:
            return None, f"HTTP_{response.status_code}"

        data = response.json()

        if not data:
            return None, "SEM_RESULTADO"

        return data[0], "ENCONTRADO"

    except Exception as erro:
        return None, f"ERRO_{type(erro).__name__}"


def extrair_bairro(resultado: dict) -> str:
    address = resultado.get("address", {}) if resultado else {}

    for campo in ["suburb", "neighbourhood", "quarter", "city_district", "district"]:
        if campo in address and address[campo]:
            return address[campo]

    return ""


def main():
    print()
    print("=" * 70)
    print("REGEOCODIFICAÇÃO AUTOMÁTICA — OPENSTREETMAP/NOMINATIM")
    print("=" * 70)

    cache = carregar_csv(CACHE_PATH)

    for col in ["latitude", "longitude", "bairro", "distrito", "status_geocodificacao", "consulta_geocoding"]:
        if col not in cache.columns:
            cache[col] = ""

    pendentes = cache[
        cache["latitude"].isna() |
        cache["longitude"].isna() |
        (cache["latitude"].astype(str).str.strip() == "") |
        (cache["longitude"].astype(str).str.strip() == "")
    ].copy()

    print(f"Total no cache: {len(cache)}")
    print(f"Pendentes para geocodificar: {len(pendentes)}")

    logs = []
    resultados = []

    for idx, row in pendentes.iterrows():
        chave = row["chave_local"]
        municipio, local, endereco = separar_chave(chave)

        consultas = montar_consultas(municipio, local, endereco)

        encontrado = None
        status_final = "NAO_ENCONTRADO"
        consulta_usada = ""

        print()
        print(f"[{len(resultados) + 1}/{len(pendentes)}] {municipio} | {local}")

        for consulta in consultas:
            print(f"  Tentando: {consulta}")

            resultado, status = consultar_nominatim(consulta)

            logs.append({
                "chave_local": chave,
                "municipio": municipio,
                "local": local,
                "endereco": endereco,
                "consulta": consulta,
                "status": status,
            })

            time.sleep(1.2)

            if resultado:
                encontrado = resultado
                status_final = "ENCONTRADO_OSM"
                consulta_usada = consulta
                print("  -> Encontrado")
                break
            else:
                print(f"  -> {status}")

        if encontrado:
            lat = encontrado.get("lat", "")
            lon = encontrado.get("lon", "")
            bairro = extrair_bairro(encontrado)
            display_name = encontrado.get("display_name", "")

            cache.loc[idx, "latitude"] = lat
            cache.loc[idx, "longitude"] = lon
            cache.loc[idx, "bairro"] = bairro
            cache.loc[idx, "status_geocodificacao"] = status_final
            cache.loc[idx, "consulta_geocoding"] = consulta_usada

            resultados.append({
                "chave_local": chave,
                "municipio": municipio,
                "local": local,
                "endereco": endereco,
                "latitude": lat,
                "longitude": lon,
                "bairro": bairro,
                "status": status_final,
                "consulta_usada": consulta_usada,
                "display_name": display_name,
            })
        else:
            resultados.append({
                "chave_local": chave,
                "municipio": municipio,
                "local": local,
                "endereco": endereco,
                "latitude": "",
                "longitude": "",
                "bairro": "",
                "status": "NAO_ENCONTRADO_OSM",
                "consulta_usada": "",
                "display_name": "",
            })

    cache.to_csv(OUT_CACHE_V2, index=False, encoding="utf-8-sig")
    pd.DataFrame(resultados).to_csv(OUT_RESULTADO, index=False, encoding="utf-8-sig")
    pd.DataFrame(logs).to_csv(OUT_LOG, index=False, encoding="utf-8-sig")

    total_encontrados = sum(1 for r in resultados if r["status"] == "ENCONTRADO_OSM")
    total_nao_encontrados = sum(1 for r in resultados if r["status"] == "NAO_ENCONTRADO_OSM")

    print()
    print("=" * 70)
    print("RESULTADO FINAL")
    print("=" * 70)
    print(f"Pendentes processados: {len(pendentes)}")
    print(f"Encontrados no OSM: {total_encontrados}")
    print(f"Não encontrados: {total_nao_encontrados}")

    print()
    print("Arquivos gerados:")
    print(f"- {OUT_CACHE_V2}")
    print(f"- {OUT_RESULTADO}")
    print(f"- {OUT_LOG}")


if __name__ == "__main__":
    main()