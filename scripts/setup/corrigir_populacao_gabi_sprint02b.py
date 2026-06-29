from __future__ import annotations

import json
import subprocess
import sys
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
    backup = caminho.with_name(f"{caminho.name}.bak_populacao_sprint02b_{timestamp}")
    backup.write_text(caminho.read_text(encoding="utf-8"), encoding="utf-8")
    print(f"[OK] Backup criado: {backup}")


def corrigir_funcao_converter_numero(script_path: Path) -> None:
    if not script_path.exists():
        raise FileNotFoundError(f"Script não encontrado: {script_path}")

    conteudo = script_path.read_text(encoding="utf-8")

    inicio = conteudo.find("def converter_numero(")
    fim = conteudo.find("\ndef normalizar_0_100", inicio)

    if inicio == -1 or fim == -1:
        raise RuntimeError(
            "Não consegui localizar corretamente a função converter_numero "
            "ou a função normalizar_0_100 no script do Sprint 02."
        )

    nova_funcao = '''def converter_numero(serie: pd.Series) -> pd.Series:
    """
    Converte séries numéricas ou textuais para número sem inflar valores.

    Problema corrigido:
    - Quando o pandas lê 3220104 como 3220104.0, transformar em string e remover
      todos os pontos gera 32201040.
    - Esta versão preserva valores já numéricos e só trata separadores quando o dado
      realmente vem como texto.
    """
    if serie is None:
        return pd.Series(dtype="float64")

    if pd.api.types.is_numeric_dtype(serie):
        return pd.to_numeric(serie, errors="coerce").fillna(0)

    def parse_valor(valor: object) -> float:
        if valor is None or pd.isna(valor):
            return 0.0

        texto = str(valor).strip()

        if texto == "":
            return 0.0

        texto = texto.replace("\\u00a0", " ")

        # Caso brasileiro clássico: 3.220.104 ou 2.442.894
        if re.fullmatch(r"\\d{1,3}(\\.\\d{3})+", texto):
            return float(texto.replace(".", ""))

        # Caso brasileiro com decimal: 1.234,56
        if re.fullmatch(r"\\d{1,3}(\\.\\d{3})+,\\d+", texto):
            return float(texto.replace(".", "").replace(",", "."))

        # Caso decimal simples vindo do pandas: 3220104.0
        if re.fullmatch(r"\\d+\\.0+", texto):
            return float(texto)

        # Caso número inteiro textual: 3220104
        if re.fullmatch(r"\\d+", texto):
            return float(texto)

        # Caso decimal com vírgula: 1234,56
        if re.fullmatch(r"\\d+,\\d+", texto):
            return float(texto.replace(",", "."))

        # Fallback: remove caracteres não numéricos mantendo ponto, vírgula e sinal.
        texto_limpo = re.sub(r"[^0-9,.\\-]", "", texto)

        if texto_limpo.count(",") == 1 and texto_limpo.count(".") >= 1:
            texto_limpo = texto_limpo.replace(".", "").replace(",", ".")
        elif texto_limpo.count(",") == 1 and texto_limpo.count(".") == 0:
            texto_limpo = texto_limpo.replace(",", ".")

        try:
            return float(texto_limpo)
        except ValueError:
            return 0.0

    return serie.apply(parse_valor).astype(float)
'''

    novo_conteudo = conteudo[:inicio] + nova_funcao + conteudo[fim:]

    # Garante que o script do Sprint 02 tenha import re.
    if "import re\n" not in novo_conteudo:
        novo_conteudo = novo_conteudo.replace("import math\n", "import math\nimport re\n")

    fazer_backup(script_path)
    script_path.write_text(novo_conteudo, encoding="utf-8")
    print(f"[OK] Função converter_numero corrigida em: {script_path}")


def rodar_sprint02(root: Path) -> None:
    script = root / "scripts" / "analytics" / "gerar_base_eleitoral_gabi_sprint02.py"

    if not script.exists():
        raise FileNotFoundError(f"Script do Sprint 02 não encontrado: {script}")

    print("")
    print("[INFO] Regenerando os arquivos do Sprint 02...")
    print(f"[INFO] Executando: {script}")

    resultado = subprocess.run(
        [sys.executable, str(script)],
        cwd=str(root),
        text=True,
        capture_output=True,
    )

    if resultado.stdout:
        print(resultado.stdout)

    if resultado.stderr:
        print(resultado.stderr)

    if resultado.returncode != 0:
        raise RuntimeError("Erro ao regenerar o Sprint 02.")

    print("[OK] Sprint 02 regenerado com a conversão numérica corrigida.")


def validar_dashboard_json(root: Path) -> None:
    json_path = (
        root
        / "data"
        / "dashboard"
        / "parceiros"
        / "gabi-goncalves"
        / "base_dashboard_gabi_v1.json"
    )

    if not json_path.exists():
        print(f"[AVISO] JSON do dashboard não encontrado: {json_path}")
        return

    dados = json.loads(json_path.read_text(encoding="utf-8"))

    populacao = (
        dados
        .get("indicadores_alagoas", {})
        .get("populacao_total")
    )

    print("")
    print("============================================================")
    print("VALIDAÇÃO")
    print("============================================================")

    if isinstance(populacao, int):
        print(f"População total no JSON do dashboard: {populacao:,}".replace(",", "."))
    else:
        print(f"População total no JSON do dashboard: {populacao}")

    if populacao == 3220104:
        print("[OK] População corrigida com sucesso: 3.220.104")
    elif populacao == 32201040:
        print("[ERRO] A população ainda está inflada: 32.201.040")
        print("[AÇÃO] Envie o log completo do Sprint 02 para revisão.")
    else:
        print("[AVISO] População diferente do esperado. Confira a base municipal de origem.")


def main() -> None:
    root = detectar_raiz_projeto()

    script_sprint02 = root / "scripts" / "analytics" / "gerar_base_eleitoral_gabi_sprint02.py"

    print("============================================================")
    print("SPRINT 02B — CORREÇÃO DA POPULAÇÃO GABI")
    print("============================================================")
    print(f"[INFO] Raiz detectada: {root}")

    corrigir_funcao_converter_numero(script_sprint02)
    rodar_sprint02(root)
    validar_dashboard_json(root)

    print("")
    print("============================================================")
    print("SPRINT 02B CONCLUÍDO")
    print("============================================================")
    print("Agora teste o painel:")
    print("  cd C:\\Users\\user\\Documents\\Workspace\\campanha_2026\\alagoas-political-intelligence")
    print("  python -m http.server 8000")
    print("")
    print("Abra:")
    print("  http://localhost:8000/parceiros/gabi-goncalves/")
    print("")
    print("Depois faça Ctrl + F5 no navegador para forçar atualização.")
    print("============================================================")


if __name__ == "__main__":
    main()