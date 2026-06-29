from __future__ import annotations

import json
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
    backup = caminho.with_name(f"{caminho.name}.bak_sprint01c_{timestamp}")
    backup.write_text(caminho.read_text(encoding="utf-8"), encoding="utf-8")
    print(f"[OK] Backup criado: {backup}")


def atualizar_texto_arquivo(caminho: Path, substituicoes: list[tuple[str, str]]) -> None:
    if not caminho.exists():
        print(f"[AVISO] Arquivo não encontrado: {caminho}")
        return

    conteudo = caminho.read_text(encoding="utf-8")
    original = conteudo

    for antigo, novo in substituicoes:
        conteudo = conteudo.replace(antigo, novo)

    if conteudo == original:
        print(f"[INFO] Nenhuma substituição textual aplicada em: {caminho}")
        return

    fazer_backup(caminho)
    caminho.write_text(conteudo, encoding="utf-8")
    print(f"[OK] Texto atualizado em: {caminho}")


def atualizar_json_base(caminho: Path) -> None:
    if not caminho.exists():
        print(f"[AVISO] JSON não encontrado: {caminho}")
        return

    dados = json.loads(caminho.read_text(encoding="utf-8"))

    metadata = dados.setdefault("metadata", {})
    metadata["cargo"] = "Deputada Estadual em mandato"
    metadata["tipo_candidatura"] = "Reeleição"
    metadata["status"] = (
        "Estrutura criada; Gabi Gonçalves registrada como Deputada Estadual em mandato "
        "e candidata à reeleição em 2026."
    )

    indicadores_gabi = dados.setdefault("indicadores_gabi", {})
    indicadores_gabi["situacao_politica"] = "Deputada Estadual em mandato"
    indicadores_gabi["tipo_candidatura"] = "Reeleição"
    indicadores_gabi["status_meta"] = "Meta de reeleição será calibrada no Sprint 02"

    fazer_backup(caminho)
    caminho.write_text(
        json.dumps(dados, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"[OK] JSON base atualizado: {caminho}")


def atualizar_json_meta(caminho: Path) -> None:
    if not caminho.exists():
        print(f"[AVISO] JSON não encontrado: {caminho}")
        return

    dados = json.loads(caminho.read_text(encoding="utf-8"))

    metadata = dados.setdefault("metadata", {})
    metadata["projeto"] = "Meta Eleitoral Gabi Gonçalves Reeleição 2026"
    metadata["status"] = "Aguardando definição estratégica da meta de reeleição"

    meta = dados.setdefault("meta_eleitoral_gabi_2026", {})
    meta["cargo"] = "Deputada Estadual em mandato"
    meta["tipo_candidatura"] = "Reeleição"
    meta["observacao"] = (
        "Meta será definida após análise do quociente eleitoral estadual, histórico de votação, "
        "base territorial, desempenho político do mandato e alianças firmadas."
    )

    fazer_backup(caminho)
    caminho.write_text(
        json.dumps(dados, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"[OK] JSON de meta atualizado: {caminho}")


def main() -> None:
    root = detectar_raiz_projeto()

    painel_dir = root / "parceiros" / "gabi-goncalves"
    index_path = painel_dir / "index.html"
    app_path = painel_dir / "app.js"

    base_json = root / "data" / "dashboard" / "parceiros" / "gabi-goncalves" / "base_dashboard_gabi_v1.json"
    meta_json = root / "data" / "dashboard" / "parceiros" / "gabi-goncalves" / "meta_eleitoral_gabi_estadual_2026.json"

    substituicoes_html = [
        ("Pré-candidata a Deputada Estadual", "Deputada Estadual · Candidata à reeleição"),
        ("Pré-candidata à Deputada Estadual", "Deputada Estadual · Candidata à reeleição"),
        ("Pré-candidata a deputada estadual", "Deputada Estadual · Candidata à reeleição"),
        ("Pré-candidata à deputada estadual", "Deputada Estadual · Candidata à reeleição"),
        ("pré-candidata a deputada estadual", "Deputada Estadual · Candidata à reeleição"),
        ("pré-candidata à deputada estadual", "Deputada Estadual · Candidata à reeleição"),
        ("Cruzamento Davi Maia x Gabi Gonçalves", "Davi Maia + Gabi Gonçalves"),
        ("Cruzamento Davi Maia x Gabi Goncalves", "Davi Maia + Gabi Gonçalves"),
    ]

    substituicoes_js = [
        ("Cruzamento Davi Maia x Gabi Gonçalves", "Davi Maia + Gabi Gonçalves"),
        ("Cruzamento Davi Maia x Gabi Goncalves", "Davi Maia + Gabi Gonçalves"),
        ("Pré-candidata a Deputada Estadual", "Deputada Estadual · Candidata à reeleição"),
        ("Pré-candidata à Deputada Estadual", "Deputada Estadual · Candidata à reeleição"),
    ]

    print("============================================================")
    print("SPRINT 01C — AJUSTES TEXTUAIS GABI GONÇALVES")
    print("============================================================")
    print(f"[INFO] Raiz detectada: {root}")

    atualizar_texto_arquivo(index_path, substituicoes_html)
    atualizar_texto_arquivo(app_path, substituicoes_js)
    atualizar_json_base(base_json)
    atualizar_json_meta(meta_json)

    print("")
    print("============================================================")
    print("SPRINT 01C CONCLUÍDO")
    print("============================================================")
    print("Alterações aplicadas:")
    print("  1. Gabi tratada como Deputada Estadual em mandato.")
    print("  2. Candidatura ajustada para reeleição.")
    print("  3. Título alterado para: Davi Maia + Gabi Gonçalves.")
    print("")
    print("Teste local:")
    print("  cd C:\\Users\\user\\Documents\\Workspace\\campanha_2026\\alagoas-political-intelligence")
    print("  python -m http.server 8000")
    print("")
    print("Abra:")
    print("  http://localhost:8000/parceiros/gabi-goncalves/")
    print("============================================================")


if __name__ == "__main__":
    main()