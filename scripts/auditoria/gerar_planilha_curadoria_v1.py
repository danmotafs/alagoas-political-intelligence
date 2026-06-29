# scripts/auditoria/gerar_planilha_curadoria_v1.py

from pathlib import Path
import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[2]

AUDIT_DIR = BASE_DIR / "data" / "audit"
CURADORIA_DIR = BASE_DIR / "data" / "curadoria"
CURADORIA_DIR.mkdir(parents=True, exist_ok=True)

PLANO_PATH = AUDIT_DIR / "plano_saneamento_geocodificacao.csv"

OUT_CSV = CURADORIA_DIR / "curadoria_geocodificacao_v1.csv"
OUT_XLSX = CURADORIA_DIR / "curadoria_geocodificacao_v1.xlsx"


def carregar_csv(caminho: Path) -> pd.DataFrame:
    if not caminho.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {caminho}")

    try:
        return pd.read_csv(caminho, sep=None, engine="python", encoding="utf-8-sig")
    except UnicodeDecodeError:
        return pd.read_csv(caminho, sep=None, engine="python", encoding="latin1")


def main():
    print()
    print("=" * 70)
    print("CUR-005 — GERAÇÃO DA PLANILHA MANUAL DE CURADORIA V1")
    print("=" * 70)

    plano = carregar_csv(PLANO_PATH)

    prioridade_1 = plano[plano["prioridade"] == "PRIORIDADE_1"].copy()

    curadoria = pd.DataFrame({
        "prioridade": prioridade_1["prioridade"],
        "municipio": prioridade_1["municipio"],
        "local_votacao": prioridade_1["local_sem_geo"],
        "local_padronizado": prioridade_1["melhor_local_cache"],
        "endereco": prioridade_1["endereco_cache"],
        "consulta_geocoding": prioridade_1["consulta_geocoding"],
        "registros_afetados": prioridade_1["registros_afetados"],
        "score_similaridade": prioridade_1["score_similaridade"],
        "status_match": prioridade_1["status_match"],
        "status_geocodificacao_atual": prioridade_1["status_geocodificacao"],
        "latitude_atual": "",
        "longitude_atual": "",
        "bairro_atual": "",
        "latitude_curadoria": "",
        "longitude_curadoria": "",
        "bairro_curadoria": "",
        "status_curadoria": "PENDENTE",
        "fonte_validacao": "",
        "responsavel": "",
        "data_validacao": "",
        "observacao": "",
    })

    curadoria = curadoria.sort_values(
        ["registros_afetados", "municipio", "local_votacao"],
        ascending=[False, True, True]
    )

    curadoria.to_csv(OUT_CSV, index=False, encoding="utf-8-sig")

    with pd.ExcelWriter(OUT_XLSX, engine="openpyxl") as writer:
        curadoria.to_excel(writer, index=False, sheet_name="curadoria_prioridade_1")

        ws = writer.book["curadoria_prioridade_1"]
        ws.freeze_panes = "A2"

        for column_cells in ws.columns:
            max_length = 0
            column_letter = column_cells[0].column_letter

            for cell in column_cells:
                value = str(cell.value) if cell.value is not None else ""
                max_length = max(max_length, len(value))

            ws.column_dimensions[column_letter].width = min(max_length + 2, 60)

    print()
    print("Planilha de curadoria gerada com sucesso.")
    print(f"Registros PRIORIDADE_1: {len(curadoria)}")

    print()
    print("Arquivos gerados:")
    print(f"- {OUT_CSV}")
    print(f"- {OUT_XLSX}")

    print()
    print("Próxima etapa: preencher latitude_curadoria, longitude_curadoria e bairro_curadoria.")


if __name__ == "__main__":
    main()