from pathlib import Path
import csv
import time
import random

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError


PROFILE_URL = "https://www.instagram.com/davimaialima/reels/"
ACCOUNT_NAME = "davi_maia"

BASE_DIR = Path(__file__).resolve().parents[2]
OUTPUT_DIR = BASE_DIR / "data" / "social"
OUTPUT_CSV = OUTPUT_DIR / "davi_maia_reels.csv"

MAX_SCROLLS = 80
WAIT_MIN = 4
WAIT_MAX = 8


def salvar_csv(links):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    with OUTPUT_CSV.open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.writer(file)
        writer.writerow(["account", "reel_url"])

        for link in sorted(links):
            writer.writerow([ACCOUNT_NAME, link])

    print(f"\nArquivo gerado: {OUTPUT_CSV}")
    print(f"Total de Reels capturados: {len(links)}")


def navegar_com_tolerancia(page, url):
    try:
        page.goto(url, wait_until="load", timeout=90000)
    except PlaywrightTimeoutError:
        print("Aviso: tempo de carregamento excedido, seguindo mesmo assim.")
    except Exception as erro:
        print(f"Aviso: navegação interrompida pelo Instagram: {erro}")
        print("Tentando continuar com a página atual...")


def extrair_links_reels(page):
    try:
        links = page.locator("a").evaluate_all(
            """
            elements => elements
                .map(a => a.href)
                .filter(href => href && href.includes('/reel/'))
            """
        )
    except Exception:
        return set()

    links_limpos = set()

    for link in links:
        link = link.split("?")[0]
        if "/reel/" in link:
            links_limpos.add(link)

    return links_limpos


def main():
    todos_links = set()

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            slow_mo=250,
        )

        context = browser.new_context(
            viewport={"width": 1366, "height": 768},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
        )

        page = context.new_page()

        print("Abrindo Instagram...")
        navegar_com_tolerancia(page, PROFILE_URL)

        print("\nSe o Instagram pedir login, faça login manualmente.")
        print("Depois que o login terminar, cole manualmente esta URL na barra do navegador aberto:")
        print(PROFILE_URL)
        print("\nQuando a página de Reels do Davi Maia estiver carregada, volte ao terminal.")
        input("Pressione ENTER para iniciar a coleta...")

        time.sleep(5)

        print("\nIniciando coleta de links dos Reels...")

        for scroll in range(1, MAX_SCROLLS + 1):
            novos_links = extrair_links_reels(page)
            quantidade_antes = len(todos_links)

            todos_links.update(novos_links)

            quantidade_depois = len(todos_links)
            capturados_agora = quantidade_depois - quantidade_antes

            print(
                f"Scroll {scroll}/{MAX_SCROLLS} | "
                f"Novos: {capturados_agora} | "
                f"Total: {quantidade_depois}"
            )

            page.mouse.wheel(0, random.randint(1200, 2200))
            time.sleep(random.uniform(WAIT_MIN, WAIT_MAX))

            if scroll % 10 == 0:
                print("Pausa curta para reduzir risco de bloqueio...")
                time.sleep(random.uniform(15, 25))

        salvar_csv(todos_links)

        print("\nColeta finalizada.")
        browser.close()


if __name__ == "__main__":
    main()