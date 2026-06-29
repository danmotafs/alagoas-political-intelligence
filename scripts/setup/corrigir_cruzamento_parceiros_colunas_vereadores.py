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


NOVA_FUNCAO_PREPARAR_BASE_VEREADORES = r'''def preparar_base_vereadores():
    arquivo_vereadores = localizar_arquivo_vereadores()

    print(f"Base de vereadores usada: {arquivo_vereadores}")

    df = ler_csv(arquivo_vereadores)

    print("Colunas disponíveis na base de vereadores:")
    for col in df.columns:
        print(f"- {col}")

    col_municipio = escolher_coluna(
        df,
        ["municipio", "NM_MUNICIPIO", "municipio_original"],
        obrigatoria=True,
        nome_logico="município",
    )

    col_zona = escolher_coluna(
        df,
        ["NR_ZONA", "zona", "zona_eleitoral"],
        obrigatoria=True,
        nome_logico="zona",
    )

    # Em algumas bases derivadas não existe NR_LOCAL_VOTACAO.
    # Nesses casos, o cruzamento será feito pelo nome do local de votação.
    col_local_numero = escolher_coluna(
        df,
        [
            "NR_LOCAL_VOTACAO",
            "numero_local_votacao",
            "local_votacao_numero",
            "codigo_local_votacao",
            "cd_local_votacao",
        ],
        obrigatoria=False,
        nome_logico="número do local de votação",
    )

    col_nome_local = escolher_coluna(
        df,
        [
            "NM_LOCAL_VOTACAO",
            "nome_local_votacao",
            "local_votacao",
            "local",
            "nome_local",
        ],
        obrigatoria=True,
        nome_logico="nome do local de votação",
    )

    col_endereco = escolher_coluna(
        df,
        [
            "DS_LOCAL_VOTACAO_ENDERECO",
            "endereco",
            "endereco_local_votacao",
            "endereco_local",
        ],
        obrigatoria=False,
        nome_logico="endereço do local",
    )

    col_vereador = escolher_coluna(
        df,
        [
            "vereador",
            "NM_VOTAVEL",
            "nome_urna",
            "nome_candidato",
            "NM_CANDIDATO",
        ],
        obrigatoria=True,
        nome_logico="vereador",
    )

    col_partido = escolher_coluna(
        df,
        [
            "SG_PARTIDO",
            "partido",
            "partido_vereador",
        ],
        obrigatoria=False,
        nome_logico="partido",
    )

    col_votos = escolher_coluna(
        df,
        [
            "QT_VOTOS",
            "votos",
            "votos_vereador",
            "votos_nominais",
        ],
        obrigatoria=True,
        nome_logico="votos",
    )

    col_cargo = escolher_coluna(
        df,
        ["DS_CARGO", "cargo"],
        obrigatoria=False,
        nome_logico="cargo",
    )

    base = df.copy()

    if col_cargo:
        base["cargo_norm"] = base[col_cargo].apply(normalizar_texto)
        base = base[base["cargo_norm"].str.contains("VEREADOR", na=False)].copy()

    base["municipio_norm"] = base[col_municipio].apply(normalizar_nome_chave)
    base["zona_norm"] = base[col_zona].apply(normalizar_numero)

    if col_local_numero:
        base["local_num_norm"] = base[col_local_numero].apply(normalizar_numero)
    else:
        base["local_num_norm"] = ""

    base["local_nome"] = base[col_nome_local].fillna("").astype(str).str.upper().str.strip()
    base["local_nome_norm"] = base["local_nome"].apply(normalizar_nome_chave)

    if col_endereco:
        base["endereco_local"] = base[col_endereco].fillna("").astype(str).str.upper().str.strip()
    else:
        base["endereco_local"] = ""

    base["vereador"] = base[col_vereador].fillna("").astype(str).str.upper().str.strip()

    if col_partido:
        base["partido_vereador"] = base[col_partido].fillna("").astype(str).str.upper().str.strip()
    else:
        base["partido_vereador"] = ""

    base["votos_vereador_local"] = base[col_votos].apply(converter_int)

    base = base[base["votos_vereador_local"] > 0].copy()

    agrupado = (
        base
        .groupby(
            [
                "municipio_norm",
                "zona_norm",
                "local_num_norm",
                "local_nome",
                "local_nome_norm",
                "endereco_local",
                "vereador",
                "partido_vereador",
            ],
            dropna=False,
            as_index=False,
        )
        .agg(
            votos_vereador_local=("votos_vereador_local", "sum"),
        )
    )

    if col_local_numero:
        agrupado["ranking_vereador_no_local"] = (
            agrupado
            .groupby(["municipio_norm", "zona_norm", "local_num_norm"])["votos_vereador_local"]
            .rank(method="first", ascending=False)
            .astype(int)
        )
    else:
        agrupado["ranking_vereador_no_local"] = (
            agrupado
            .groupby(["municipio_norm", "zona_norm", "local_nome_norm"])["votos_vereador_local"]
            .rank(method="first", ascending=False)
            .astype(int)
        )

    agrupado = agrupado[
        agrupado["ranking_vereador_no_local"] <= TOP_N_VEREADORES_POR_LOCAL
    ].copy()

    print(f"Linhas de vereadores preparadas: {len(agrupado):,}".replace(",", "."))
    print("Modo de cruzamento disponível na base de vereadores:")

    if col_local_numero:
        print("- município + zona + número do local de votação")
        print("- município + nome do local de votação")
    else:
        print("- município + zona + nome do local de votação")
        print("- município + nome do local de votação")

    return agrupado
'''


