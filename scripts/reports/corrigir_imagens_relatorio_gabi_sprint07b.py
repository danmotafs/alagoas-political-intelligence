from __future__ import annotations

import re
import shutil
from datetime import datetime
from pathlib import Path


EXTENSOES_SUPORTADAS = {".png", ".jpg", ".jpeg", ".webp", ".svg"}


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
    backup = caminho.with_name(f"{caminho.name}.bak_sprint07b_{timestamp}")
    backup.write_text(caminho.read_text(encoding="utf-8"), encoding="utf-8")
    print(f"[OK] Backup criado: {backup}")


def localizar_asset(assets_dir: Path, nomes_base: list[str]) -> Path | None:
    if not assets_dir.exists():
        return None

    arquivos = [
        arquivo
        for arquivo in assets_dir.iterdir()
        if arquivo.is_file() and arquivo.suffix.lower() in EXTENSOES_SUPORTADAS
    ]

    nomes_normalizados = [nome.lower().strip() for nome in nomes_base]

    for nome in nomes_normalizados:
        for arquivo in arquivos:
            if arquivo.stem.lower() == nome:
                return arquivo

    for nome in nomes_normalizados:
        for arquivo in arquivos:
            if nome in arquivo.stem.lower():
                return arquivo

    return None


def copiar_asset(origem: Path, destino_dir: Path) -> Path:
    destino_dir.mkdir(parents=True, exist_ok=True)

    destino = destino_dir / origem.name
    shutil.copy2(origem, destino)

    print(f"[OK] Asset copiado:")
    print(f"     Origem : {origem}")
    print(f"     Destino: {destino}")

    return destino


def substituir_box_imagem(
    html: str,
    classe_box: str,
    src: str,
    alt: str,
) -> str:
    novo_bloco = f'''<div class="{classe_box}">
          <img
            src="{src}"
            alt="{alt}"
            loading="eager"
            decoding="sync"
          />
        </div>'''

    padrao = rf'<div class="{re.escape(classe_box)}">.*?</div>'

    if re.search(padrao, html, flags=re.DOTALL):
        return re.sub(
            padrao,
            novo_bloco,
            html,
            count=1,
            flags=re.DOTALL,
        )

    print(f"[AVISO] Não encontrei o bloco .{classe_box} no relatório.")
    return html


def aplicar_css_impressao(html: str) -> str:
    marcador_inicio = "/* ===== SPRINT07B_IMAGENS_PRINT_INICIO ===== */"
    marcador_fim = "/* ===== SPRINT07B_IMAGENS_PRINT_FIM ===== */"

    bloco_css = f"""
    {marcador_inicio}

    .photo-box img,
    .logo-box img {{
      display: block !important;
      opacity: 1 !important;
      visibility: visible !important;
    }}

    @media print {{
      * {{
        -webkit-print-color-adjust: exact !important;
        print-color-adjust: exact !important;
      }}

      .cover {{
        grid-template-columns: 1.25fr .75fr !important;
        break-inside: avoid !important;
        page-break-inside: avoid !important;
      }}

      .cover-side {{
        display: grid !important;
        grid-template-rows: 1fr auto !important;
        gap: 18px !important;
      }}

      .photo-box {{
        display: block !important;
        min-height: 360px !important;
        height: 360px !important;
        overflow: hidden !important;
        background: rgba(255,255,255,.12) !important;
        break-inside: avoid !important;
        page-break-inside: avoid !important;
      }}

      .photo-box img {{
        display: block !important;
        width: 100% !important;
        height: 360px !important;
        object-fit: cover !important;
        object-position: center top !important;
        opacity: 1 !important;
        visibility: visible !important;
        filter: none !important;
        transform: none !important;
      }}

      .logo-box {{
        display: grid !important;
        place-items: center !important;
        min-height: 130px !important;
        height: 130px !important;
        background: #ffffff !important;
        break-inside: avoid !important;
        page-break-inside: avoid !important;
      }}

      .logo-box img {{
        display: block !important;
        max-width: 92% !important;
        max-height: 105px !important;
        width: auto !important;
        height: auto !important;
        object-fit: contain !important;
        opacity: 1 !important;
        visibility: visible !important;
        filter: none !important;
        transform: none !important;
      }}
    }}

    {marcador_fim}
"""

    padrao_bloco = rf"{re.escape(marcador_inicio)}.*?{re.escape(marcador_fim)}"

    if re.search(padrao_bloco, html, flags=re.DOTALL):
        html = re.sub(
            padrao_bloco,
            bloco_css.strip(),
            html,
            count=1,
            flags=re.DOTALL,
        )
        return html

    if "</style>" not in html:
        print("[AVISO] Não encontrei </style> no relatório. CSS de impressão não foi injetado.")
        return html

    html = html.replace("</style>", bloco_css + "\n  </style>", 1)

    return html


