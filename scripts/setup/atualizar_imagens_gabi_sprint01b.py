from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path


EXTENSOES_SUPORTADAS = {".png", ".jpg", ".jpeg", ".webp", ".svg"}


def detectar_raiz_projeto() -> Path:
    caminho_script = Path(__file__).resolve()

    if (
        caminho_script.parent.name.lower() == "setup"
        and caminho_script.parent.parent.name.lower() == "scripts"
    ):
        return caminho_script.parent.parent.parent

    return Path.cwd()


def localizar_asset(assets_dir: Path, nomes_base: list[str]) -> Path | None:
    if not assets_dir.exists():
        return None

    arquivos = [
        p for p in assets_dir.iterdir()
        if p.is_file() and p.suffix.lower() in EXTENSOES_SUPORTADAS
    ]

    nomes_normalizados = [n.lower().strip() for n in nomes_base]

    for nome in nomes_normalizados:
        for arquivo in arquivos:
            if arquivo.stem.lower() == nome:
                return arquivo

    for nome in nomes_normalizados:
        for arquivo in arquivos:
            if nome in arquivo.stem.lower():
                return arquivo

    return None


def fazer_backup(caminho: Path) -> None:
    if not caminho.exists():
        return

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = caminho.with_name(f"{caminho.name}.bak_imagens_gabi_{timestamp}")
    backup.write_text(caminho.read_text(encoding="utf-8"), encoding="utf-8")
    print(f"[OK] Backup criado: {backup}")


def atualizar_html(index_path: Path, logo_nome: str, foto_nome: str) -> None:
    if not index_path.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {index_path}")

    html = index_path.read_text(encoding="utf-8")

    novo_aside = f'''<aside class="candidate-card candidate-card-complete">
          <div class="candidate-photo-panel">
            <div class="photo-glow photo-glow-yellow"></div>
            <div class="photo-glow photo-glow-pink"></div>

            <img
              class="candidate-photo"
              src="assets/{foto_nome}"
              alt="Foto de Gabi Gonçalves"
            />

            <div class="photo-gradient"></div>

            <div class="candidate-photo-caption">
              <span>Parceira política</span>
              <strong>Gabi Gonçalves</strong>
              <small>Pré-candidata a Deputada Estadual</small>
            </div>
          </div>

          <div class="campaign-logo-panel">
            <div class="logo-mini-label">Identidade 2026</div>

            <img
              class="campaign-logo-main"
              src="assets/{logo_nome}"
              alt="Logomarca Gabi Gonçalves 2026"
            />

            <p>
              Módulo parceiro da rede de inteligência territorial Davi Maia 2026.
            </p>
          </div>
        </aside>'''

    padrao_aside = r'<aside class="candidate-card">.*?</aside>'

    if re.search(padrao_aside, html, flags=re.DOTALL):
        html = re.sub(
            padrao_aside,
            novo_aside,
            html,
            count=1,
            flags=re.DOTALL,
        )
    elif re.search(r'<aside class="candidate-card candidate-card-complete">.*?</aside>', html, flags=re.DOTALL):
        html = re.sub(
            r'<aside class="candidate-card candidate-card-complete">.*?</aside>',
            novo_aside,
            html,
            count=1,
            flags=re.DOTALL,
        )
    else:
        raise RuntimeError(
            "Não encontrei o bloco <aside class=\"candidate-card\"> no index.html. "
            "Confira se o arquivo foi alterado manualmente."
        )

    index_path.write_text(html, encoding="utf-8")
    print(f"[OK] HTML atualizado com foto e logo: {index_path}")


