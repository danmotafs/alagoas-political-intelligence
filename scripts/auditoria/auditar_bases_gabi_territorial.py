import os
import json
import pandas as pd
from datetime import datetime


# ============================================================
# CONFIGURAÇÕES
# ============================================================

BASE_DIR = r"C:\Users\user\Documents\Workspace\campanha_2026\alagoas-political-intelligence"

DIR_FINAL_GABI = os.path.join(BASE_DIR, "data", "final", "parceiros", "gabi-goncalves")
DIR_DASHBOARD_GABI = os.path.join(BASE_DIR, "data", "dashboard", "parceiros", "gabi-goncalves")
DIR_RAW_TSE = os.path.join(BASE_DIR, "data", "raw", "tse_2024")
DIR_FINAL = os.path.join(BASE_DIR, "data", "final")
DIR_REPORTS = os.path.join(BASE_DIR, "reports")

os.makedirs(DIR_REPORTS, exist_ok=True)

ARQUIVO_TSE_SECAO = os.path.join(DIR_RAW_TSE, "votacao_secao_2024_AL.csv")

ARQUIVOS_GABI_CSV = [
    os.path.join(DIR_FINAL_GABI, "base_eleitoral_gabi_v1.csv"),
    os.path.join(DIR_FINAL_GABI, "cruzamento_davi_gabi_v1.csv"),
    os.path.join(DIR_FINAL_GABI, "curadoria_politica_davi_gabi_v1.csv"),
    os.path.join(DIR_FINAL_GABI, "rede_liderancas_gabi_v1.csv"),
    os.path.join(DIR_FINAL_GABI, "resumo_liderancas_municipio_gabi_v1.csv"),
    os.path.join(DIR_FINAL_GABI, "roteiro_territorial_davi_gabi_v1.csv"),
]

ARQUIVOS_GABI_JSON = [
    os.path.join(DIR_DASHBOARD_GABI, "base_dashboard_gabi_v1.json"),
    os.path.join(DIR_DASHBOARD_GABI, "cruzamento_davi_gabi_v1.json"),
    os.path.join(DIR_DASHBOARD_GABI, "curadoria_politica_davi_gabi_v1.json"),
    os.path.join(DIR_DASHBOARD_GABI, "meta_eleitoral_gabi_estadual_2026.json"),
    os.path.join(DIR_DASHBOARD_GABI, "roteiro_territorial_davi_gabi_v1.json"),
]

ARQUIVOS_TERRITORIAIS_EXISTENTES = [
    os.path.join(DIR_FINAL, "locais_votacao_top10.csv"),
    os.path.join(DIR_FINAL, "mapa_influencia_geografico.csv"),
    os.path.join(DIR_FINAL, "mapa_influencia_vereadores_top10.csv"),
    os.path.join(DIR_FINAL, "polos_eleitorais_top10.csv"),
    os.path.join(DIR_FINAL, "redutos_vereadores_top10.csv"),
    os.path.join(DIR_FINAL, "redutos_qualificados_top10.csv"),
]

SAIDA_MD = os.path.join(DIR_REPORTS, "auditoria_bases_gabi_territorial.md")
SAIDA_CSV_ENCONTRADOS_TSE = os.path.join(DIR_FINAL_GABI, "auditoria_gabi_encontrados_tse_secao.csv")
SAIDA_CSV_RESUMO = os.path.join(DIR_FINAL_GABI, "auditoria_resumo_bases_gabi_territorial.csv")


# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================

def normalizar_texto(valor):
    if valor is None:
        return ""

    texto = str(valor).strip().upper()

    substituicoes = {
        "Á": "A",
        "À": "A",
        "Â": "A",
        "Ã": "A",
        "É": "E",
        "Ê": "E",
        "Í": "I",
        "Ó": "O",
        "Ô": "O",
        "Õ": "O",
        "Ú": "U",
        "Ç": "C",
    }

    for origem, destino in substituicoes.items():
        texto = texto.replace(origem, destino)

    return texto


