import os
import pandas as pd


# ============================================================
# CONFIGURAÇÕES
# ============================================================

BASE_DIR = r"C:\Users\user\Documents\Workspace\campanha_2026\alagoas-political-intelligence"

REFERENCE_DIR = os.path.join(BASE_DIR, "data", "reference")
os.makedirs(REFERENCE_DIR, exist_ok=True)

SAIDA_CSV = os.path.join(REFERENCE_DIR, "parceiros_davi_2026.csv")
SAIDA_XLSX = os.path.join(REFERENCE_DIR, "parceiros_davi_2026.xlsx")


# ============================================================
# BASE INICIAL DE PARCEIROS
# ============================================================

dados = [
    {
        "id_parceiro": "gabi-goncalves",
        "nome_parceiro": "Gabi Gonçalves",
        "nome_urna_2022": "GABI GONÇALVES",
        "cargo_atual": "Deputada Estadual",
        "cargo_disputado_2022": "Deputado Estadual",
        "ano_base_eleitoral": 2022,
        "uf_base_eleitoral": "AL",
        "partido_2022": "",
        "partido_atual": "",
        "grupo_politico": "",
        "relacao_com_davi": "Parceira estabelecida",
        "status_parceria": "Confirmada",
        "mes_fechamento_parceria": "",
        "prioridade_politica": "Alta",
        "tipo_parceiro": "Deputada Estadual",
        "base_territorial_principal": "",
        "municipios_prioritarios": "",
        "segmentos_de_atuacao": "",
        "utilidade_esperada_para_davi": (
            "Abrir interlocução com vereadores e lideranças locais em territórios "
            "onde possui capital eleitoral comprovado em 2022."
        ),
        "tipo_de_utilidade": "Territorial / Articulação com vereadores",
        "risco_politico": "",
        "observacao": (
            "Primeira parceira estruturada no painel. Será usada como modelo para "
            "cruzamento entre votação estadual de 2022 e votação de vereadores em 2024."
        ),
        "arquivo_votacao_secao": "data/raw/tse_2022/votacao_secao_2022_AL.csv",
        "arquivo_saida_territorial": "data/dashboard/parceiros/gabi-goncalves/gabi_territorial_2022.json",
        "arquivo_saida_cruzamento": "data/dashboard/parceiros/gabi-goncalves/cruzamento_gabi_2022_vereadores_2024.json",
        "incluir_no_dashboard": "SIM",
        "ordem_dashboard": 1,
    }
]


# ============================================================
# COLUNAS PADRÃO
# ============================================================

colunas = [
    "id_parceiro",
    "nome_parceiro",
    "nome_urna_2022",
    "cargo_atual",
    "cargo_disputado_2022",
    "ano_base_eleitoral",
    "uf_base_eleitoral",
    "partido_2022",
    "partido_atual",
    "grupo_politico",
    "relacao_com_davi",
    "status_parceria",
    "mes_fechamento_parceria",
    "prioridade_politica",
    "tipo_parceiro",
    "base_territorial_principal",
    "municipios_prioritarios",
    "segmentos_de_atuacao",
    "utilidade_esperada_para_davi",
    "tipo_de_utilidade",
    "risco_politico",
    "observacao",
    "arquivo_votacao_secao",
    "arquivo_saida_territorial",
    "arquivo_saida_cruzamento",
    "incluir_no_dashboard",
    "ordem_dashboard",
]


def main():
    print("=" * 80)
    print("CRIANDO BASE DE REFERÊNCIA — PARCEIROS DAVI 2026")
    print("=" * 80)

    df = pd.DataFrame(dados, columns=colunas)

    df.to_csv(SAIDA_CSV, index=False, encoding="utf-8-sig")
    df.to_excel(SAIDA_XLSX, index=False)

    print("Arquivos gerados com sucesso:")
    print(SAIDA_CSV)
    print(SAIDA_XLSX)

    print()
    print("Parceiros cadastrados:")
    for _, row in df.iterrows():
        print(f"- {row['nome_parceiro']} | {row['cargo_atual']} | {row['status_parceria']}")

    print("=" * 80)


if __name__ == "__main__":
    main()