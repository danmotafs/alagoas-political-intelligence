from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path


def detectar_raiz_projeto() -> Path:
    caminho_script = Path(__file__).resolve()

    if (
        caminho_script.parent.name.lower() == "setup"
        and caminho_script.parent.parent.name.lower() == "scripts"
    ):
        return caminho_script.parent.parent.parent

    return Path.cwd()


def fazer_backup(caminho: Path) -> None:
    if not caminho.exists():
        print(f"[AVISO] Arquivo não encontrado para backup: {caminho}")
        return

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = caminho.with_name(f"{caminho.name}.bak_print_gabi_{timestamp}")
    backup.write_text(caminho.read_text(encoding="utf-8"), encoding="utf-8")
    print(f"[OK] Backup criado: {backup}")


def localizar_foto_no_html(html: str) -> str | None:
    match = re.search(
        r'<img\s+[^>]*class="candidate-photo"[^>]*src="([^"]+)"[^>]*>',
        html,
        flags=re.IGNORECASE | re.DOTALL,
    )

    if match:
        return match.group(1)

    return None


def atualizar_html(index_path: Path) -> None:
    if not index_path.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {index_path}")

    html = index_path.read_text(encoding="utf-8")
    original = html

    foto_src = localizar_foto_no_html(html)

    if not foto_src:
        print("[AVISO] Não encontrei a imagem .candidate-photo no HTML.")
        print("[AVISO] Vou seguir apenas com a correção de CSS.")
        return

    if 'class="candidate-photo-print"' in html:
        print("[OK] Fallback de impressão da foto já existe no HTML.")
        return

    # Melhora o carregamento da foto principal no navegador antes do Ctrl+P.
    html = re.sub(
        r'(<img\s+[^>]*class="candidate-photo"[^>]*src="[^"]+"[^>]*)(/?>)',
        lambda m: (
            m.group(1)
            + '\n              loading="eager"\n              decoding="sync"'
            + m.group(2)
        )
        if 'loading=' not in m.group(1) else m.group(0),
        html,
        count=1,
        flags=re.IGNORECASE | re.DOTALL,
    )

    bloco_print = f'''
            <img
              class="candidate-photo-print"
              src="{foto_src}"
              alt="Foto de Gabi Gonçalves para impressão"
            />
'''

    html = re.sub(
        r'(<img\s+[^>]*class="candidate-photo"[^>]*src="[^"]+"[^>]*>)',
        r'\1' + bloco_print,
        html,
        count=1,
        flags=re.IGNORECASE | re.DOTALL,
    )

    if html != original:
        fazer_backup(index_path)
        index_path.write_text(html, encoding="utf-8")
        print(f"[OK] HTML atualizado com fallback de impressão da foto: {index_path}")
    else:
        print("[INFO] Nenhuma alteração aplicada no HTML.")


