import os
import re
from datetime import datetime


BASE_DIR = r"C:\Users\user\Documents\Workspace\campanha_2026\alagoas-political-intelligence"

ARQUIVO_SCRIPT = os.path.join(
    BASE_DIR,
    "scripts",
    "analytics",
    "cruzar_parceiros_2022_vereadores_2024.py",
)


NOVA_FUNCAO_CALCULAR_INDICES = r'''def calcular_indices(cruzamento, nome_parceiro):
    if cruzamento.empty:
        return cruzamento

    df = cruzamento.copy()

    # ============================================================
    # AJUSTE METODOLÓGICO
    # ============================================================
    # Não basta o vereador ser forte no local.
    # Para haver convergência real, o parceiro também precisa ter presença mínima.
    #
    # Critérios iniciais:
    # - Parceiro com pelo menos 50 votos no local;
    # - Vereador com pelo menos 30 votos no local.
    #
    # Esses limites podem ser calibrados depois conforme curadoria política.
    # ============================================================

    df["votos_parceiro_local"] = df["votos_parceiro_local"].apply(converter_int)
    df["votos_vereador_local"] = df["votos_vereador_local"].apply(converter_int)

    df = df[
        (df["votos_parceiro_local"] >= 50)
        & (df["votos_vereador_local"] >= 30)
    ].copy()

    if df.empty:
        return df

    # ============================================================
    # REMOÇÃO DE DUPLICIDADES
    # ============================================================
    # O mesmo cruzamento pode aparecer duas vezes:
    # 1. município + zona + local
    # 2. município + nome do local
    #
    # Mantemos apenas uma ocorrência por:
    # município + local + vereador.
    # ============================================================

    colunas_dedup = [
        "municipio_norm",
        "local_nome_norm",
        "vereador",
        "partido_vereador",
    ]

    colunas_dedup = [col for col in colunas_dedup if col in df.columns]

    if colunas_dedup:
        df = df.sort_values(
            by=["votos_parceiro_local", "votos_vereador_local"],
            ascending=[False, False],
        ).drop_duplicates(subset=colunas_dedup, keep="first").copy()

    if df.empty:
        return df

    max_votos_parceiro = df["votos_parceiro_local"].max()
    max_votos_vereador = df["votos_vereador_local"].max()

    df["score_parceiro_local"] = (
        df["votos_parceiro_local"] / max_votos_parceiro * 100
    ).round(2) if max_votos_parceiro else 0

    df["score_vereador_local"] = (
        df["votos_vereador_local"] / max_votos_vereador * 100
    ).round(2) if max_votos_vereador else 0

    df["potencial_davi_10pct_local"] = (df["votos_vereador_local"] * 0.10).round(0).astype(int)
    df["potencial_davi_15pct_local"] = (df["votos_vereador_local"] * 0.15).round(0).astype(int)
    df["potencial_davi_20pct_local"] = (df["votos_vereador_local"] * 0.20).round(0).astype(int)

    max_potencial = df["potencial_davi_20pct_local"].max()

    df["score_potencial_davi"] = (
        df["potencial_davi_20pct_local"] / max_potencial * 100
    ).round(2) if max_potencial else 0

    # ============================================================
    # NOVA FÓRMULA
    # ============================================================
    # Antes, o vereador pesava demais e fazia locais com 1 voto da parceira
    # aparecerem no topo.
    #
    # Agora o peso maior fica na presença real do parceiro no local.
    # ============================================================

    df["indice_convergencia"] = (
        df["score_parceiro_local"] * 0.50
        + df["score_vereador_local"] * 0.30
        + df["score_potencial_davi"] * 0.20
    ).round(2)

    def classificar(valor):
        if valor >= 75:
            return "CONVERGÊNCIA ALTA"

        if valor >= 55:
            return "CONVERGÊNCIA MÉDIA"

        if valor >= 35:
            return "CONVERGÊNCIA BAIXA"

        return "CONVERGÊNCIA RESIDUAL"

    df["classificacao_convergencia"] = df["indice_convergencia"].apply(classificar)

    df["acao_recomendada"] = df.apply(
        lambda row: (
            f"Agendar articulação Davi + {nome_parceiro} com o vereador {row.get('vereador', '')} "
            f"no território do local de votação {row.get('local_votacao_parceiro', row.get('local_nome', ''))}. "
            "Objetivo: validar apoio, mapear lideranças locais e pactuar entrada territorial."
        ),
        axis=1,
    )

    df["observacao_metodologica"] = (
        "Cruzamento entre votação do parceiro em 2022 e votação de vereadores em 2024. "
        "Foram considerados apenas locais com presença mínima do parceiro e do vereador, "
        "para evitar convergência artificial baseada em votação residual."
    )

    df = df.sort_values(
        by=[
            "indice_convergencia",
            "votos_parceiro_local",
            "votos_vereador_local",
        ],
        ascending=[False, False, False],
    ).reset_index(drop=True)

    df["ranking_convergencia"] = df.index + 1

    return df
'''


