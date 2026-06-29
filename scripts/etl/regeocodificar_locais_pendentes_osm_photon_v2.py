# scripts/etl/regeocodificar_locais_pendentes_osm_photon_v2.py

import time
from pathlib import Path

import pandas as pd
import requests


BASE_DIR = Path(__file__).resolve().parents[2]

DATA_REFERENCE = BASE_DIR / "data" / "reference"
CURADORIA_DIR = BASE_DIR / "data" / "curadoria"
AUDIT_DIR = BASE_DIR / "data" / "audit"

CURADORIA_DIR.mkdir(parents=True, exist_ok=True)
AUDIT_DIR.mkdir(parents=True, exist_ok=True)

CACHE_ORIGINAL = DATA_REFERENCE / "cache_geocodificacao_locais_top10.csv"

OUT_CACHE_V3 = DATA_REFERENCE / "cache_geocodificacao_locais_top10_v3.csv"
OUT_RESULTADO = CURADORIA_DIR / "resultado_regeocodificacao_osm_photon_v2.csv"
OUT_LOG = AUDIT_DIR / "log_regeocodificacao_osm_photon_v2.csv"

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
PHOTON_URL = "https://photon.komoot.io/api/"

HEADERS = {
    "User-Agent": "alagoas-political-intelligence/1.0"
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
    municipio = partes[0].strip() if len(partes) > 0 else ""
    local = partes[1].strip() if len(partes) > 1 else ""
    endereco = partes[2].strip() if len(partes) > 2 else ""
    return municipio, local, endereco


def limpar_sn(valor: str) -> str:
    texto = str(valor or "")
    texto = texto.replace("S/N", "")
    texto = texto.replace("SN", "")
    texto = texto.replace("S N", "")
    texto = " ".join(texto.split())
    return texto.strip(" ,-")


def simplificar_local(local: str) -> str:
    texto = str(local or "")
    termos_remover = [
        "ESCOLA DE ENSINO FUNDAMENTAL",
        "ESCOLA ENSINO FUNDAMENTAL",
        "ESCOLA ESTADUAL",
        "ESCOLA MUNICIPAL",
        "COLÉGIO ESTADUAL",
        "COLEGIO ESTADUAL",
        "GRUPO ESCOLAR",
        "COMPLEXO ESTADUAL",
        "E.E.",
        "E.M.",
        "ESC.",
        "EST.",
        "PROFª.",
        "PROFA.",
        "PROF.",
        "DR.",
        "DRA.",
    ]

    texto_upper = texto.upper()

    for termo in termos_remover:
        texto_upper = texto_upper.replace(termo, " ")

    texto_upper = " ".join(texto_upper.split())
    return texto_upper.strip()


def montar_consultas(municipio: str, local: str, endereco: str) -> list[tuple[str, str]]:
    endereco_limpo = limpar_sn(endereco)
    local_simplificado = simplificar_local(local)

    consultas = []

    if local and endereco and municipio:
        consultas.append(("OSM_COMPLETA", f"{local}, {endereco}, {municipio}, Alagoas, Brasil"))

    if local and endereco_limpo and municipio:
        consultas.append(("OSM_COMPLETA_SEM_SN", f"{local}, {endereco_limpo}, {municipio}, Alagoas, Brasil"))

    if local and municipio:
        consultas.append(("OSM_LOCAL_MUNICIPIO", f"{local}, {municipio}, Alagoas, Brasil"))

    if local_simplificado and municipio:
        consultas.append(("OSM_LOCAL_SIMPLIFICADO", f"{local_simplificado}, {municipio}, Alagoas, Brasil"))

    if endereco_limpo and municipio:
        consultas.append(("OSM_ENDERECO_MUNICIPIO", f"{endereco_limpo}, {municipio}, Alagoas, Brasil"))

    if local and municipio:
        consultas.append(("PHOTON_LOCAL_MUNICIPIO", f"{local}, {municipio}, Alagoas, Brasil"))

    if local_simplificado and municipio:
        consultas.append(("PHOTON_LOCAL_SIMPLIFICADO", f"{local_simplificado}, {municipio}, Alagoas, Brasil"))

    if endereco_limpo and municipio:
        consultas.append(("PHOTON_ENDERECO_MUNICIPIO", f"{endereco_limpo}, {municipio}, Alagoas, Brasil"))

    return consultas


def consultar_osm(query: str):
    params = {
        "q": query,
        "format": "json",
        "limit": 1,
        "addressdetails": 1,
        "countrycodes": "br",
    }

    try:
        r = requests.get(NOMINATIM_URL, params=params, headers=HEADERS, timeout=30)
        if r.status_code != 200:
            return None, f"HTTP_{r.status_code}"

        data = r.json()
        if not data:
            return None, "SEM_RESULTADO"

        item = data[0]
        return {
            "latitude": item.get("lat", ""),
            "longitude": item.get("lon", ""),
            "bairro": extrair_bairro_osm(item),
            "display_name": item.get("display_name", ""),
            "fonte": "OSM_NOMINATIM",
        }, "ENCONTRADO"

    except Exception as erro:
        return None, f"ERRO_{type(erro).__name__}"


def consultar_photon(query: str):
    params = {
        "q": query,
        "limit": 1,
        "lang": "pt",
    }

    try:
        r = requests.get(PHOTON_URL, params=params, headers=HEADERS, timeout=30)
        if r.status_code != 200:
            return None, f"HTTP_{r.status_code}"

        data = r.json()
        features = data.get("features", [])

        if not features:
            return None, "SEM_RESULTADO"

        item = features[0]
        props = item.get("properties", {})
        coords = item.get("geometry", {}).get("coordinates", [])

        if len(coords) < 2:
            return None, "SEM_COORDENADAS"

        longitude = coords[0]
        latitude = coords[1]

        bairro = (
            props.get("district")
            or props.get("suburb")
            or props.get("locality")
            or props.get("neighbourhood")
            or ""
        )

        display = ", ".join(
            str(x) for x in [
                props.get("name", ""),
                props.get("street", ""),
                props.get("city", ""),
                props.get("state", ""),
                props.get("country", ""),
            ] if x
        )

        return {
            "latitude": latitude,
            "longitude": longitude,
            "bairro": bairro,
            "display_name": display,
            "fonte": "PHOTON_KOMOOT",
        }, "ENCONTRADO"

    except Exception as erro:
        return None, f"ERRO_{type(erro).__name__}"


def extrair_bairro_osm(resultado: dict) -> str:
    address = resultado.get("address", {}) if resultado else {}

    for campo in ["suburb", "neighbourhood", "quarter", "city_district", "district"]:
        if address.get(campo):
            return address.get(campo)

    return ""


def vazio_ou_nulo(serie: pd.Series) -> pd.Series:
    return serie.isna() | (serie.astype(str).str.strip() == "")


def main():
    print()
    print("=" * 70)
    print("REGEOCODIFICAÇÃO V2 — OSM + PHOTON + CONSULTAS SIMPLIFICADAS")
    print("=" * 70)

    cache = carregar_csv(CACHE_ORIGINAL)

    for col in ["latitude", "longitude", "bairro", "distrito", "status_geocodificacao", "consulta_geocoding"]:
        if col not in cache.columns:
            cache[col] = ""

    pendentes = cache[
        vazio_ou_nulo(cache["latitude"]) |
        vazio_ou_nulo(cache["longitude"])
    ].copy()

    print(f"Total no cache original: {len(cache)}")
    print(f"Pendentes para geocodificar: {len(pendentes)}")

    logs = []
    resultados = []

    total = len(pendentes)

    for pos, (idx, row) in enumerate(pendentes.iterrows(), start=1):
        chave = row["chave_local"]
        municipio, local, endereco = separar_chave(chave)

        print()
        print(f"[{pos}/{total}] {municipio} | {local}")

        consultas = montar_consultas(municipio, local, endereco)

        encontrado = None
        consulta_usada = ""
        estrategia_usada = ""
        status_final = "NAO_ENCONTRADO_V2"

        for estrategia, consulta in consultas:
            print(f"  Tentando {estrategia}: {consulta}")

            if estrategia.startswith("OSM"):
                resultado, status = consultar_osm(consulta)
                time.sleep(1.2)
            else:
                resultado, status = consultar_photon(consulta)
                time.sleep(0.5)

            logs.append({
                "chave_local": chave,
                "municipio": municipio,
                "local": local,
                "endereco": endereco,
                "estrategia": estrategia,
                "consulta": consulta,
                "status": status,
            })

            if resultado:
                encontrado = resultado
                consulta_usada = consulta
                estrategia_usada = estrategia
                status_final = f"ENCONTRADO_{resultado['fonte']}"
                print("  -> Encontrado")
                break

            print(f"  -> {status}")

        if encontrado:
            cache.loc[idx, "latitude"] = encontrado["latitude"]
            cache.loc[idx, "longitude"] = encontrado["longitude"]
            cache.loc[idx, "bairro"] = encontrado["bairro"]
            cache.loc[idx, "status_geocodificacao"] = status_final
            cache.loc[idx, "consulta_geocoding"] = consulta_usada

            resultados.append({
                "chave_local": chave,
                "municipio": municipio,
                "local": local,
                "endereco": endereco,
                "latitude": encontrado["latitude"],
                "longitude": encontrado["longitude"],
                "bairro": encontrado["bairro"],
                "status": status_final,
                "fonte": encontrado["fonte"],
                "estrategia_usada": estrategia_usada,
                "consulta_usada": consulta_usada,
                "display_name": encontrado["display_name"],
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
                "status": "NAO_ENCONTRADO_V2",
                "fonte": "",
                "estrategia_usada": "",
                "consulta_usada": "",
                "display_name": "",
            })

    cache.to_csv(OUT_CACHE_V3, index=False, encoding="utf-8-sig")
    pd.DataFrame(resultados).to_csv(OUT_RESULTADO, index=False, encoding="utf-8-sig")
    pd.DataFrame(logs).to_csv(OUT_LOG, index=False, encoding="utf-8-sig")

    resultado_df = pd.DataFrame(resultados)

    print()
    print("=" * 70)
    print("RESULTADO FINAL")
    print("=" * 70)

    print(resultado_df["status"].value_counts(dropna=False).to_string())

    print()
    print("Arquivos gerados:")
    print(f"- {OUT_CACHE_V3}")
    print(f"- {OUT_RESULTADO}")
    print(f"- {OUT_LOG}")


if __name__ == "__main__":
    main()