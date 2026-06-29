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
# UTILITÁRIOS
# ============================================================

def criar_backup(caminho):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    nome, ext = os.path.splitext(caminho)
    backup = f"{nome}_backup_logo_clean_{timestamp}{ext}"
    shutil.copy2(caminho, backup)
    return backup


def ler_arquivo(caminho):
    with open(caminho, "r", encoding="utf-8") as f:
        return f.read()


def salvar_arquivo(caminho, conteudo):
    with open(caminho, "w", encoding="utf-8") as f:
        f.write(conteudo)


def substituir_bloco_css(css, seletor, novo_bloco):
    padrao = re.compile(
        rf'{re.escape(seletor)}\s*\{{.*?\}}',
        flags=re.DOTALL
    )

    novo_css, qtd = padrao.subn(novo_bloco, css)

    if qtd == 0:
        novo_css += "\n\n" + novo_bloco + "\n"

    return novo_css


# ============================================================
# AJUSTE HTML
# ============================================================

def ajustar_html():
    if not os.path.exists(INDEX_HTML):
        raise FileNotFoundError(f"Arquivo não encontrado: {INDEX_HTML}")

    backup = criar_backup(INDEX_HTML)
    print(f"Backup HTML criado: {backup}")

    html = ler_arquivo(INDEX_HTML)

    # Garante que a logo seja link para o painel principal do Davi
    padrao_logo_link = re.compile(
        r'<a href="\.\./dashboard_v2/" class="davi-logo-wrap"[^>]*>\s*<img src="([^"]+)" alt="Davi Maia"\s*/>\s*</a>',
        flags=re.DOTALL
    )

    novo_bloco = r'''<a href="../dashboard_v2/" class="davi-logo-wrap" aria-label="Abrir painel principal do Davi Maia" title="Abrir painel principal do Davi Maia">
          <img src="\1" alt="Davi Maia" />
        </a>'''

    html_novo, qtd = padrao_logo_link.subn(novo_bloco, html)

    if qtd == 0:
        # tenta converter caso ainda esteja em div
        padrao_logo_div = re.compile(
            r'<div class="davi-logo-wrap">\s*<img src="([^"]+)" alt="Davi Maia"\s*/>\s*</div>',
            flags=re.DOTALL
        )
        html_novo, qtd2 = padrao_logo_div.subn(novo_bloco, html)

        if qtd2 == 0:
            print("[AVISO] Não foi possível localizar o bloco da logo no HTML.")
            html_novo = html
        else:
            print("[OK] Bloco da logo convertido de div para link.")
    else:
        print("[OK] Link da logo confirmado no HTML.")

    salvar_arquivo(INDEX_HTML, html_novo)
    print("[OK] index.html atualizado.")


# ============================================================
# AJUSTE CSS
# ============================================================

def ajustar_css():
    if not os.path.exists(CSS_FILE):
        raise FileNotFoundError(f"Arquivo não encontrado: {CSS_FILE}")

    backup = criar_backup(CSS_FILE)
    print(f"Backup CSS criado: {backup}")

    css = ler_arquivo(CSS_FILE)

    bloco_logo = r'''.davi-logo-wrap {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: auto;
  height: auto;
  min-width: 0;
  min-height: 0;
  background: transparent;
  border: none;
  border-radius: 0;
  padding: 0;
  overflow: visible;
  text-decoration: none;
  flex-shrink: 0;
  box-shadow: none;
  line-height: 0;
  cursor: pointer;
}'''

    bloco_logo_img = r'''.davi-logo-wrap img {
  display: block;
  width: auto;
  height: auto;
  max-width: 104px;
  max-height: 58px;
  object-fit: contain;
}'''

    bloco_fallback = r'''.davi-logo-wrap.fallback {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: none;
  padding: 0;
  text-decoration: none;
}'''

    bloco_fallback_span = r'''.davi-logo-wrap.fallback span {
  color: #ffffff;
  font-size: 12px;
  line-height: .95;
  font-weight: 900;
  text-align: center;
}'''

    css = substituir_bloco_css(css, ".davi-logo-wrap", bloco_logo)
    css = substituir_bloco_css(css, ".davi-logo-wrap img", bloco_logo_img)
    css = substituir_bloco_css(css, ".davi-logo-wrap.fallback", bloco_fallback)
    css = substituir_bloco_css(css, ".davi-logo-wrap.fallback span", bloco_fallback_span)

    # Remove media query antiga específica da logo, se houver
    css = re.sub(
        r'\.davi-logo-wrap\s*\{\s*width:\s*100px;\s*height:\s*52px;\s*padding:\s*8px 10px;\s*\}',
        '',
        css,
        flags=re.DOTALL
    )

    css = re.sub(
        r'\.davi-logo-wrap img\s*\{\s*transform:\s*scale\(\.86\);\s*\}',
        '',
        css,
        flags=re.DOTALL
    )

    # Substitui o bloco @media (max-width: 380px)
    padrao_media = re.compile(
        r'@media\s*\(max-width:\s*380px\)\s*\{.*?\}',
        flags=re.DOTALL
    )

    novo_media = r'''@media (max-width: 380px) {
  .hero h1 {
    font-size: 34px;
  }

  .metric-grid {
    grid-template-columns: 1fr;
  }

  .davi-logo-wrap img {
    max-width: 92px;
    max-height: 52px;
  }
}'''

    if padrao_media.search(css):
        css = padrao_media.sub(novo_media, css)
    else:
        css += "\n\n" + novo_media + "\n"

    salvar_arquivo(CSS_FILE, css)
    print("[OK] CSS atualizado.")


# ============================================================
# MAIN
# ============================================================

def main():
    print("=" * 80)
    print("AJUSTE DA LOGO DO DAVI — SEM CONTAINER BRANCO")
    print("=" * 80)

    ajustar_html()
    ajustar_css()

    print()
    print("Concluído com sucesso.")
    print()
    print("Agora abra:")
    print("http://localhost:8000/dashboard_mobile_parceiros/?v=logo-clean-v1")
    print()
    print("Depois pressione CTRL + F5")
    print("=" * 80)


if __name__ == "__main__":
    main()