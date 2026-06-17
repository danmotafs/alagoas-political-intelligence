from pathlib import Path
import csv
import time
import random
import unicodedata
from datetime import datetime, date

import pandas as pd
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError


BASE_DIR = Path(__file__).resolve().parents[2]

REELS_CSV = BASE_DIR / "data" / "social" / "davi_maia_reels.csv"
MUNICIPIOS_CSV = BASE_DIR / "data" / "final" / "ranking_estrategico_alagoas_2024.csv"

OUTPUT_METADATA = BASE_DIR / "data" / "social" / "davi_maia_reels_metadata.csv"
OUTPUT_PRESENCA = BASE_DIR / "data" / "social" / "davi_maia_presenca_territorial_2026.csv"

DATA_INICIO_PRE_CAMPANHA = date(2026, 5, 1)

WAIT_MIN = 8
WAIT_MAX = 14


def normalizar_texto(texto: str) -> str:
    if pd.isna(texto):
        return ""

    texto = str(texto).strip().upper()
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    return texto


def carregar_municipios() -> list[str]:
    df = pd.read_csv(MUNICIPIOS_CSV)
    return sorted(df["municipio"].dropna().unique().tolist())


def carregar_links() -> list[str]:
    df = pd.read_csv(REELS_CSV)

    if "reel_url" not in df.columns:
        raise KeyError("Coluna 'reel_url' não encontrada em davi_maia_reels.csv")

    links = df["reel_url"].dropna().drop_duplicates().tolist()
    return links


def extrair_data(page):
    try:
        datetime_value = page.locator("time").first.get_attribute("datetime", timeout=10000)
        if datetime_value:
            return datetime.fromisoformat(datetime_value.replace("Z", "+00:00")).date()
    except Exception:
        return None

    return None


def extrair_texto_visivel(page) -> str:
    try:
        texto = page.locator("body").inner_text(timeout=15000)
        return texto
    except Exception:
        return ""


def identificar_municipios(texto: str, municipios: list[str]) -> list[str]:
    texto_norm = normalizar_texto(texto)
    encontrados = []

    for municipio in municipios:
        municipio_norm = normalizar_texto(municipio)

        if municipio_norm in texto_norm:
            encontrados.append(municipio)

    return sorted(set(encontrados))


def salvar_metadata(linhas: list[dict]) -> None:
    OUTPUT_METADATA.parent.mkdir(parents=True, exist_ok=True)

    df = pd.DataFrame(linhas)
    df.to_csv(OUTPUT_METADATA, index=False, encoding="utf-8-sig")

    print(f"\nMetadata salva em: {OUTPUT_METADATA}")


def gerar_presenca_territorial(linhas: list[dict]) -> None:
    registros = []

    for linha in linhas:
        data_postagem = linha.get("data_postagem")
        municipios = linha.get("municipios_identificados", "")

        if not data_postagem or not municipios:
            continue

        try:
            data_obj = datetime.strptime(data_postagem, "%Y-%m-%d").date()
        except ValueError:
            continue

        if data_obj < DATA_INICIO_PRE_CAMPANHA:
            continue

        for municipio in municipios.split("|"):
            municipio = municipio.strip()

            if not municipio:
                continue

            registros.append(
                {
                    "municipio": municipio,
                    "data_postagem": data_postagem,
                    "reel_url": linha.get("reel_url"),
                    "fonte": "Instagram/Reels",
                }
            )

    if not registros:
        df_vazio = pd.DataFrame(
            columns=[
                "municipio",
                "quantidade_registros",
                "primeira_ocorrencia",
                "ultima_ocorrencia",
                "links_reels",
                "fonte",
            ]
        )
        df_vazio.to_csv(OUTPUT_PRESENCA, index=False, encoding="utf-8-sig")
        print("\nNenhum município identificado no período.")
        return

    df = pd.DataFrame(registros)

    resumo = (
        df.groupby("municipio")
        .agg(
            quantidade_registros=("municipio", "count"),
            primeira_ocorrencia=("data_postagem", "min"),
            ultima_ocorrencia=("data_postagem", "max"),
            links_reels=("reel_url", lambda x: " | ".join(sorted(set(x)))),
        )
        .reset_index()
        .sort_values(["quantidade_registros", "ultima_ocorrencia"], ascending=[False, False])
    )

    resumo["fonte"] = "Instagram/Reels"
    resumo.to_csv(OUTPUT_PRESENCA, index=False, encoding="utf-8-sig")

    print(f"Presença territorial salva em: {OUTPUT_PRESENCA}")
    print("\nMunicípios identificados no período de pré-campanha:")
    print(resumo.to_string(index=False))


def main():
    municipios = carregar_municipios()
    links = carregar_links()

    print(f"Municípios de referência: {len(municipios)}")
    print(f"Reels para analisar: {len(links)}")
    print(f"Filtro de data: a partir de {DATA_INICIO_PRE_CAMPANHA}")

    linhas = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=250)

        context = browser.new_context(
            viewport={"width": 1366, "height": 768},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
        )

        page = context.new_page()

        print("\nAbrindo Instagram...")
        page.goto("https://www.instagram.com/", wait_until="domcontentloaded", timeout=60000)

        print("\nFaça login, se necessário.")
        input("Quando estiver logado, pressione ENTER para iniciar a análise dos Reels...")

        for i, link in enumerate(links, start=1):
            print(f"\n[{i}/{len(links)}] Analisando: {link}")

            data_postagem = None
            texto = ""
            municipios_identificados = []

            try:
                page.goto(link, wait_until="domcontentloaded", timeout=60000)
                time.sleep(random.uniform(WAIT_MIN, WAIT_MAX))

                data_postagem = extrair_data(page)
                texto = extrair_texto_visivel(page)
                municipios_identificados = identificar_municipios(texto, municipios)

            except PlaywrightTimeoutError:
                print("Timeout. Pulando Reel.")
            except Exception as erro:
                print(f"Erro ao analisar Reel: {erro}")

            data_formatada = data_postagem.isoformat() if data_postagem else ""

            print(f"Data: {data_formatada}")
            print(f"Municípios: {', '.join(municipios_identificados) if municipios_identificados else 'nenhum'}")

            linhas.append(
                {
                    "reel_url": link,
                    "data_postagem": data_formatada,
                    "municipios_identificados": "|".join(municipios_identificados),
                    "texto_extraido": texto[:3000],
                }
            )

            if i % 15 == 0:
                salvar_metadata(linhas)
                print("Pausa maior para reduzir risco de bloqueio...")
                time.sleep(random.uniform(30, 60))

        browser.close()

    salvar_metadata(linhas)
    gerar_presenca_territorial(linhas)

    print("\nAnálise concluída.")


if __name__ == "__main__":
    main()