def detectar_encoding(caminho):
    """
    Testa encodings comuns em bases brasileiras/TSE.
    """
    encodings = ["utf-8-sig", "utf-8", "latin-1", "ISO-8859-1", "cp1252"]

    for encoding in encodings:
        try:
            with open(caminho, "r", encoding=encoding) as f:
                f.readline()
            return encoding
        except UnicodeDecodeError:
            continue

    return "latin-1"


def detectar_sep(caminho, encoding):
    with open(caminho, "r", encoding=encoding, errors="replace") as f:
        primeira_linha = f.readline()

    if ";" in primeira_linha:
        return ";"

    if "," in primeira_linha:
        return ","

    return ";"


def ler_csv_amostra(caminho, nrows=1000):
    encoding = detectar_encoding(caminho)
    sep = detectar_sep(caminho, encoding)

    return pd.read_csv(
        caminho,
        sep=sep,
        encoding=encoding,
        dtype=str,
        nrows=nrows,
        low_memory=False,
        on_bad_lines="skip",
    )


def buscar_gabi_em_df(df):
    termos = [
        "GABI",
        "GABY",
        "GABRIELA",
        "GONCALVES",
        "GONÇALVES",
    ]

    if df.empty:
        return pd.DataFrame()

    mascara = pd.Series(False, index=df.index)

    for col in df.columns:
        serie = df[col].astype(str).apply(normalizar_texto)

        for termo in termos:
            termo_norm = normalizar_texto(termo)
            mascara = mascara | serie.str.contains(termo_norm, na=False)

    return df[mascara].copy()


def analisar_csv(caminho):
    info = {
        "arquivo": caminho,
        "existe": os.path.exists(caminho),
        "tipo": "csv",
        "encoding": "",
        "separador": "",
        "linhas_amostra": 0,
        "colunas": "",
        "qtd_gabi_amostra": 0,
        "erro": "",
    }

    if not os.path.exists(caminho):
        return info, pd.DataFrame()

    try:
        encoding = detectar_encoding(caminho)
        sep = detectar_sep(caminho, encoding)

        df = pd.read_csv(
            caminho,
            sep=sep,
            encoding=encoding,
            dtype=str,
            nrows=1000,
            low_memory=False,
            on_bad_lines="skip",
        )

        encontrados = buscar_gabi_em_df(df)

        info["encoding"] = encoding
        info["separador"] = sep
        info["linhas_amostra"] = len(df)
        info["colunas"] = " | ".join(df.columns.tolist())
        info["qtd_gabi_amostra"] = len(encontrados)

        return info, encontrados

    except Exception as e:
        info["erro"] = str(e)
        return info, pd.DataFrame()


def analisar_json(caminho):
    info = {
        "arquivo": caminho,
        "existe": os.path.exists(caminho),
        "tipo": "json",
        "encoding": "utf-8",
        "separador": "",
        "linhas_amostra": "",
        "colunas": "",
        "qtd_gabi_amostra": "",
        "erro": "",
    }

    if not os.path.exists(caminho):
        return info

    try:
        with open(caminho, "r", encoding="utf-8") as f:
            dados = json.load(f)

        if isinstance(dados, dict):
            info["colunas"] = " | ".join(dados.keys())
        elif isinstance(dados, list):
            info["colunas"] = f"lista com {len(dados)} itens"
        else:
            info["colunas"] = str(type(dados))

        return info

    except Exception as e:
        info["erro"] = str(e)
        return info


