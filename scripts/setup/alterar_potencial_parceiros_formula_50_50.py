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
    # AJUSTE METODOLÓGICO — POTENCIAL DE VOTOS 50/50
    # ============================================================
    # Nova fórmula solicitada:
    #
    # Potencial de votos =
    # 50% dos votos do deputado/parceiro no território
    # +
    # 50% dos votos do vereador convergente no mesmo local
    #
    # Exemplo:
    # Parceiro no local: 1.133 votos
    # Vereador no local: 278 votos
    # Potencial = 566,5 + 139 = 705 votos
    #
    # Observação:
    # Continua sendo uma estimativa operacional de influência territorial,
    # não uma previsão eleitoral nem apoio confirmado.
    # ============================================================

    df["votos_parceiro_local"] = df["votos_parceiro_local"].apply(converter_int)
    df["votos_vereador_local"] = df["votos_vereador_local"].apply(converter_int)

    # Mantemos o filtro mínimo para evitar convergência artificial.
    df = df[
        (df["votos_parceiro_local"] >= 50)
        & (df["votos_vereador_local"] >= 30)
    ].copy()

    if df.empty:
        return df

    # Remove duplicidades causadas pelo cruzamento por número do local e por nome do local.
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

    # Nova fórmula de potencial.
    df["potencial_votos_50pct_parceiro"] = (df["votos_parceiro_local"] * 0.50).round(0).astype(int)
    df["potencial_votos_50pct_vereador"] = (df["votos_vereador_local"] * 0.50).round(0).astype(int)

    df["potencial_votos"] = (
        df["potencial_votos_50pct_parceiro"]
        + df["potencial_votos_50pct_vereador"]
    ).astype(int)

    # Mantém nomes antigos para compatibilidade com os painéis já criados.
    # A partir desta versão, esses campos passam a carregar a nova fórmula 50/50.
    df["potencial_davi_10pct_local"] = df["potencial_votos"]
    df["potencial_davi_15pct_local"] = df["potencial_votos"]
    df["potencial_davi_20pct_local"] = df["potencial_votos"]

    max_votos_parceiro = df["votos_parceiro_local"].max()
    max_votos_vereador = df["votos_vereador_local"].max()
    max_potencial = df["potencial_votos"].max()

    df["score_parceiro_local"] = (
        df["votos_parceiro_local"] / max_votos_parceiro * 100
    ).round(2) if max_votos_parceiro else 0

    df["score_vereador_local"] = (
        df["votos_vereador_local"] / max_votos_vereador * 100
    ).round(2) if max_votos_vereador else 0

    df["score_potencial_davi"] = (
        df["potencial_votos"] / max_potencial * 100
    ).round(2) if max_potencial else 0

    # Índice de convergência:
    # - parceiro pesa mais, porque estamos medindo utilidade do parceiro;
    # - vereador pesa como capacidade local de ativação;
    # - potencial pondera o volume total estimado pela nova fórmula.
    df["indice_convergencia"] = (
        df["score_parceiro_local"] * 0.45
        + df["score_vereador_local"] * 0.25
        + df["score_potencial_davi"] * 0.30
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

    df["formula_potencial_votos"] = (
        "50% dos votos do parceiro no território + "
        "50% dos votos do vereador convergente no mesmo local de votação"
    )

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
        "O potencial de votos usa a fórmula 50/50: metade dos votos do parceiro no território "
        "mais metade dos votos do vereador convergente no mesmo local. "
        "A métrica orienta articulação política e não representa voto garantido."
    )

    df = df.sort_values(
        by=[
            "potencial_votos",
            "indice_convergencia",
            "votos_parceiro_local",
            "votos_vereador_local",
        ],
        ascending=[False, False, False, False],
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
                "formula_potencial_votos": (
                    "50% dos votos do parceiro no território + "
                    "50% dos votos do vereador convergente no mesmo local de votação"
                ),
            },
            "resumo": {
                "total_cruzamentos": 0,
                "municipios_com_convergencia": 0,
                "vereadores_convergentes": 0,
                "potencial_votos_bruto": 0,
                "potencial_votos_vereadores_unicos": 0,
            },
            "top_convergencias": [],
            "agenda_recomendada": [],
        }

        return dados

    resumo_municipios = df["municipio"].nunique() if "municipio" in df.columns else df["municipio_norm"].nunique()

    # Potencial bruto local: soma todas as convergências qualificadas.
    potencial_bruto = int(df["potencial_votos"].sum())

    # Potencial por vereador único:
    # evita superestimar repetindo o mesmo vereador em múltiplos locais.
    vereadores_unicos = (
        df.sort_values(
            by=["potencial_votos", "indice_convergencia", "votos_vereador_local"],
            ascending=[False, False, False],
        )
        .drop_duplicates(subset=["vereador", "partido_vereador"], keep="first")
        .copy()
    )

    potencial_unico = int(vereadores_unicos["potencial_votos"].sum())

    dados = {
        "metadata": {
            "titulo": f"Cruzamento Territorial — {nome_parceiro} x Vereadores 2024",
            "id_parceiro": id_parceiro,
            "versao": "v3_formula_50_50",
            "gerado_em": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "fonte": "TSE 2022 parceiro + TSE 2024 vereadores",
            "formula_potencial_votos": (
                "50% dos votos do parceiro no território + "
                "50% dos votos do vereador convergente no mesmo local de votação"
            ),
            "observacao_metodologica": (
                "O cruzamento identifica locais onde o parceiro teve voto relevante em 2022 "
                "e vereadores tiveram força em 2024. Foram excluídos cruzamentos residuais "
                "com menos de 50 votos do parceiro no local ou menos de 30 votos do vereador. "
                "O potencial de votos é uma estimativa operacional para orientar articulação política, "
                "não uma previsão eleitoral automática."
            ),
        },
        "resumo": {
            "total_cruzamentos": int(len(df)),
            "municipios_com_convergencia": int(resumo_municipios),
            "vereadores_convergentes": int(df["vereador"].nunique()),
            "locais_convergentes": int(df["local_nome_norm"].nunique()) if "local_nome_norm" in df.columns else 0,

            "potencial_votos_bruto": potencial_bruto,
            "potencial_votos_vereadores_unicos": potencial_unico,

            # Campos antigos mantidos para compatibilidade.
            "potencial_davi_10pct_local_bruto": potencial_bruto,
            "potencial_davi_15pct_local_bruto": potencial_bruto,
            "potencial_davi_20pct_local_bruto": potencial_bruto,

            "potencial_davi_10pct_vereadores_unicos": potencial_unico,
            "potencial_davi_15pct_vereadores_unicos": potencial_unico,
            "potencial_davi_20pct_vereadores_unicos": potencial_unico,

            "observacao_potencial": (
                "O potencial por vereadores únicos é a métrica conservadora. "
                "A fórmula vigente considera 50% dos votos do parceiro no território "
                "mais 50% dos votos do vereador convergente no mesmo local."
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
                "potencial_votos_50pct_parceiro",
                "potencial_votos_50pct_vereador",
                "potencial_votos",
                "indice_convergencia",
                "classificacao_convergencia",
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
    print("ALTERAÇÃO DO POTENCIAL DE VOTOS — FÓRMULA 50/50")
    print("=" * 80)

    if not os.path.exists(ARQUIVO_SCRIPT):
        raise FileNotFoundError(f"Script não encontrado: {ARQUIVO_SCRIPT}")

    with open(ARQUIVO_SCRIPT, "r", encoding="utf-8") as f:
        conteudo = f.read()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = ARQUIVO_SCRIPT.replace(".py", f"_backup_formula_50_50_{timestamp}.py")

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

    print("Script atualizado com sucesso:")
    print(ARQUIVO_SCRIPT)

    print()
    print("Agora rode, nesta ordem:")
    print("1) python scripts\\analytics\\cruzar_parceiros_2022_vereadores_2024.py")
    print("2) python scripts\\analytics\\gerar_modulo_parceiros_estrategicos_dashboard.py")
    print("3) python scripts\\analytics\\integrar_parceiros_estrategicos_base_dashboard_v2.py")
    print("4) python scripts\\setup\\criar_dashboard_mobile_parceiros_v2.py")
    print("=" * 80)


if __name__ == "__main__":
    main()