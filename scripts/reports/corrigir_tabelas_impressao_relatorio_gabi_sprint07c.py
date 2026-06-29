from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path


def detectar_raiz_projeto() -> Path:
    caminho_script = Path(__file__).resolve()

    if (
        caminho_script.parent.name.lower() == "reports"
        and caminho_script.parent.parent.name.lower() == "scripts"
    ):
        return caminho_script.parent.parent.parent

    return Path.cwd()


def fazer_backup(caminho: Path) -> None:
    if not caminho.exists():
        print(f"[AVISO] Arquivo não encontrado para backup: {caminho}")
        return

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = caminho.with_name(f"{caminho.name}.bak_sprint07c_{timestamp}")
    backup.write_text(caminho.read_text(encoding="utf-8"), encoding="utf-8")
    print(f"[OK] Backup criado: {backup}")


def aplicar_css_tabelas_print(html: str) -> str:
    marcador_inicio = "/* ===== SPRINT07C_TABELAS_PRINT_INICIO ===== */"
    marcador_fim = "/* ===== SPRINT07C_TABELAS_PRINT_FIM ===== */"

    bloco_css = f"""
    {marcador_inicio}

    /*
      Correção para impressão das tabelas do relatório executivo.
      Motivo:
      - No navegador, .table-wrap usa overflow-x:auto.
      - Na impressão, isso faz o Chrome cortar as colunas à direita.
      - Esta regra força as tabelas a caberem dentro da área útil do PDF.
    */

    @page {{
      size: A4 landscape;
      margin: 8mm;
    }}

    .table-wrap {{
      width: 100%;
      max-width: 100%;
    }}

    table {{
      width: 100%;
      max-width: 100%;
    }}

    th,
    td {{
      overflow-wrap: anywhere;
      word-break: break-word;
      hyphens: auto;
    }}

    @media print {{
      html,
      body {{
        width: 100% !important;
        max-width: 100% !important;
        overflow: visible !important;
      }}

      body {{
        background: #ffffff !important;
        -webkit-print-color-adjust: exact !important;
        print-color-adjust: exact !important;
      }}

      .page {{
        width: 100% !important;
        max-width: 100% !important;
        margin: 0 !important;
        padding: 0 !important;
      }}

      .section {{
        width: 100% !important;
        max-width: 100% !important;
        margin: 8mm 0 !important;
        padding: 8mm !important;
        border-radius: 14px !important;
        overflow: visible !important;
        box-shadow: none !important;
        break-inside: avoid-page !important;
        page-break-inside: avoid !important;
      }}

      .section-header {{
        margin-bottom: 10px !important;
      }}

      .section-header h2 {{
        font-size: 22px !important;
        line-height: 1.05 !important;
        letter-spacing: -0.04em !important;
      }}

      .section-header p {{
        font-size: 11px !important;
        line-height: 1.35 !important;
        max-width: none !important;
      }}

      .table-wrap {{
        width: 100% !important;
        max-width: 100% !important;
        overflow: visible !important;
        border-radius: 8px !important;
        border: 1px solid #DCE4F4 !important;
        break-inside: auto !important;
        page-break-inside: auto !important;
      }}

      table {{
        width: 100% !important;
        max-width: 100% !important;
        min-width: 0 !important;
        table-layout: fixed !important;
        border-collapse: collapse !important;
        font-size: 7.4px !important;
        line-height: 1.16 !important;
      }}

      thead {{
        display: table-header-group !important;
      }}

      tbody {{
        display: table-row-group !important;
      }}

      tr {{
        break-inside: avoid !important;
        page-break-inside: avoid !important;
      }}

      th {{
        padding: 4px 4px !important;
        white-space: normal !important;
        overflow-wrap: anywhere !important;
        word-break: break-word !important;
        line-height: 1.12 !important;
        font-size: 6.7px !important;
        letter-spacing: .02em !important;
        vertical-align: middle !important;
      }}

      td {{
        padding: 4px 4px !important;
        white-space: normal !important;
        overflow-wrap: anywhere !important;
        word-break: break-word !important;
        line-height: 1.16 !important;
        vertical-align: top !important;
      }}

      /*
        Distribuição genérica para tabelas com muitas colunas.
        Mantém todas as colunas visíveis, sem rolagem horizontal.
      */
      table th:nth-child(1),
      table td:nth-child(1) {{
        width: 6% !important;
      }}

      table th:nth-child(2),
      table td:nth-child(2) {{
        width: 12% !important;
      }}

      table th:nth-child(3),
      table td:nth-child(3) {{
        width: 12% !important;
      }}

      table th:nth-child(4),
      table td:nth-child(4) {{
        width: 13% !important;
      }}

      table th:nth-child(5),
      table td:nth-child(5) {{
        width: 16% !important;
      }}

      table th:nth-child(6),
      table td:nth-child(6) {{
        width: 13% !important;
      }}

      table th:nth-child(7),
      table td:nth-child(7) {{
        width: 14% !important;
      }}

      table th:nth-child(8),
      table td:nth-child(8) {{
        width: 14% !important;
      }}

      /*
        Para tabelas com textos muito longos na última coluna,
        permite quebra agressiva sem cortar conteúdo.
      */
      table td:last-child,
      table th:last-child {{
        overflow-wrap: anywhere !important;
        word-break: break-word !important;
      }}

      .cover {{
        margin-bottom: 8mm !important;
      }}

      .kpi-grid,
      .highlight-grid,
      .week-grid {{
        break-inside: avoid !important;
        page-break-inside: avoid !important;
      }}
    }}

    {marcador_fim}
"""

    padrao = rf"{re.escape(marcador_inicio)}.*?{re.escape(marcador_fim)}"

    if re.search(padrao, html, flags=re.DOTALL):
        html = re.sub(
            padrao,
            bloco_css.strip(),
            html,
            count=1,
            flags=re.DOTALL,
        )
        return html

    if "</style>" not in html:
        raise RuntimeError("Não encontrei </style> no relatório HTML.")

    html = html.replace("</style>", bloco_css + "\n  </style>", 1)

    return html


