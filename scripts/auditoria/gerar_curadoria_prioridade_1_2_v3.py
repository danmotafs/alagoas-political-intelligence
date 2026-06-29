# scripts/auditoria/gerar_curadoria_prioridade_1_2_v3.py

from pathlib import Path
import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[2]

AUDIT_DIR = BASE_DIR / "data" / "audit"
CURADORIA_DIR = BASE_DIR / "data" / "curadoria"

CURADORIA_DIR.mkdir(parents=True, exist_ok=True)

PENDENCIAS_PATH = AUDIT_DIR / "pendencias_geocodificacao_v3.csv"

OUT_CSV = CURADORIA_DIR / "curadoria_geocodificacao_prioridade_1_2_v3.csv"
OUT_XLSX = CURADORIA_DIR / "curadoria_geocodificacao_prioridade_1_2_v3.xlsx"
OUT_RESUMO = CURADORIA_DIR / "resumo_curadoria_prioridade_1_2_v3.csv"


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
    print("GERAÇÃO DA CURADORIA GEOCODIFICAÇÃO — PRIORIDADE 1 E 2 — V3")
    print("=" * 70)

    pendencias = carregar_csv(PENDENCIAS_PATH)

    prioridades = ["PRIORIDADE_1", "PRIORIDADE_2"]

    base = pendencias[
        pendencias["prioridade"].isin(prioridades)
    ].copy()

    if base.empty:
        print()
        print("Nenhuma pendência PRIORIDADE_1 ou PRIORIDADE_2 encontrada.")
        return

    curadoria = pd.DataFrame({
        "prioridade": base["prioridade"],
        "tipo_pendencia": base["tipo_pendencia"],
        "municipio": base["municipio"],
        "local_votacao_original": base["local_sem_geo"],
        "local_votacao_padronizado": base["melhor_local_cache"],
        "endereco": base["endereco_cache"],
        "consulta_geocoding_original": base["consulta_geocoding"],
        "registros_afetados": base["registros_afetados"],
        "score_similaridade": base["score_similaridade"],
        "status_match": base["status_match"],
        "status_geocodificacao_atual": base["status_geocodificacao"],

        # Campos para preenchimento manual
        "latitude_curadoria": "",
        "longitude_curadoria": "",
        "bairro_curadoria": "",
        "status_curadoria": "PENDENTE",
        "fonte_validacao": "",
        "responsavel": "",
        "data_validacao": "",
        "observacao_curadoria": "",
    })

    curadoria = curadoria.sort_values(
        ["prioridade", "registros_afetados", "municipio", "local_votacao_original"],
        ascending=[True, False, True, True]
    )

    curadoria.to_csv(OUT_CSV, index=False, encoding="utf-8-sig")

    resumo = (
        curadoria
        .groupby(["prioridade", "municipio"], dropna=False)
        .agg(
            locais=("local_votacao_original", "count"),
            registros_afetados=("registros_afetados", "sum")
        )
        .reset_index()
        .sort_values(["prioridade", "registros_afetados"], ascending=[True, False])
    )

    resumo.to_csv(OUT_RESUMO, index=False, encoding="utf-8-sig")

    with pd.ExcelWriter(OUT_XLSX, engine="openpyxl") as writer:
        curadoria.to_excel(writer, index=False, sheet_name="curadoria_p1_p2")
        resumo.to_excel(writer, index=False, sheet_name="resumo_municipio")

        wb = writer.book
        ws = wb["curadoria_p1_p2"]

        ws.freeze_panes = "A2"
        ws.auto_filter.ref = ws.dimensions

        for column_cells in ws.columns:
            max_length = 0
            column_letter = column_cells[0].column_letter

            for cell in column_cells:
                value = "" if cell.value is None else str(cell.value)
                max_length = max(max_length, len(value))

            ws.column_dimensions[column_letter].width = min(max_length + 2, 70)

        ws_resumo = wb["resumo_municipio"]
        ws_resumo.freeze_panes = "A2"
        ws_resumo.auto_filter.ref = ws_resumo.dimensions

        for column_cells in ws_resumo.columns:
            max_length = 0
            column_letter = column_cells[0].column_letter

            for cell in column_cells:
                value = "" if cell.value is None else str(cell.value)
                max_length = max(max_length, len(value))

            ws_resumo.column_dimensions[column_letter].width = min(max_length + 2, 50)

    print()
    print("CURADORIA PRIORIDADE 1 E 2 GERADA COM SUCESSO")
    print("-" * 70)
    print(f"Locais para curadoria: {len(curadoria)}")
    print(f"Registros afetados: {curadoria['registros_afetados'].sum()}")

    print()
    print("RESUMO POR PRIORIDADE")
    print("-" * 70)
    print(
        curadoria
        .groupby("prioridade")
        .agg(
            locais=("local_votacao_original", "count"),
            registros_afetados=("registros_afetados", "sum")
        )
        .reset_index()
        .to_string(index=False)
    )

    print()
    print("Arquivos gerados:")
    print(f"- {OUT_CSV}")
    print(f"- {OUT_XLSX}")
    print(f"- {OUT_RESUMO}")

    print()
    print("Próxima etapa: preencher latitude_curadoria, longitude_curadoria e bairro_curadoria no XLSX.")


if __name__ == "__main__":
    main()