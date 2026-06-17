from pathlib import Path
import csv
import time
import random
from datetime import datetime, date

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError


PROFILE_URL = "https://www.instagram.com/davimaialima/reels/"
ACCOUNT_NAME = "davi_maia"

DATA_INICIO = date(2026, 5, 1)

BASE_DIR = Path(__file__).resolve().parents[2]
OUTPUT_DIR = BASE_DIR / "data" / "social"

OUTPUT_CSV = OUTPUT_DIR / "davi_maia_reels_pre_campanha_2026.csv"

MAX_SCROLLS = 25
MAX_REELS_ANALISAR = 120


def salvar_csv(registros):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    with OUTPUT_CSV.open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "account",
                "reel_url",
                "data_postagem",
                "texto_extraido",
            ],
        )
        writer.writeheader()
        writer.writerows(registros)

    print(f"\nArquivo gerado: {OUTPUT_CSV}")
    print(f"Total de Reels no período: {len(registros)}")


def extrair_links_em_ordem(page):
    links = page.locator("a").evaluate_all(
        """
        elements => elements
            .map(a => a.href)
            .filter(href => href && href.includes('/reel/'))
        """
    )

    resultado = []
    vistos = set()

    for link in links:
        link = link.split("?")[0]

        if link not in vistos:
            vistos.add(link)
            resultado.append(link)

    return resultado


def extrair_data(page):
    try:
        valor = page.locator("time").first.get_attribute("datetime", timeout=10000)

        if valor:
            return datetime.fromisoformat(valor.replace("Z", "+00:00")).date()

    except Exception:
        return None

    return None


def extrair_texto(page):
    try:
        return page.locator("body").inner_text(timeout=15000)
    except Exception:
        return ""


def main():
    registros = []

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

        print("Abrindo perfil de Reels do Davi Maia...")
        page.goto(PROFILE_URL, wait_until="domcontentloaded", timeout=60000)

        print("\nFaça login, se necessário.")
        print("Depois cole esta URL no navegador aberto:")
        print(PROFILE_URL)

        input("\nQuando a página de Reels estiver aberta, pressione ENTER...")

        todos_links = []
        vistos = set()

        print("\nColetando links em ordem visual do perfil...")

        for scroll in range(1, MAX_SCROLLS + 1):
            links_pagina = extrair_links_em_ordem(page)

            novos = 0

            for link in links_pagina:
                if link not in vistos:
                    vistos.add(link)
                    todos_links.append(link)
                    novos += 1

            print(f"Scroll {scroll}/{MAX_SCROLLS} | Novos: {novos} | Total: {len(todos_links)}")

            page.mouse.wheel(0, random.randint(1200, 2200))
            time.sleep(random.uniform(4, 8))

            if len(todos_links) >= MAX_REELS_ANALISAR:
                break

        print(f"\nTotal de links coletados para checagem: {len(todos_links)}")
        print(f"Filtrando apenas posts a partir de {DATA_INICIO}...")

        datas_antigas_seguidas = 0

        for i, link in enumerate(todos_links, start=1):
            print(f"\n[{i}/{len(todos_links)}] {link}")

            try:
                page.goto(link, wait_until="domcontentloaded", timeout=60000)
                time.sleep(random.uniform(6, 10))

                data_postagem = extrair_data(page)

                if not data_postagem:
                    print("Data não encontrada. Pulando.")
                    continue

                print(f"Data: {data_postagem}")

                if data_postagem < DATA_INICIO:
                    datas_antigas_seguidas += 1
                    print("Fora do período. Ignorando.")

                    if datas_antigas_seguidas >= 8:
                        print("\nEncontrados 8 posts antigos seguidos. Encerrando análise.")
                        break

                    continue

                datas_antigas_seguidas = 0

                texto = extrair_texto(page)

                registros.append(
                    {
                        "account": ACCOUNT_NAME,
                        "reel_url": link,
                        "data_postagem": data_postagem.isoformat(),
                        "texto_extraido": texto[:3000],
                    }
                )

                print("Reel dentro do período salvo.")

            except PlaywrightTimeoutError:
                print("Timeout. Pulando.")
            except Exception as erro:
                print(f"Erro: {erro}")

            if i % 10 == 0:
                salvar_csv(registros)
                time.sleep(random.uniform(20, 35))

        browser.close()

    salvar_csv(registros)
    print("\nColeta de pré-campanha concluída.")


if __name__ == "__main__":
    main()