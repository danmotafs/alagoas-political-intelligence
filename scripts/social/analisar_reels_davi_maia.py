from pathlib import Path
import time
import random
from datetime import datetime, date

import pandas as pd
from playwright.sync_api import sync_playwright


DATA_CORTE = date(2026, 5, 1)

BASE_DIR = Path(__file__).resolve().parents[2]

INPUT_CSV = BASE_DIR / "data" / "social" / "davi_maia_reels.csv"
OUTPUT_CSV = BASE_DIR / "data" / "social" / "davi_maia_reels_pre_campanha_2026.csv"

MAX_REELS = 150


def extrair_data(page):
    try:
        page.wait_for_selector("time", timeout=15000)

        valor = page.locator("time").first.get_attribute("datetime")

        if not valor:
            return None

        return datetime.fromisoformat(
            valor.replace("Z", "+00:00")
        ).date()

    except Exception:
        return None


def extrair_legenda(page):
    try:
        texto = page.locator("body").inner_text(timeout=10000)
        return texto[:5000]
    except Exception:
        return ""


def salvar_checkpoint(resultados):
    pd.DataFrame(resultados).to_csv(
        OUTPUT_CSV,
        index=False,
        encoding="utf-8-sig"
    )


def main():

    if not INPUT_CSV.exists():
        raise FileNotFoundError(INPUT_CSV)

    df = pd.read_csv(INPUT_CSV)

    links = df["reel_url"].dropna().tolist()

    # CORREÇÃO PRINCIPAL
    links = list(reversed(links))

    print(f"Links encontrados: {len(links)}")
    print("Processando do mais recente para o mais antigo")

    resultados = []

    antigos_seguidos = 0

    with sync_playwright() as p:

        browser = p.chromium.launch(
            headless=False,
            slow_mo=250
        )

        context = browser.new_context(
            viewport={"width": 1366, "height": 768}
        )

        page = context.new_page()

        page.goto(
            "https://www.instagram.com/",
            wait_until="domcontentloaded"
        )

        print("\nFaça login no Instagram.")
        input("Após login pressione ENTER...")

        for indice, link in enumerate(links[:MAX_REELS], start=1):

            print("\n====================================")
            print(f"[{indice}/{MAX_REELS}]")
            print(link)

            try:

                page.goto(
                    link,
                    wait_until="domcontentloaded",
                    timeout=60000
                )

                time.sleep(random.uniform(4, 8))

                data_postagem = extrair_data(page)

                if not data_postagem:
                    print("Data não encontrada.")
                    continue

                print(f"Data: {data_postagem}")

                if data_postagem < DATA_CORTE:

                    antigos_seguidos += 1

                    print(
                        f"Anterior a {DATA_CORTE} "
                        f"(sequência={antigos_seguidos})"
                    )

                    if antigos_seguidos >= 8:

                        print(
                            "\nEncontrados 8 posts antigos consecutivos."
                        )

                        print(
                            "Encerrando análise."
                        )

                        break

                    continue

                antigos_seguidos = 0

                legenda = extrair_legenda(page)

                resultados.append(
                    {
                        "data_postagem": data_postagem.isoformat(),
                        "reel_url": link,
                        "texto": legenda
                    }
                )

                print("Reel dentro do período.")

            except Exception as erro:

                print(f"Erro: {erro}")

            if indice % 10 == 0:

                salvar_checkpoint(resultados)

                print(
                    f"Checkpoint salvo "
                    f"({len(resultados)} reels válidos)"
                )

                time.sleep(random.uniform(15, 30))

        browser.close()

    salvar_checkpoint(resultados)

    print("\n====================================")
    print("ANÁLISE FINALIZADA")
    print("====================================")
    print(f"Reels encontrados no período: {len(resultados)}")
    print(f"Arquivo gerado: {OUTPUT_CSV}")


if __name__ == "__main__":
    main()