NOVA_FUNCAO_GERAR_JSON_CRUZAMENTO = r'''def gerar_json_cruzamento(id_parceiro, nome_parceiro, df):
    if df.empty:
        dados = {
            "metadata": {
                "titulo": f"Cruzamento Territorial — {nome_parceiro} x Vereadores 2024",
                "id_parceiro": id_parceiro,
                "gerado_em": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            },
            "resumo": {
                "total_cruzamentos": 0,
                "municipios_com_convergencia": 0,
                "vereadores_convergentes": 0,
                "potencial_davi_20pct_local_bruto": 0,
                "potencial_davi_20pct_vereadores_unicos": 0,
            },
            "top_convergencias": [],
            "agenda_recomendada": [],
        }

        return dados

    resumo_municipios = df["municipio"].nunique() if "municipio" in df.columns else df["municipio_norm"].nunique()

    # Potencial bruto local: soma todos os locais.
    potencial_local_bruto_10 = int(df["potencial_davi_10pct_local"].sum())
    potencial_local_bruto_15 = int(df["potencial_davi_15pct_local"].sum())
    potencial_local_bruto_20 = int(df["potencial_davi_20pct_local"].sum())

    # Potencial por vereador único: evita superestimar repetindo o mesmo vereador em múltiplos locais.
    vereadores_unicos = (
        df.sort_values(
            by=["indice_convergencia", "votos_vereador_local"],
            ascending=[False, False],
        )
        .drop_duplicates(subset=["vereador", "partido_vereador"], keep="first")
        .copy()
    )

    potencial_unico_10 = int(vereadores_unicos["potencial_davi_10pct_local"].sum())
    potencial_unico_15 = int(vereadores_unicos["potencial_davi_15pct_local"].sum())
    potencial_unico_20 = int(vereadores_unicos["potencial_davi_20pct_local"].sum())

    dados = {
        "metadata": {
            "titulo": f"Cruzamento Territorial — {nome_parceiro} x Vereadores 2024",
            "id_parceiro": id_parceiro,
            "versao": "v2_metodologia_corrigida",
            "gerado_em": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "fonte": "TSE 2022 parceiro + TSE 2024 vereadores",
            "observacao_metodologica": (
                "O cruzamento identifica locais onde o parceiro teve voto relevante em 2022 "
                "e vereadores tiveram força em 2024. Foram excluídos cruzamentos residuais "
                "com menos de 50 votos do parceiro no local ou menos de 30 votos do vereador. "
                "O objetivo é orientar articulação política, não prever voto automaticamente."
            ),
        },
        "resumo": {
            "total_cruzamentos": int(len(df)),
            "municipios_com_convergencia": int(resumo_municipios),
            "vereadores_convergentes": int(df["vereador"].nunique()),
            "locais_convergentes": int(df["local_nome_norm"].nunique()) if "local_nome_norm" in df.columns else 0,

            "potencial_davi_10pct_local_bruto": potencial_local_bruto_10,
            "potencial_davi_15pct_local_bruto": potencial_local_bruto_15,
            "potencial_davi_20pct_local_bruto": potencial_local_bruto_20,

            "potencial_davi_10pct_vereadores_unicos": potencial_unico_10,
            "potencial_davi_15pct_vereadores_unicos": potencial_unico_15,
            "potencial_davi_20pct_vereadores_unicos": potencial_unico_20,

            "observacao_potencial": (
                "O potencial por vereadores únicos é mais conservador e deve ser usado "
                "como referência principal para meta eleitoral. O potencial local bruto "
                "serve para medir intensidade territorial, mas pode repetir vereadores."
            ),
        },
        "top_convergencias": df.head(100).to_dict(orient="records"),
        "vereadores_unicos_prioritarios": vereadores_unicos.head(100).to_dict(orient="records"),
        "agenda_recomendada": df.head(30)[
            [
                "ranking_convergencia",
                "municipio",
                "local_votacao_parceiro",
                "regiao_estimada",
                "nome_parceiro",
                "vereador",
                "partido_vereador",
                "votos_parceiro_local",
                "votos_vereador_local",
                "indice_convergencia",
                "classificacao_convergencia",
                "potencial_davi_20pct_local",
                "acao_recomendada",
            ]
        ].to_dict(orient="records"),
    }

    return limpar_json(dados)
'''


def substituir_funcao(conteudo, nome_funcao, nova_funcao):
    padrao = rf"def {nome_funcao}\(.*?\n(?=def |\# ============================================================|\Z)"

    novo_conteudo, qtd = re.subn(
        padrao,
        nova_funcao + "\n\n",
        conteudo,
        flags=re.DOTALL,
    )

    if qtd != 1:
        raise RuntimeError(
            f"Não foi possível substituir a função {nome_funcao}. "
            f"Ocorrências encontradas/substituídas: {qtd}"
        )

    return novo_conteudo


def main():
    print("=" * 80)
    print("CORREÇÃO METODOLÓGICA — CRUZAMENTO PARCEIROS x VEREADORES")
    print("=" * 80)

    if not os.path.exists(ARQUIVO_SCRIPT):
        raise FileNotFoundError(f"Script não encontrado: {ARQUIVO_SCRIPT}")

    with open(ARQUIVO_SCRIPT, "r", encoding="utf-8") as f:
        conteudo = f.read()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = ARQUIVO_SCRIPT.replace(".py", f"_backup_metodologia_{timestamp}.py")

    with open(backup, "w", encoding="utf-8") as f:
        f.write(conteudo)

    print(f"Backup criado: {backup}")

    conteudo = substituir_funcao(
        conteudo,
        "calcular_indices",
        NOVA_FUNCAO_CALCULAR_INDICES,
    )

    conteudo = substituir_funcao(
        conteudo,
        "gerar_json_cruzamento",
        NOVA_FUNCAO_GERAR_JSON_CRUZAMENTO,
    )

    with open(ARQUIVO_SCRIPT, "w", encoding="utf-8") as f:
        f.write(conteudo)

    print("Script corrigido com sucesso:")
    print(ARQUIVO_SCRIPT)

    print()
    print("Agora rode novamente:")
    print("python scripts\\analytics\\cruzar_parceiros_2022_vereadores_2024.py")
    print("=" * 80)


if __name__ == "__main__":
    main()