def auditar_tse_secao():
    if not os.path.exists(ARQUIVO_TSE_SECAO):
        return {
            "existe": False,
            "encoding": "",
            "separador": "",
            "linhas_lidas": 0,
            "colunas": [],
            "qtd_encontrados": 0,
            "erro": f"Arquivo não encontrado: {ARQUIVO_TSE_SECAO}",
        }, pd.DataFrame()

    print("Auditando arquivo oficial de votação por seção do TSE...")
    print(ARQUIVO_TSE_SECAO)

    encoding = detectar_encoding(ARQUIVO_TSE_SECAO)
    sep = detectar_sep(ARQUIVO_TSE_SECAO, encoding)

    print(f"Encoding detectado: {encoding}")
    print(f"Separador detectado: {repr(sep)}")

    encontrados_lista = []
    colunas_detectadas = []
    total_linhas_lidas = 0

    try:
        chunks = pd.read_csv(
            ARQUIVO_TSE_SECAO,
            sep=sep,
            encoding=encoding,
            dtype=str,
            chunksize=100000,
            low_memory=False,
            on_bad_lines="skip",
        )

        for i, chunk in enumerate(chunks, start=1):
            if i == 1:
                colunas_detectadas = chunk.columns.tolist()

            total_linhas_lidas += len(chunk)

            encontrados = buscar_gabi_em_df(chunk)

            if not encontrados.empty:
                encontrados_lista.append(encontrados)

            print(
                f"Chunk {i} processado | linhas acumuladas: "
                f"{total_linhas_lidas:,}".replace(",", ".")
            )

        if encontrados_lista:
            df_encontrados = pd.concat(encontrados_lista, ignore_index=True)
        else:
            df_encontrados = pd.DataFrame()

        resumo = {
            "existe": True,
            "encoding": encoding,
            "separador": sep,
            "linhas_lidas": total_linhas_lidas,
            "colunas": colunas_detectadas,
            "qtd_encontrados": len(df_encontrados),
            "erro": "",
        }

        return resumo, df_encontrados

    except Exception as e:
        return {
            "existe": True,
            "encoding": encoding,
            "separador": sep,
            "linhas_lidas": total_linhas_lidas,
            "colunas": colunas_detectadas,
            "qtd_encontrados": 0,
            "erro": str(e),
        }, pd.DataFrame()


def gerar_relatorio_md(resumos, resumo_tse):
    with open(SAIDA_MD, "w", encoding="utf-8") as f:
        f.write("# Auditoria das Bases Territoriais da Gabi Gonçalves\n\n")
        f.write(f"Data de geração: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n\n")

        f.write("## 1. Objetivo\n\n")
        f.write(
            "Esta auditoria verifica quais bases da Gabi Gonçalves já existem no projeto, "
            "quais colunas estão disponíveis e se é possível iniciar a territorialização "
            "por seção eleitoral, local de votação, bairro ou região.\n\n"
        )

        f.write("## 2. Bases verificadas\n\n")
        f.write("| Tipo | Existe | Encoding | Separador | Arquivo | Colunas / Chaves | Ocorrências de Gabi na amostra | Erro |\n")
        f.write("|---|---:|---|---|---|---|---:|---|\n")

        for item in resumos:
            f.write(
                f"| {item.get('tipo')} "
                f"| {item.get('existe')} "
                f"| {item.get('encoding', '')} "
                f"| {item.get('separador', '')} "
                f"| {item.get('arquivo')} "
                f"| {str(item.get('colunas', '')).replace('|', '/')} "
                f"| {item.get('qtd_gabi_amostra', '')} "
                f"| {item.get('erro', '')} |\n"
            )

        f.write("\n## 3. Arquivo oficial de votação por seção do TSE\n\n")
        f.write(f"- Arquivo: `{ARQUIVO_TSE_SECAO}`\n")
        f.write(f"- Existe: {resumo_tse.get('existe')}\n")
        f.write(f"- Encoding detectado: {resumo_tse.get('encoding')}\n")
        f.write(f"- Separador detectado: `{resumo_tse.get('separador')}`\n")
        f.write(f"- Linhas lidas: {resumo_tse.get('linhas_lidas')}\n")
        f.write(f"- Ocorrências encontradas com termos GABI/GABRIELA/GONÇALVES: {resumo_tse.get('qtd_encontrados')}\n")

        if resumo_tse.get("erro"):
            f.write(f"- Erro: {resumo_tse.get('erro')}\n")

        f.write("\n### Colunas do arquivo TSE\n\n")

        for col in resumo_tse.get("colunas", []):
            f.write(f"- {col}\n")

        f.write("\n## 4. Interpretação\n\n")

        if resumo_tse.get("qtd_encontrados", 0) > 0:
            f.write(
                "Foram encontradas ocorrências ligadas à Gabi/Gabriela/Gonçalves no arquivo oficial de votação por seção. "
                "O próximo passo é validar qual registro corresponde exatamente à Gabi Gonçalves e gerar a base territorial.\n\n"
            )
        else:
            f.write(
                "Não foram encontradas ocorrências diretas com os termos GABI/GABRIELA/GONÇALVES na busca ampla. "
                "Nesse caso, o próximo passo é identificar a candidata pela base `base_eleitoral_gabi_v1.csv`, "
                "especialmente por número de candidatura, nome de urna, partido e município.\n\n"
            )