def corrigir_relatorio(root: Path) -> None:
    relatorio_html = (
        root
        / "reports"
        / "parceiros"
        / "gabi-goncalves"
        / "relatorio_executivo_gabi_sprint07.html"
    )

    if not relatorio_html.exists():
        raise FileNotFoundError(
            "Relatório executivo não encontrado. Rode antes o Sprint 07."
        )

    html = relatorio_html.read_text(encoding="utf-8")
    novo_html = aplicar_css_tabelas_print(html)

    if novo_html != html:
        fazer_backup(relatorio_html)
        relatorio_html.write_text(novo_html, encoding="utf-8")
        print(f"[OK] Relatório atualizado para impressão de tabelas: {relatorio_html}")
    else:
        print("[INFO] Nenhuma alteração aplicada. O bloco Sprint 07C já existia.")


def main() -> None:
    root = detectar_raiz_projeto()

    print("============================================================")
    print("SPRINT 07C — AJUSTE DE TABELAS PARA IMPRESSÃO")
    print("============================================================")
    print(f"[INFO] Raiz detectada: {root}")

    corrigir_relatorio(root)

    print("")
    print("============================================================")
    print("SPRINT 07C CONCLUÍDO")
    print("============================================================")
    print("Agora teste novamente:")
    print("  cd C:\\Users\\user\\Documents\\Workspace\\campanha_2026\\alagoas-political-intelligence")
    print("  python -m http.server 8000")
    print("")
    print("Abra:")
    print("  http://localhost:8000/reports/parceiros/gabi-goncalves/relatorio_executivo_gabi_sprint07.html")
    print("")
    print("Depois use:")
    print("  Ctrl + F5")
    print("  Ctrl + P")
    print("")
    print("No preview, mantenha:")
    print("  Layout: Paisagem")
    print("  Cor: Cor")
    print("============================================================")


if __name__ == "__main__":
    main()