def atualizar_css(css_path: Path) -> None:
    if not css_path.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {css_path}")

    css = css_path.read_text(encoding="utf-8")

    marcador_inicio = "/* ===== SPRINT01D_PRINT_GABI_INICIO ===== */"
    marcador_fim = "/* ===== SPRINT01D_PRINT_GABI_FIM ===== */"

    bloco_css = f"""
{marcador_inicio}

/*
  Correção específica para impressão/PDF.
  Motivo: o Chrome pode falhar ao renderizar imagens absolutas dentro de cards
  com overflow, gradientes e filtros no preview de impressão.
*/

.candidate-photo-print {{
  display: none;
}}

@media print {{
  * {{
    -webkit-print-color-adjust: exact !important;
    print-color-adjust: exact !important;
  }}

  body {{
    background: #ffffff !important;
  }}

  .page-shell {{
    width: 100% !important;
    max-width: none !important;
    margin: 0 auto !important;
  }}

  .hero {{
    padding-top: 8px !important;
  }}

  .candidate-card-complete {{
    display: grid !important;
    grid-template-columns: 1fr 1fr !important;
    grid-template-rows: auto !important;
    gap: 14px !important;
    break-inside: avoid !important;
    page-break-inside: avoid !important;
  }}

  .candidate-photo-panel {{
    position: relative !important;
    min-height: auto !important;
    height: auto !important;
    overflow: hidden !important;
    border-radius: 22px !important;
    background: #0B1F4D !important;
    box-shadow: none !important;
    break-inside: avoid !important;
    page-break-inside: avoid !important;
  }}

  .candidate-photo {{
    display: none !important;
  }}

  .candidate-photo-print {{
    display: block !important;
    position: relative !important;
    z-index: 1 !important;
    width: 100% !important;
    height: 300px !important;
    object-fit: cover !important;
    object-position: center top !important;
    opacity: 1 !important;
    visibility: visible !important;
    filter: none !important;
    transform: none !important;
    border-radius: 22px 22px 0 0 !important;
  }}

  .photo-gradient {{
    display: none !important;
  }}

  .photo-glow {{
    display: none !important;
  }}

  .candidate-photo-caption {{
    position: relative !important;
    left: auto !important;
    right: auto !important;
    bottom: auto !important;
    z-index: 2 !important;
    margin: 0 !important;
    border-radius: 0 0 22px 22px !important;
    background: #0B1F4D !important;
    color: #ffffff !important;
    box-shadow: none !important;
    backdrop-filter: none !important;
  }}

  .campaign-logo-panel {{
    min-height: auto !important;
    box-shadow: none !important;
    break-inside: avoid !important;
    page-break-inside: avoid !important;
  }}

  .campaign-logo-main {{
    display: block !important;
    max-width: 260px !important;
    max-height: 130px !important;
    object-fit: contain !important;
    visibility: visible !important;
    opacity: 1 !important;
  }}

  .hero-content,
  .candidate-card,
  .section,
  .panel-card,
  .strategy-card,
  .cross-card,
  .roadmap-item,
  .kpi-card {{
    box-shadow: none !important;
    backdrop-filter: none !important;
    break-inside: avoid !important;
    page-break-inside: avoid !important;
  }}

  .topbar {{
    break-inside: avoid !important;
    page-break-inside: avoid !important;
  }}
}}

{marcador_fim}
"""

    padrao = rf"{re.escape(marcador_inicio)}.*?{re.escape(marcador_fim)}"

    if re.search(padrao, css, flags=re.DOTALL):
        novo_css = re.sub(padrao, bloco_css.strip(), css, flags=re.DOTALL)
    else:
        novo_css = css.rstrip() + "\n\n" + bloco_css.strip() + "\n"

    fazer_backup(css_path)
    css_path.write_text(novo_css, encoding="utf-8")
    print(f"[OK] CSS de impressão atualizado: {css_path}")


def main() -> None:
    root = detectar_raiz_projeto()

    painel_dir = root / "parceiros" / "gabi-goncalves"
    index_path = painel_dir / "index.html"
    css_path = painel_dir / "styles.css"

    print("============================================================")
    print("SPRINT 01D — CORREÇÃO DA FOTO DA GABI NA IMPRESSÃO")
    print("============================================================")
    print(f"[INFO] Raiz detectada: {root}")

    atualizar_html(index_path)
    atualizar_css(css_path)

    print("")
    print("============================================================")
    print("SPRINT 01D CONCLUÍDO")
    print("============================================================")
    print("Agora teste novamente:")
    print("  cd C:\\Users\\user\\Documents\\Workspace\\campanha_2026\\alagoas-political-intelligence")
    print("  python -m http.server 8000")
    print("")
    print("Abra:")
    print("  http://localhost:8000/parceiros/gabi-goncalves/")
    print("")
    print("Depois use Ctrl + P e confira se a foto aparece no preview.")
    print("============================================================")


if __name__ == "__main__":
    main()