NOVA_FUNCAO_CRUZAR_REDUTOS = r'''def cruzar_redutos(redutos_parceiro, vereadores):
    cruzamentos = []

    # Cruzamento 1: município + zona + número do local de votação.
    # Só funciona quando as duas bases têm número do local.
    if (
        "local_num_norm" in redutos_parceiro.columns
        and "local_num_norm" in vereadores.columns
        and redutos_parceiro["local_num_norm"].astype(str).str.strip().ne("").any()
        and vereadores["local_num_norm"].astype(str).str.strip().ne("").any()
    ):
        chaves_exatas = ["municipio_norm", "zona_norm", "local_num_norm"]

        cruzamento_exato = redutos_parceiro.merge(
            vereadores,
            on=chaves_exatas,
            how="inner",
            suffixes=("_parceiro", "_vereador"),
        )

        if not cruzamento_exato.empty:
            cruzamento_exato["tipo_cruzamento"] = "MUNICIPIO_ZONA_LOCAL_NUMERO"
            cruzamentos.append(cruzamento_exato)

    # Cruzamento 2: município + zona + nome do local de votação.
    # Este é o modo correto para a base votacao_secao_vereadores_top10.csv.
    if (
        "municipio_norm" in redutos_parceiro.columns
        and "zona_norm" in redutos_parceiro.columns
        and "local_nome_norm" in redutos_parceiro.columns
        and "municipio_norm" in vereadores.columns
        and "zona_norm" in vereadores.columns
        and "local_nome_norm" in vereadores.columns
    ):
        chaves_zona_nome = ["municipio_norm", "zona_norm", "local_nome_norm"]

        cruzamento_zona_nome = redutos_parceiro.merge(
            vereadores,
            on=chaves_zona_nome,
            how="inner",
            suffixes=("_parceiro", "_vereador"),
        )

        if not cruzamento_zona_nome.empty:
            cruzamento_zona_nome["tipo_cruzamento"] = "MUNICIPIO_ZONA_NOME_LOCAL"
            cruzamentos.append(cruzamento_zona_nome)

    # Cruzamento 3: município + nome do local.
    # Fallback útil quando há divergência de zona entre eleições ou ausência de número do local.
    if (
        "municipio_norm" in redutos_parceiro.columns
        and "local_nome_norm" in redutos_parceiro.columns
        and "municipio_norm" in vereadores.columns
        and "local_nome_norm" in vereadores.columns
    ):
        chaves_nome = ["municipio_norm", "local_nome_norm"]

        cruzamento_nome = redutos_parceiro.merge(
            vereadores,
            on=chaves_nome,
            how="inner",
            suffixes=("_parceiro", "_vereador"),
        )

        if not cruzamento_nome.empty:
            cruzamento_nome["tipo_cruzamento"] = "MUNICIPIO_NOME_LOCAL"
            cruzamentos.append(cruzamento_nome)

    if not cruzamentos:
        return pd.DataFrame()

    cruzamento = pd.concat(cruzamentos, ignore_index=True)

    # Deduplicação conservadora.
    colunas_dedup = [
        "municipio_norm",
        "zona_norm",
        "local_num_norm",
        "local_nome_norm",
        "vereador",
        "partido_vereador",
    ]

    colunas_dedup = [col for col in colunas_dedup if col in cruzamento.columns]

    if colunas_dedup:
        cruzamento = cruzamento.drop_duplicates(subset=colunas_dedup).copy()
    else:
        cruzamento = cruzamento.drop_duplicates().copy()

    return cruzamento
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
    print("CORREÇÃO DO SCRIPT DE CRUZAMENTO — COLUNAS DA BASE DE VEREADORES")
    print("=" * 80)

    if not os.path.exists(ARQUIVO_SCRIPT):
        raise FileNotFoundError(f"Script não encontrado: {ARQUIVO_SCRIPT}")

    with open(ARQUIVO_SCRIPT, "r", encoding="utf-8") as f:
        conteudo = f.read()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = ARQUIVO_SCRIPT.replace(".py", f"_backup_colunas_vereadores_{timestamp}.py")

    with open(backup, "w", encoding="utf-8") as f:
        f.write(conteudo)

    print(f"Backup criado: {backup}")

    conteudo = substituir_funcao(
        conteudo,
        "preparar_base_vereadores",
        NOVA_FUNCAO_PREPARAR_BASE_VEREADORES,
    )

    conteudo = substituir_funcao(
        conteudo,
        "cruzar_redutos",
        NOVA_FUNCAO_CRUZAR_REDUTOS,
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