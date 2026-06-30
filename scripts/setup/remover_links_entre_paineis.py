import os
import re
import shutil
from datetime import datetime


# ============================================================
# CONFIGURAÇÕES
# ============================================================

BASE_DIR = r"C:\Users\user\Documents\Workspace\campanha_2026\alagoas-political-intelligence"

INDEX_MOBILE = os.path.join(
    BASE_DIR,
    "dashboard_mobile_parceiros",
    "index.html",
)

CSS_MOBILE = os.path.join(
    BASE_DIR,
    "dashboard_mobile_parceiros",
    "css",
    "mobile-parceiros.css",
)

INDEX_DASHBOARD_V2 = os.path.join(
    BASE_DIR,
    "dashboard_v2",
    "index.html",
)


# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================

def criar_backup(caminho):
    if not os.path.exists(caminho):
        return ""

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    nome, ext = os.path.splitext(caminho)
    backup = f"{nome}_backup_remover_links_paineis_{timestamp}{ext}"

    shutil.copy2(caminho, backup)

    return backup


def ler_arquivo(caminho):
    with open(caminho, "r", encoding="utf-8") as f:
        return f.read()


def salvar_arquivo(caminho, conteudo):
    with open(caminho, "w", encoding="utf-8") as f:
        f.write(conteudo)


# ============================================================
# PAINEL MOBILE
# ============================================================

def remover_botao_painel_completo_mobile(html):
    """
    Remove o botão:
    <a href="../dashboard_v2/" class="back-link">← Painel completo</a>
    """

    padroes = [
        r'\s*<a\s+href="\.\./dashboard_v2/"\s+class="back-link"[^>]*>\s*←\s*Painel completo\s*</a>\s*',
        r'\s*<a\s+class="back-link"\s+href="\.\./dashboard_v2/"[^>]*>\s*←\s*Painel completo\s*</a>\s*',
    ]

    total = 0

    for padrao in padroes:
        html, qtd = re.subn(
            padrao,
            "\n",
            html,
            flags=re.IGNORECASE | re.DOTALL,
        )
        total += qtd

    return html, total


def transformar_logo_davi_em_elemento_estatico(html):
    """
    Converte:
    <a href="../dashboard_v2/" class="davi-logo-wrap" ...>
      <img ... />
    </a>

    em:
    <div class="davi-logo-wrap" aria-label="Davi Maia">
      <img ... />
    </div>
    """

    padrao_link_logo = re.compile(
        r'<a\s+href="\.\./dashboard_v2/"\s+class="davi-logo-wrap"[^>]*>\s*(<img\s+src="[^"]+"\s+alt="Davi Maia"\s*/?>)\s*</a>',
        flags=re.IGNORECASE | re.DOTALL,
    )

    html, qtd_1 = padrao_link_logo.subn(
        r'''<div class="davi-logo-wrap" aria-label="Davi Maia">
          \1
        </div>''',
        html,
    )

    padrao_link_logo_ordem_invertida = re.compile(
        r'<a\s+class="davi-logo-wrap"\s+href="\.\./dashboard_v2/"[^>]*>\s*(<img\s+src="[^"]+"\s+alt="Davi Maia"\s*/?>)\s*</a>',
        flags=re.IGNORECASE | re.DOTALL,
    )

    html, qtd_2 = padrao_link_logo_ordem_invertida.subn(
        r'''<div class="davi-logo-wrap" aria-label="Davi Maia">
          \1
        </div>''',
        html,
    )

    padrao_fallback = re.compile(
        r'<a\s+href="\.\./dashboard_v2/"\s+class="davi-logo-wrap fallback"[^>]*>\s*(<span>DAVI<br>MAIA</span>)\s*</a>',
        flags=re.IGNORECASE | re.DOTALL,
    )

    html, qtd_3 = padrao_fallback.subn(
        r'''<div class="davi-logo-wrap fallback" aria-label="Davi Maia">
          \1
        </div>''',
        html,
    )

    return html, qtd_1 + qtd_2 + qtd_3


