from pathlib import Path
import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[2]

ARQUIVOS_DASHBOARD_V2 = [
    "data/final/base_politica_municipal_2024.csv",
    "data/final/inteligencia_politica_territorial_2024_2026.csv",
    "data/final/inteligencia_politica_territorial_enriquecida.csv",
    "data/final/agenda_prioritaria_davi_maia.csv",
    "data/final/resumo_municipios_visitados.csv",
    "data/final/top30_liderancas_estrategicas.csv",
    "data/final/rede_poder_top30_enriquecida.csv",
    "data/final/rede_poder_top30_classificada.csv",
    "data/processed/alagoas_municipios_base_2024.csv",
    "data/processed/ranking_estrategico_alagoas_2024.csv",
]

POSSIVEIS_COLUNAS_MUNICIPIO = [
    "municipio",
    "nome_municipio",
    "município",
    "cidade",
]

COLUNAS_RELEVANTES_VAZIOS = [
    "municipio",
    "prefeito",
    "partido",
    "eleitorado_2024",
    "populacao_estimada_2024",
    "visitado",
    "grupo_politico",
    "relacao_davi",
    "peso_politico",
    "status_articulacao",
]


def carregar_csv(caminho: Path) -> pd.DataFrame:
    """
    Carrega CSV com fallback de separador e encoding.
    """
    tentativas = [
        {"sep": ",", "encoding": "utf-8"},
        {"sep": ";", "encoding": "utf-8"},
        {"sep": ",", "encoding": "latin1"},
        {"sep": ";", "encoding": "latin1"},
    ]

    ultimo_erro = None

    for params in tentativas:
        try:
            df = pd.read_csv(caminho, **params)
            if df.shape[1] > 1:
                return df
        except Exception as erro:
            ultimo_erro = erro

    raise RuntimeError(f"Erro ao carregar {caminho}: {ultimo_erro}")


def detectar_coluna_municipio(df: pd.DataFrame) -> str | None:
    """
    Detecta a coluna municipal mais provável.
    """
    colunas_normalizadas = {col.lower().strip(): col for col in df.columns}

    for candidato in POSSIVEIS_COLUNAS_MUNICIPIO:
        if candidato in colunas_normalizadas:
            return colunas_normalizadas[candidato]

    for col in df.columns:
        if "municip" in col.lower():
            return col

    return None


def auditar_arquivo(caminho_relativo: str) -> dict:
    caminho = BASE_DIR / caminho_relativo

    resultado = {
        "arquivo": caminho_relativo,
        "existe": caminho.exists(),
        "linhas": None,
        "colunas_qtd": None,
        "colunas": [],
        "coluna_municipio": None,
        "municipios_unicos": None,
        "campos_vazios": {},
        "status": "AUSENTE",
        "erro": None,
    }

    if not caminho.exists():
        return resultado

    try:
        df = carregar_csv(caminho)

        resultado["linhas"] = len(df)
        resultado["colunas_qtd"] = len(df.columns)
        resultado["colunas"] = list(df.columns)

        coluna_municipio = detectar_coluna_municipio(df)
        resultado["coluna_municipio"] = coluna_municipio

        if coluna_municipio:
            resultado["municipios_unicos"] = df[coluna_municipio].dropna().astype(str).str.strip().nunique()

        for coluna in COLUNAS_RELEVANTES_VAZIOS:
            if coluna in df.columns:
                resultado["campos_vazios"][coluna] = int(df[coluna].isna().sum())

        resultado["status"] = "OK"

    except Exception as erro:
        resultado["status"] = "ERRO"
        resultado["erro"] = str(erro)

    return resultado


def imprimir_relatorio(resultados: list[dict]) -> None:
    print("\n" + "=" * 80)
    print("AUDITORIA DAS BASES DO DASHBOARD V2")
    print("=" * 80)

    arquivos_ok = [r for r in resultados if r["status"] == "OK"]
    arquivos_ausentes = [r for r in resultados if r["status"] == "AUSENTE"]
    arquivos_erro = [r for r in resultados if r["status"] == "ERRO"]

    print(f"\nArquivos esperados: {len(resultados)}")
    print(f"Arquivos encontrados: {len(arquivos_ok)}")
    print(f"Arquivos ausentes: {len(arquivos_ausentes)}")
    print(f"Arquivos com erro: {len(arquivos_erro)}")

    print("\n" + "=" * 80)
    print("DETALHAMENTO POR ARQUIVO")
    print("=" * 80)

    for r in resultados:
        print(f"\nArquivo: {r['arquivo']}")
        print(f"Status: {r['status']}")

        if r["status"] == "AUSENTE":
            print("Observação: arquivo não encontrado.")
            continue

        if r["status"] == "ERRO":
            print(f"Erro: {r['erro']}")
            continue

        print(f"Linhas: {r['linhas']}")
        print(f"Colunas: {r['colunas_qtd']}")
        print(f"Coluna municipal detectada: {r['coluna_municipio']}")
        print(f"Municípios únicos: {r['municipios_unicos']}")

        print("Lista de colunas:")
        for coluna in r["colunas"]:
            print(f"  - {coluna}")

        if r["campos_vazios"]:
            print("Campos vazios relevantes:")
            for coluna, qtd in r["campos_vazios"].items():
                print(f"  - {coluna}: {qtd}")
        else:
            print("Campos vazios relevantes: nenhuma coluna monitorada encontrada.")

    print("\n" + "=" * 80)
    print("POSSÍVEIS CHAVES DE MERGE")
    print("=" * 80)

    for r in arquivos_ok:
        print(f"\n{r['arquivo']}")
        print(f"Chave municipal provável: {r['coluna_municipio']}")

    print("\n" + "=" * 80)
    print("DIAGNÓSTICO INICIAL")
    print("=" * 80)

    if arquivos_ausentes:
        print("\nArquivos ausentes:")
        for r in arquivos_ausentes:
            print(f"  - {r['arquivo']}")
    else:
        print("\nNenhum arquivo ausente.")

    if arquivos_erro:
        print("\nArquivos com erro de leitura:")
        for r in arquivos_erro:
            print(f"  - {r['arquivo']}: {r['erro']}")
    else:
        print("Nenhum erro de leitura identificado.")

    print("\nBases prontas para análise:")
    for r in arquivos_ok:
        if r["coluna_municipio"] and r["linhas"] and r["linhas"] > 0:
            print(f"  - {r['arquivo']}")

    print("\nAuditoria concluída.")


def main() -> None:
    resultados = []

    for arquivo in ARQUIVOS_DASHBOARD_V2:
        resultado = auditar_arquivo(arquivo)
        resultados.append(resultado)

    imprimir_relatorio(resultados)


if __name__ == "__main__":
    main()