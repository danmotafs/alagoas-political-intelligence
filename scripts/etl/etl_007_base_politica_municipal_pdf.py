from pathlib import Path
import re
import unicodedata

import pdfplumber
import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[2]

PDF_DIR = BASE_DIR / "data" / "Relatorio_Resultado_Totalizacao_2024_AL"

OUTPUT_CSV = BASE_DIR / "data" / "final" / "base_politica_municipal_2024.csv"
OUTPUT_XLSX = BASE_DIR / "data" / "final" / "base_politica_municipal_2024.xlsx"


PARTIDOS = {
    "10": "REPUBLICANOS",
    "11": "PP",
    "12": "PDT",
    "13": "PT",
    "15": "MDB",
    "20": "PODE",
    "22": "PL",
    "25": "PRD",
    "28": "PRTB",
    "30": "NOVO",
    "33": "MOBILIZA",
    "36": "AGIR",
    "40": "PSB",
    "43": "PV",
    "44": "UNIÃO",
    "45": "PSDB",
    "50": "PSOL",
    "55": "PSD",
    "65": "PCdoB",
    "70": "AVANTE",
    "77": "SOLIDARIEDADE",
}


def normalizar(texto: str) -> str:
    texto = str(texto).upper().strip()
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    return texto


def municipio_arquivo(nome_arquivo: str) -> str:
    nome = nome_arquivo.replace(".pdf", "")
    partes = nome.split("_")
    municipio = "_".join(partes[2:-2])
    return municipio.replace("-", " ").title()


def extrair_texto_pdf(pdf_path: Path) -> str:
    texto_total = ""

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            texto = page.extract_text()
            if texto:
                texto_total += "\n" + texto

    return texto_total


def localizar_bloco_anexo_ix_prefeito(texto: str) -> str | None:
    marcador = "Anexo IX - Resultado de votação"
    inicio = texto.find(marcador)

    while inicio != -1:
        trecho = texto[inicio:inicio + 5000]

        if "Cargo: Prefeito" in trecho:
            fim = trecho.find("Resultado em")
            if fim != -1:
                return trecho[:fim]

            return trecho

        inicio = texto.find(marcador, inicio + 1)

    return None


def limpar_nome(nome: str) -> str:
    nome = re.sub(r"\s+", " ", nome).strip()
    return nome


def parse_linha_candidato(linha: str) -> dict | None:
    padrao = (
        r"^\*?(\d{2})\s*-\s*(.*?)\s+"
        r"([\d\.]+)\s+"
        r"(\d+,\d+)%\s+"
        r"Válido\s+"
        r"(Eleito|Não eleito)"
    )

    match = re.search(padrao, linha, flags=re.I)

    if not match:
        return None

    numero = match.group(1)
    nome = limpar_nome(match.group(2))
    votos = int(match.group(3).replace(".", ""))
    percentual = float(match.group(4).replace(",", "."))
    situacao = match.group(5)

    return {
        "numero": numero,
        "nome": nome,
        "partido": PARTIDOS.get(numero, numero),
        "votos": votos,
        "percentual": percentual,
        "situacao": situacao,
    }


def extrair_candidatos_prefeito(bloco: str) -> list[dict]:
    linhas = [linha.strip() for linha in bloco.splitlines() if linha.strip()]
    candidatos = []

    i = 0

    while i < len(linhas):
        linha = linhas[i]

        candidato = parse_linha_candidato(linha)

        if candidato:
            vice = ""

            if i + 1 < len(linhas):
                proxima = linhas[i + 1].strip()

                if not re.match(r"^\*?\d{2}\s*-\s*", proxima):
                    if "Cargo:" not in proxima and "Resultado em" not in proxima:
                        vice = limpar_nome(proxima)

            candidato["vice"] = vice
            candidatos.append(candidato)

        i += 1

    return candidatos