def ajustar_topbar_mobile_css(css):
    """
    Com a remoção do botão Painel completo, a logo deve ficar no topo direito.
    """

    bloco_topbar = r'''.topbar {
  position: relative;
  z-index: 2;
  display: flex;
  justify-content: flex-end;
  align-items: center;
  margin-bottom: 34px;
  gap: 12px;
}'''

    css = re.sub(
        r'\.topbar\s*\{.*?\}',
        bloco_topbar,
        css,
        flags=re.DOTALL,
    )

    # Garante que a logo não pareça clicável.
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
  cursor: default;
}'''

    if ".davi-logo-wrap {" in css:
        css = re.sub(
            r'\.davi-logo-wrap\s*\{.*?\}',
            bloco_logo,
            css,
            flags=re.DOTALL,
        )
    else:
        css += "\n\n" + bloco_logo + "\n"

    return css


def corrigir_painel_mobile():
    print()
    print("=" * 80)
    print("AJUSTANDO PAINEL MOBILE")
    print("=" * 80)

    if not os.path.exists(INDEX_MOBILE):
        print(f"[AVISO] index mobile não encontrado: {INDEX_MOBILE}")
        return

    backup_html = criar_backup(INDEX_MOBILE)
    print(f"Backup HTML mobile criado: {backup_html}")

    html = ler_arquivo(INDEX_MOBILE)

    html, qtd_botao = remover_botao_painel_completo_mobile(html)
    html, qtd_logo = transformar_logo_davi_em_elemento_estatico(html)

    salvar_arquivo(INDEX_MOBILE, html)

    print(f"Botões 'Painel completo' removidos: {qtd_botao}")
    print(f"Logos convertidas para elemento sem link: {qtd_logo}")
    print("[OK] index.html mobile atualizado.")

    if os.path.exists(CSS_MOBILE):
        backup_css = criar_backup(CSS_MOBILE)
        print(f"Backup CSS mobile criado: {backup_css}")

        css = ler_arquivo(CSS_MOBILE)
        css = ajustar_topbar_mobile_css(css)
        salvar_arquivo(CSS_MOBILE, css)

        print("[OK] CSS mobile atualizado.")


# ============================================================
# PAINEL COMPLETO DAVI
# ============================================================

def remover_css_botao_mobile_dashboard_v2(html):
    """
    Remove o bloco:
    <style id="atalho-mobile-parceiros-style">...</style>
    """

    padrao = re.compile(
        r'\s*<style\s+id="atalho-mobile-parceiros-style">\s*.*?\s*</style>\s*',
        flags=re.IGNORECASE | re.DOTALL,
    )

    html, qtd = padrao.subn("\n", html)

    return html, qtd


def remover_botao_mobile_dashboard_v2(html):
    """
    Remove o botão flutuante:
    <a id="atalho-mobile-parceiros" ...>...</a>
    """

    padrao = re.compile(
        r'\s*<a\s+[^>]*id="atalho-mobile-parceiros"[^>]*>.*?</a>\s*',
        flags=re.IGNORECASE | re.DOTALL,
    )

    html, qtd_1 = padrao.subn("\n", html)

    padrao_classe = re.compile(
        r'\s*<a\s+[^>]*class="atalho-mobile-parceiros"[^>]*>.*?</a>\s*',
        flags=re.IGNORECASE | re.DOTALL,
    )

    html, qtd_2 = padrao_classe.subn("\n", html)

    return html, qtd_1 + qtd_2


def corrigir_dashboard_v2():
    print()
    print("=" * 80)
    print("AJUSTANDO DASHBOARD V2")
    print("=" * 80)

    if not os.path.exists(INDEX_DASHBOARD_V2):
        print(f"[AVISO] index dashboard_v2 não encontrado: {INDEX_DASHBOARD_V2}")
        return

    backup = criar_backup(INDEX_DASHBOARD_V2)
    print(f"Backup dashboard_v2 criado: {backup}")

    html = ler_arquivo(INDEX_DASHBOARD_V2)

    html, qtd_css = remover_css_botao_mobile_dashboard_v2(html)
    html, qtd_botao = remover_botao_mobile_dashboard_v2(html)

    salvar_arquivo(INDEX_DASHBOARD_V2, html)

    print(f"Blocos CSS do atalho mobile removidos: {qtd_css}")
    print(f"Botões 'Versão Mobile' removidos: {qtd_botao}")
    print("[OK] dashboard_v2/index.html atualizado.")


# ============================================================
# MAIN
# ============================================================

def main():
    print("=" * 80)
    print("REMOÇÃO DE LINKS ENTRE PAINÉIS")
    print("=" * 80)

    corrigir_painel_mobile()
    corrigir_dashboard_v2()

    print()
    print("=" * 80)
    print("PROCESSO CONCLUÍDO")
    print("=" * 80)

    print()
    print("Teste local:")
    print("1) Painel mobile:")
    print("   http://localhost:8000/dashboard_mobile_parceiros/?v=sem-links-v1")
    print()
    print("2) Painel completo:")
    print("   http://localhost:8000/dashboard_v2/?v=sem-botao-mobile-v1")
    print()
    print("Depois pressione CTRL + F5 em ambos.")
    print("=" * 80)


if __name__ == "__main__":
    main()