def atualizar_css(css_path: Path) -> None:
    if not css_path.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {css_path}")

    css = css_path.read_text(encoding="utf-8")

    marcador_inicio = "/* ===== SPRINT01B_GABI_FOTO_LOGO_INICIO ===== */"
    marcador_fim = "/* ===== SPRINT01B_GABI_FOTO_LOGO_FIM ===== */"

    bloco_css = f"""
{marcador_inicio}

.candidate-card-complete {{
  display: grid;
  grid-template-rows: minmax(320px, 1fr) auto;
  gap: 18px;
  padding: 18px;
  border-radius: var(--radius-xl);
  background:
    radial-gradient(circle at 20% 0%, rgba(241, 210, 20, .20), transparent 30%),
    radial-gradient(circle at 90% 15%, rgba(226, 128, 178, .24), transparent 34%),
    rgba(255, 255, 255, .92);
}}

.candidate-photo-panel {{
  position: relative;
  min-height: 390px;
  overflow: hidden;
  border-radius: 26px;
  background:
    linear-gradient(145deg, var(--blue-900), var(--blue-700));
  border: 1px solid rgba(255, 255, 255, .28);
  box-shadow: 0 24px 52px rgba(11, 31, 77, .24);
}}

.photo-glow {{
  position: absolute;
  border-radius: 999px;
  filter: blur(4px);
  opacity: .78;
  z-index: 1;
}}

.photo-glow-yellow {{
  width: 170px;
  height: 170px;
  right: -54px;
  top: -48px;
  background: rgba(241, 210, 20, .40);
}}

.photo-glow-pink {{
  width: 190px;
  height: 190px;
  left: -70px;
  bottom: 26px;
  background: rgba(226, 128, 178, .32);
}}

.candidate-photo {{
  position: absolute;
  inset: 0;
  z-index: 2;
  width: 100%;
  height: 100%;
  object-fit: cover;
  object-position: center top;
  transform: scale(1.01);
}}

.photo-gradient {{
  position: absolute;
  inset: 0;
  z-index: 3;
  background:
    linear-gradient(180deg, rgba(11, 31, 77, .02) 0%, rgba(11, 31, 77, .14) 45%, rgba(11, 31, 77, .88) 100%),
    linear-gradient(90deg, rgba(11, 31, 77, .32), transparent 42%);
}}

.candidate-photo-caption {{
  position: absolute;
  left: 18px;
  right: 18px;
  bottom: 18px;
  z-index: 4;
  padding: 18px;
  border-radius: 22px;
  background: rgba(11, 31, 77, .74);
  border: 1px solid rgba(255, 255, 255, .22);
  color: #ffffff;
  backdrop-filter: blur(14px);
}}

.candidate-photo-caption span {{
  display: block;
  margin-bottom: 8px;
  color: var(--yellow-500);
  font-size: 11px;
  font-weight: 900;
  letter-spacing: .12em;
  text-transform: uppercase;
}}

.candidate-photo-caption strong {{
  display: block;
  font-size: 30px;
  line-height: .95;
  letter-spacing: -0.05em;
}}

.candidate-photo-caption small {{
  display: block;
  margin-top: 8px;
  color: rgba(255, 255, 255, .78);
  font-weight: 700;
}}

.campaign-logo-panel {{
  display: grid;
  place-items: center;
  text-align: center;
  min-height: 170px;
  padding: 18px;
  border-radius: 24px;
  background:
    radial-gradient(circle at 20% 10%, rgba(241, 210, 20, .22), transparent 32%),
    linear-gradient(180deg, #ffffff, #EEF3FF);
  border: 1px solid var(--line);
}}

.logo-mini-label {{
  display: inline-flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 10px;
  padding: 7px 10px;
  border-radius: 999px;
  background: rgba(26, 67, 146, .08);
  color: var(--blue-700);
  font-size: 10px;
  font-weight: 900;
  letter-spacing: .12em;
  text-transform: uppercase;
}}

.campaign-logo-main {{
  display: block;
  width: min(100%, 285px);
  max-height: 118px;
  object-fit: contain;
}}

.campaign-logo-panel p {{
  max-width: 280px;
  margin: 12px 0 0;
  color: var(--muted);
  font-size: 13px;
  line-height: 1.45;
}}

@media (max-width: 980px) {{
  .candidate-card-complete {{
    grid-template-columns: 1fr 1fr;
    grid-template-rows: auto;
  }}

  .candidate-photo-panel {{
    min-height: 340px;
  }}

  .campaign-logo-panel {{
    min-height: 340px;
  }}
}}

@media (max-width: 680px) {{
  .candidate-card-complete {{
    grid-template-columns: 1fr;
  }}

  .candidate-photo-panel {{
    min-height: 390px;
  }}

  .campaign-logo-panel {{
    min-height: 170px;
  }}

  .candidate-photo-caption strong {{
    font-size: 26px;
  }}
}}

{marcador_fim}
"""

    padrao_bloco = rf"{re.escape(marcador_inicio)}.*?{re.escape(marcador_fim)}"

    if re.search(padrao_bloco, css, flags=re.DOTALL):
        css = re.sub(padrao_bloco, bloco_css.strip(), css, flags=re.DOTALL)
    else:
        css = css.rstrip() + "\n\n" + bloco_css.strip() + "\n"

    css_path.write_text(css, encoding="utf-8")
    print(f"[OK] CSS atualizado com bloco visual de foto + logo: {css_path}")


def main() -> None:
    root = detectar_raiz_projeto()

    painel_dir = root / "parceiros" / "gabi-goncalves"
    assets_dir = painel_dir / "assets"

    index_path = painel_dir / "index.html"
    css_path = painel_dir / "styles.css"

    print("============================================================")
    print("SPRINT 01B — FOTO + LOGO NO PAINEL DA GABI")
    print("============================================================")
    print(f"[INFO] Raiz detectada: {root}")
    print(f"[INFO] Pasta de assets: {assets_dir}")

    logo = localizar_asset(
        assets_dir,
        [
            "logo-gabi-2026",
            "logo_gabi_2026",
            "logo-gabi",
            "gabi-logo",
        ],
    )

    foto = localizar_asset(
        assets_dir,
        [
            "foto-gabi",
            "foto_gabi",
            "gabi-foto",
            "gabi",
        ],
    )

    if not logo:
        print("[ERRO] Não encontrei a logomarca da Gabi.")
        print("[DICA] Salve o arquivo como logo-gabi-2026.png, .jpg ou .webp dentro de:")
        print(f"       {assets_dir}")
        return

    if not foto:
        print("[ERRO] Não encontrei a foto da Gabi.")
        print("[DICA] Salve o arquivo como foto-gabi.png, .jpg ou .webp dentro de:")
        print(f"       {assets_dir}")
        return

    print(f"[OK] Logo encontrada: {logo.name}")
    print(f"[OK] Foto encontrada: {foto.name}")

    fazer_backup(index_path)
    fazer_backup(css_path)

    atualizar_html(index_path, logo.name, foto.name)
    atualizar_css(css_path)

    print("")
    print("============================================================")
    print("SPRINT 01B CONCLUÍDO")
    print("============================================================")
    print("Agora teste localmente:")
    print("  cd C:\\Users\\user\\Documents\\Workspace\\campanha_2026\\alagoas-political-intelligence")
    print("  python -m http.server 8000")
    print("")
    print("Abra:")
    print("  http://localhost:8000/parceiros/gabi-goncalves/")
    print("============================================================")


if __name__ == "__main__":
    main()