def processar_pdf(pdf_path: Path) -> dict:
    municipio = municipio_arquivo(pdf_path.name)
    texto = extrair_texto_pdf(pdf_path)

    bloco = localizar_bloco_anexo_ix_prefeito(texto)

    if not bloco:
        return {
            "municipio": municipio,
            "prefeito": None,
            "vice_prefeito": None,
            "partido": None,
            "numero": None,
            "votos_prefeito": None,
            "percentual_prefeito": None,
            "segundo_colocado": None,
            "partido_segundo_colocado": None,
            "votos_segundo_colocado": None,
            "percentual_segundo_colocado": None,
            "margem_vitoria_votos": None,
            "margem_vitoria_pct": None,
            "status_extracao": "ANEXO_IX_NAO_ENCONTRADO",
            "arquivo_origem": pdf_path.name,
        }

    candidatos = extrair_candidatos_prefeito(bloco)

    if not candidatos:
        return {
            "municipio": municipio,
            "prefeito": None,
            "vice_prefeito": None,
            "partido": None,
            "numero": None,
            "votos_prefeito": None,
            "percentual_prefeito": None,
            "segundo_colocado": None,
            "partido_segundo_colocado": None,
            "votos_segundo_colocado": None,
            "percentual_segundo_colocado": None,
            "margem_vitoria_votos": None,
            "margem_vitoria_pct": None,
            "status_extracao": "CANDIDATO_NAO_ENCONTRADO",
            "arquivo_origem": pdf_path.name,
        }

    candidatos = sorted(candidatos, key=lambda x: x["votos"], reverse=True)

    eleito = next(
        (c for c in candidatos if normalizar(c["situacao"]) == "ELEITO"),
        candidatos[0],
    )

    segundo = None
    for candidato in candidatos:
        if candidato["nome"] != eleito["nome"]:
            segundo = candidato
            break

    if segundo:
        margem_votos = eleito["votos"] - segundo["votos"]
        margem_pct = eleito["percentual"] - segundo["percentual"]
    else:
        margem_votos = None
        margem_pct = None

    return {
        "municipio": municipio,
        "prefeito": eleito["nome"],
        "vice_prefeito": eleito.get("vice", ""),
        "partido": eleito["partido"],
        "numero": eleito["numero"],
        "votos_prefeito": eleito["votos"],
        "percentual_prefeito": eleito["percentual"],
        "segundo_colocado": segundo["nome"] if segundo else None,
        "partido_segundo_colocado": segundo["partido"] if segundo else None,
        "votos_segundo_colocado": segundo["votos"] if segundo else None,
        "percentual_segundo_colocado": segundo["percentual"] if segundo else None,
        "margem_vitoria_votos": margem_votos,
        "margem_vitoria_pct": margem_pct,
        "status_extracao": "OK",
        "arquivo_origem": pdf_path.name,
    }


def main() -> None:
    print("Iniciando ETL 007 — Base Política Municipal com votos")

    arquivos = sorted(PDF_DIR.glob("*.pdf"))
    arquivos = [a for a in arquivos if "_leiame" not in a.name.lower()]

    print(f"PDFs encontrados: {len(arquivos)}")

    registros = []

    for i, pdf_path in enumerate(arquivos, start=1):
        print(f"[{i}/{len(arquivos)}] {pdf_path.name}")
        registros.append(processar_pdf(pdf_path))

    df = pd.DataFrame(registros)

    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)

    df.to_csv(OUTPUT_CSV, index=False, encoding="utf-8-sig")
    df.to_excel(OUTPUT_XLSX, index=False)

    print("\nVALIDAÇÃO")
    print(f"Registros: {len(df)}")
    print(f"Extrações OK: {(df['status_extracao'] == 'OK').sum()}")
    print(f"Falhas: {(df['status_extracao'] != 'OK').sum()}")

    print("\nAmostra:")
    print(
        df[
            [
                "municipio",
                "prefeito",
                "vice_prefeito",
                "partido",
                "votos_prefeito",
                "percentual_prefeito",
                "segundo_colocado",
                "margem_vitoria_votos",
                "status_extracao",
            ]
        ]
        .head(20)
        .to_string(index=False)
    )

    print("\nArquivos gerados:")
    print(OUTPUT_CSV)
    print(OUTPUT_XLSX)

    print("\nETL 007 concluído.")


if __name__ == "__main__":
    main()