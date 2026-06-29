import os
import re
import shutil
from datetime import datetime


# ============================================================
# CONFIGURAÇÕES
# ============================================================

BASE_DIR = r"C:\Users\user\Documents\Workspace\campanha_2026\alagoas-political-intelligence"

INDEX_HTML = os.path.join(
    BASE_DIR,
    "dashboard_mobile_parceiros",
    "index.html",
)

CSS_FILE = os.path.join(
    BASE_DIR,
    "dashboard_mobile_parceiros",
    "css",
    "mobile-parceiros.css",
)


# ============================================================
# FUNÇÕES
# ============================================================

def criar_backup(caminho):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = caminho.replace(
        os.path.splitext(caminho)[1],
        f"_backup_logo_davi_{timestamp}{os.path.splitext(caminho)[1]}",
    )

    shutil.copy2(caminho, backup)
    return backup


def corrigir_html():
    if not os.path.exists(INDEX_HTML):
        raise FileNotFoundError(f"Arquivo não encontrado: {INDEX_HTML}")

    with open(INDEX_HTML, "r", encoding="utf-8") as f:
        html = f.read()

    backup = criar_backup(INDEX_HTML)
    print(f"Backup HTML criado: {backup}")

    # Caso atual: logo em div
    padrao_div_logo = re.compile(
        r'<div class="davi-logo-wrap">\s*<img src="([^"]+)" alt="Davi Maia" />\s*</div>',
        flags=re.DOTALL,
    )

    html, qtd = padrao_div_logo.subn(
        r'''<a href="../dashboard_v2/" class="davi-logo-wrap" aria-label="Abrir painel principal do Davi Maia">
          <img src="\1" alt="Davi Maia" />
        </a>''',
        html,
    )

    # Caso fallback: div sem imagem
    padrao_fallback = re.compile(
        r'<div class="davi-logo-wrap fallback">\s*<span>DAVI<br>MAIA</span>\s*</div>',
        flags=re.DOTALL,
    )

    html, qtd_fallback = padrao_fallback.subn(
        r'''<a href="../dashboard_v2/" class="davi-logo-wrap fallback" aria-label="Abrir painel principal do Davi Maia">
          <span>DAVI<br>MAIA</span>
        </a>''',
        html,
    )

    if qtd == 0 and qtd_fallback == 0:
        print("[AVISO] Não encontrei o bloco da logo para substituir. Verifique o index.html.")
    else:
        print("[OK] Logo transformada em link para ../dashboard_v2/")

    with open(INDEX_HTML, "w", encoding="utf-8") as f:
        f.write(html)


def substituir_bloco_css(css, seletor, novo_bloco):
    """
    Substitui um bloco CSS simples do tipo:
    .classe {
      ...
    }
    """
    padrao = re.compile(
        rf'{re.escape(seletor)}\s*\{{.*?\}}',
        flags=re.DOTALL,
    )

    novo_css, qtd = padrao.subn(novo_bloco, css)

    if qtd == 0:
        novo_css += "\n\n" + novo_bloco + "\n"

    return novo_css, qtd


def corrigir_css():
    if not os.path.exists(CSS_FILE):
        raise FileNotFoundError(f"Arquivo não encontrado: {CSS_FILE}")

    with open(CSS_FILE, "r", encoding="utf-8") as f:
        css = f.read()

    backup = criar_backup(CSS_FILE)
    print(f"Backup CSS criado: {backup}")

    bloco_logo = r'''.davi-logo-wrap {
  width: 112px;
  height: 56px;
  border-radius: 18px;
  background: rgba(255, 255, 255, .96);
  border: 1px solid rgba(255, 255, 255, .45);
  display: grid;
  place-items: center;
  padding: 8px 10px;
  overflow: hidden;
  text-decoration: none;
  flex-shrink: 0;
}'''

    bloco_logo_img = r'''.davi-logo-wrap img {
  width: 100%;
  height: 100%;
  object-fit: contain;
  transform: scale(.88);
  transform-origin: center;
  display: block;
}'''

    bloco_fallback = r'''.davi-logo-wrap.fallback span {
  color: var(--blue-dark);
  font-size: 12px;
  line-height: .95;
  font-weight: 900;
  text-align: center;
}'''

    bloco_mobile = r'''@media (max-width: 380px) {
  .hero h1 {
    font-size: 34px;
  }

  .metric-grid {
    grid-template-columns: 1fr;
  }

  .davi-logo-wrap {
    width: 100px;
    height: 52px;
    padding: 8px 10px;
  }

  .davi-logo-wrap img {
    transform: scale(.86);
  }
}'''

    css, _ = substituir_bloco_css(css, ".davi-logo-wrap", bloco_logo)
    css, _ = substituir_bloco_css(css, ".davi-logo-wrap img", bloco_logo_img)
    css, _ = substituir_bloco_css(css, ".davi-logo-wrap.fallback span", bloco_fallback)

    # Remove bloco @media anterior pequeno, se existir no final, e substitui por versão nova.
    css = re.sub(
        r'@media\s*\(max-width:\s*380px\)\s*\{.*?\n\}',
        '',
        css,
        flags=re.DOTALL,
    ).strip()

    css += "\n\n" + bloco_mobile + "\n"

    with open(CSS_FILE, "w", encoding="utf-8") as f:
        f.write(css)

    print("[OK] CSS da logo ajustado.")


def main():
    print("=" * 80)
    print("CORREÇÃO LOGO DAVI — DASHBOARD MOBILE PARCEIROS")
    print("=" * 80)

    corrigir_html()
    corrigir_css()

    print()
    print("Correção concluída.")
    print()
    print("Teste local:")
    print("http://localhost:8000/dashboard_mobile_parceiros/?v=logo-davi-ajustada-v1")
    print()
    print("Depois pressione CTRL + F5.")
    print("=" * 80)


if __name__ == "__main__":
    main()