def corrigir_relatorio(root: Path) -> None:
    painel_assets_dir = root / "parceiros" / "gabi-goncalves" / "assets"
    relatorio_dir = root / "reports" / "parceiros" / "gabi-goncalves"
    relatorio_assets_dir = relatorio_dir / "assets"
    relatorio_html = relatorio_dir / "relatorio_executivo_gabi_sprint07.html"

    if not relatorio_html.exists():
        raise FileNotFoundError(
            "Relatório executivo não encontrado. Rode antes o Sprint 07:\n"
            "python scripts\\reports\\gerar_relatorio_executivo_gabi_sprint07.py"
        )

    print(f"[INFO] Assets originais: {painel_assets_dir}")
    print(f"[INFO] Relatório HTML : {relatorio_html}")

    foto = localizar_asset(
        painel_assets_dir,
        [
            "foto-gabi",
            "foto_gabi",
            "gabi-foto",
            "foto",
            "gabi",
        ],
    )

    logo = localizar_asset(
        painel_assets_dir,
        [
            "logo-gabi-2026",
            "logo_gabi_2026",
            "logo-gabi",
            "gabi-logo",
            "logo",
        ],
    )

    if foto is None:
        raise FileNotFoundError(
            "Não encontrei a foto da Gabi em parceiros\\gabi-goncalves\\assets. "
            "Confirme se o arquivo começa com foto-gabi."
        )

    if logo is None:
        raise FileNotFoundError(
            "Não encontrei a logo da Gabi em parceiros\\gabi-goncalves\\assets. "
            "Confirme se o arquivo começa com logo-gabi-2026."
        )

    print(f"[OK] Foto encontrada: {foto.name}")
    print(f"[OK] Logo encontrada: {logo.name}")

    foto_relatorio = copiar_asset(foto, relatorio_assets_dir)
    logo_relatorio = copiar_asset(logo, relatorio_assets_dir)

    html = relatorio_html.read_text(encoding="utf-8")
    original = html

    html = substituir_box_imagem(
        html=html,
        classe_box="photo-box",
        src=f"assets/{foto_relatorio.name}",
        alt="Foto de Gabi Gonçalves",
    )

    html = substituir_box_imagem(
        html=html,
        classe_box="logo-box",
        src=f"assets/{logo_relatorio.name}",
        alt="Logomarca Gabi Gonçalves 2026",
    )

    html = aplicar_css_impressao(html)

    if html != original:
        fazer_backup(relatorio_html)
        relatorio_html.write_text(html, encoding="utf-8")
        print(f"[OK] Relatório corrigido: {relatorio_html}")
    else:
        print("[INFO] Nenhuma alteração aplicada no HTML do relatório.")


def main() -> None:
    root = detectar_raiz_projeto()

    print("============================================================")
    print("SPRINT 07B — CORREÇÃO DE IMAGENS NO RELATÓRIO")
    print("============================================================")
    print(f"[INFO] Raiz detectada: {root}")

    corrigir_relatorio(root)

    print("")
    print("============================================================")
    print("SPRINT 07B CONCLUÍDO")
    print("============================================================")
    print("Agora teste novamente:")
    print("  cd C:\\Users\\user\\Documents\\Workspace\\campanha_2026\\alagoas-political-intelligence")
    print("  python -m http.server 8000")
    print("")
    print("Abra:")
    print("  http://localhost:8000/reports/parceiros/gabi-goncalves/relatorio_executivo_gabi_sprint07.html")
    print("")
    print("Depois use Ctrl + F5 e, em seguida, Ctrl + P.")
    print("============================================================")


if __name__ == "__main__":
    main()