import os
import json
import math
import shutil
from datetime import datetime


# ============================================================
# CONFIGURAÇÕES
# ============================================================

BASE_DIR = r"C:\Users\user\Documents\Workspace\campanha_2026\alagoas-political-intelligence"

ARQUIVO_BASE_DASHBOARD = os.path.join(
    BASE_DIR,
    "data",
    "dashboard",
    "base_dashboard_v2.json",
)

ARQUIVO_MODULO_PARCEIROS = os.path.join(
    BASE_DIR,
    "data",
    "dashboard",
    "parceiros",
    "modulo_parceiros_estrategicos_v1.json",
)

SAIDA_BASE_DASHBOARD = ARQUIVO_BASE_DASHBOARD


# ============================================================
# FUNÇÕES
# ============================================================

def limpar_json(obj):
    """
    Garante que o JSON final não tenha NaN, Infinity ou valores incompatíveis
    com o navegador.
    """
    if isinstance(obj, dict):
        return {chave: limpar_json(valor) for chave, valor in obj.items()}

    if isinstance(obj, list):
        return [limpar_json(item) for item in obj]

    if isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
        return obj

    return obj


def carregar_json(caminho):
    if not os.path.exists(caminho):
        raise FileNotFoundError(f"Arquivo não encontrado: {caminho}")

    with open(caminho, "r", encoding="utf-8") as f:
        return json.load(f)


def salvar_json(caminho, dados):
    dados = limpar_json(dados)

    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(
            dados,
            f,
            ensure_ascii=False,
            indent=2,
            allow_nan=False,
        )


def criar_backup(caminho):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = caminho.replace(".json", f"_backup_antes_parceiros_{timestamp}.json")

    shutil.copy2(caminho, backup)

    return backup


def main():
    print("=" * 80)
    print("INTEGRAÇÃO — PARCEIROS ESTRATÉGICOS NO BASE DASHBOARD V2")
    print("=" * 80)

    print("Carregando dashboard principal...")
    base_dashboard = carregar_json(ARQUIVO_BASE_DASHBOARD)

    print("Carregando módulo de parceiros...")
    modulo_parceiros = carregar_json(ARQUIVO_MODULO_PARCEIROS)

    backup = criar_backup(ARQUIVO_BASE_DASHBOARD)

    print(f"Backup criado: {backup}")

    resumo = modulo_parceiros.get("resumo_geral", {})

    base_dashboard["parceiros_estrategicos_2026"] = modulo_parceiros

    if "indicadores" not in base_dashboard:
        base_dashboard["indicadores"] = {}

    base_dashboard["indicadores"]["parceiros_processados"] = resumo.get("parceiros_processados", 0)
    base_dashboard["indicadores"]["parceiros_cruzamentos_qualificados"] = resumo.get("total_cruzamentos_qualificados", 0)
    base_dashboard["indicadores"]["parceiros_municipios_convergencia"] = resumo.get("municipios_com_convergencia", 0)
    base_dashboard["indicadores"]["parceiros_vereadores_convergentes"] = resumo.get("vereadores_convergentes", 0)
    base_dashboard["indicadores"]["parceiros_potencial_vereadores_unicos_20pct"] = resumo.get("potencial_vereadores_unicos_20pct", 0)
    base_dashboard["indicadores"]["parceiros_percentual_meta_davi_20pct"] = resumo.get("percentual_meta_davi_potencial_unico_20pct", 0)

    if "metadata" not in base_dashboard:
        base_dashboard["metadata"] = {}

    base_dashboard["metadata"]["ultima_integracao_parceiros"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    base_dashboard["metadata"]["modulo_parceiros_estrategicos"] = "v1"

    salvar_json(SAIDA_BASE_DASHBOARD, base_dashboard)

    print()
    print("Integração concluída com sucesso.")
    print(f"Arquivo atualizado: {SAIDA_BASE_DASHBOARD}")

    print()
    print("Resumo integrado:")
    print(f"Parceiros processados: {resumo.get('parceiros_processados', 0)}")
    print(f"Cruzamentos qualificados: {resumo.get('total_cruzamentos_qualificados', 0)}")
    print(f"Municípios com convergência: {resumo.get('municipios_com_convergencia', 0)}")
    print(f"Vereadores convergentes: {resumo.get('vereadores_convergentes', 0)}")
    print(f"Potencial vereadores únicos 20%: {resumo.get('potencial_vereadores_unicos_20pct', 0)}")
    print(f"% da meta Davi: {resumo.get('percentual_meta_davi_potencial_unico_20pct', 0)}%")

    print("=" * 80)


if __name__ == "__main__":
    main()