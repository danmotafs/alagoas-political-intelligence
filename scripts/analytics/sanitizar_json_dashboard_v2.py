import os
import json
import math
import shutil
from datetime import datetime


BASE_DIR = r"C:\Users\user\Documents\Workspace\campanha_2026\alagoas-political-intelligence"

ARQUIVOS_JSON = [
    os.path.join(BASE_DIR, "data", "dashboard", "base_dashboard_v2.json"),
    os.path.join(BASE_DIR, "data", "dashboard", "meta_eleitoral_davi_federal_2026.json"),
]


def limpar_valores_invalidos(obj):
    """
    Remove valores inválidos para JSON de navegador:
    - NaN
    - Infinity
    - -Infinity

    Substitui por None, que vira null no JSON final.
    """
    if isinstance(obj, dict):
        return {chave: limpar_valores_invalidos(valor) for chave, valor in obj.items()}

    if isinstance(obj, list):
        return [limpar_valores_invalidos(item) for item in obj]

    if isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
        return obj

    return obj


def sanitizar_arquivo(caminho):
    if not os.path.exists(caminho):
        print(f"Arquivo não encontrado, ignorando: {caminho}")
        return

    print("=" * 80)
    print(f"Sanitizando: {caminho}")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = caminho.replace(".json", f"_backup_antes_sanitizacao_{timestamp}.json")

    shutil.copy2(caminho, backup)
    print(f"Backup criado: {backup}")

    with open(caminho, "r", encoding="utf-8") as f:
        conteudo = f.read()

    # Python consegue ler NaN/Infinity por padrão.
    dados = json.loads(conteudo)

    dados_limpos = limpar_valores_invalidos(dados)

    # allow_nan=False garante que nenhum NaN volte para o arquivo.
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(
            dados_limpos,
            f,
            ensure_ascii=False,
            indent=2,
            allow_nan=False
        )

    print("Arquivo sanitizado com sucesso.")
    print("=" * 80)


def main():
    print("SANITIZAÇÃO DOS JSONS DO DASHBOARD V2")
    print("=" * 80)

    for caminho in ARQUIVOS_JSON:
        sanitizar_arquivo(caminho)

    print()
    print("Processo concluído.")
    print("Agora atualize o dashboard local com CTRL + F5.")


if __name__ == "__main__":
    main()