def main():
    print("=" * 80)
    print("AUDITORIA DAS BASES TERRITORIAIS DA GABI GONÇALVES")
    print("=" * 80)

    resumos = []
    encontrados_geral = []

    for caminho in ARQUIVOS_GABI_CSV:
        print(f"Analisando CSV: {caminho}")
        info, encontrados = analisar_csv(caminho)
        resumos.append(info)

        if not encontrados.empty:
            encontrados["arquivo_origem"] = os.path.basename(caminho)
            encontrados_geral.append(encontrados)

    for caminho in ARQUIVOS_GABI_JSON:
        print(f"Analisando JSON: {caminho}")
        info = analisar_json(caminho)
        resumos.append(info)

    for caminho in ARQUIVOS_TERRITORIAIS_EXISTENTES:
        print(f"Analisando base territorial existente: {caminho}")
        info, encontrados = analisar_csv(caminho)
        resumos.append(info)

        if not encontrados.empty:
            encontrados["arquivo_origem"] = os.path.basename(caminho)
            encontrados_geral.append(encontrados)

    resumo_tse, df_tse_encontrados = auditar_tse_secao()

    if not df_tse_encontrados.empty:
        df_tse_encontrados.to_csv(
            SAIDA_CSV_ENCONTRADOS_TSE,
            index=False,
            encoding="utf-8-sig",
        )
    else:
        pd.DataFrame().to_csv(
            SAIDA_CSV_ENCONTRADOS_TSE,
            index=False,
            encoding="utf-8-sig",
        )

    df_resumo = pd.DataFrame(resumos)
    df_resumo.to_csv(
        SAIDA_CSV_RESUMO,
        index=False,
        encoding="utf-8-sig",
    )

    gerar_relatorio_md(resumos, resumo_tse)

    print()
    print("=" * 80)
    print("AUDITORIA CONCLUÍDA")
    print("=" * 80)
    print(f"Relatório: {SAIDA_MD}")
    print(f"Resumo CSV: {SAIDA_CSV_RESUMO}")
    print(f"Ocorrências no TSE: {SAIDA_CSV_ENCONTRADOS_TSE}")

    print()
    print("Resumo TSE:")
    print(f"Encoding: {resumo_tse.get('encoding')}")
    print(f"Separador: {repr(resumo_tse.get('separador'))}")
    print(f"Linhas lidas: {resumo_tse.get('linhas_lidas')}")
    print(f"Ocorrências encontradas: {resumo_tse.get('qtd_encontrados')}")
    print(f"Erro: {resumo_tse.get('erro') or '-'}")

    print()
    print("Colunas detectadas no TSE:")
    for col in resumo_tse.get("colunas", []):
        print(f"- {col}")

    print("=" * 80)


if __name__ == "__main__":
    main()