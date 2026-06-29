from __future__ import annotations

import json
import re
import textwrap
import unicodedata
from datetime import datetime
from pathlib import Path

import pandas as pd


TOP_CURADORIA = 30


def limpar_texto(texto: str) -> str:
    return textwrap.dedent(texto).lstrip()


def detectar_raiz_projeto() -> Path:
    caminho_script = Path(__file__).resolve()

    if (
        caminho_script.parent.name.lower() == "analytics"
        and caminho_script.parent.parent.name.lower() == "scripts"
    ):
        return caminho_script.parent.parent.parent

    return Path.cwd()


def normalizar_texto(valor: object) -> str:
    if valor is None or pd.isna(valor):
        return ""

    texto = str(valor).strip().upper()
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(ch for ch in texto if not unicodedata.combining(ch))
    texto = " ".join(texto.split())
    return texto


def normalizar_coluna(coluna: str) -> str:
    texto = normalizar_texto(coluna).lower()
    texto = texto.replace(" ", "_")
    texto = texto.replace("-", "_")
    texto = texto.replace("/", "_")
    texto = texto.replace(".", "")
    texto = texto.replace("ç", "c")
    return texto


def encontrar_arquivo(root: Path, candidatos: list[str]) -> Path | None:
    for relativo in candidatos:
        caminho = root / relativo
        if caminho.exists():
            return caminho

    return None


def ler_csv_robusto(caminho: Path) -> pd.DataFrame:
    tentativas = [
        {"encoding": "utf-8-sig", "sep": None, "engine": "python"},
        {"encoding": "utf-8", "sep": None, "engine": "python"},
        {"encoding": "latin1", "sep": None, "engine": "python"},
        {"encoding": "cp1252", "sep": None, "engine": "python"},
    ]

    ultimo_erro: Exception | None = None

    for kwargs in tentativas:
        try:
            df = pd.read_csv(caminho, **kwargs)
            df.columns = [normalizar_coluna(c) for c in df.columns]
            return df
        except Exception as erro:
            ultimo_erro = erro

    raise RuntimeError(f"Não foi possível ler {caminho}. Erro: {ultimo_erro}")


def ler_tabela(caminho: Path) -> pd.DataFrame:
    if caminho.suffix.lower() in [".xlsx", ".xls"]:
        df = pd.read_excel(caminho)
        df.columns = [normalizar_coluna(c) for c in df.columns]
        return df

    return ler_csv_robusto(caminho)


def encontrar_coluna(df: pd.DataFrame, candidatos: list[str]) -> str | None:
    colunas = list(df.columns)
    candidatos_norm = [normalizar_coluna(c) for c in candidatos]

    for candidato in candidatos_norm:
        if candidato in colunas:
            return candidato

    for candidato in candidatos_norm:
        for coluna in colunas:
            if candidato in coluna:
                return coluna

    return None


def converter_numero(serie: pd.Series) -> pd.Series:
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

        texto = texto.replace("\u00a0", " ")

        if re.fullmatch(r"\d{1,3}(\.\d{3})+", texto):
            return float(texto.replace(".", ""))

        if re.fullmatch(r"\d{1,3}(\.\d{3})+,\d+", texto):
            return float(texto.replace(".", "").replace(",", "."))

        if re.fullmatch(r"\d+\.0+", texto):
            return float(texto)

        if re.fullmatch(r"\d+", texto):
            return float(texto)

        if re.fullmatch(r"\d+,\d+", texto):
            return float(texto.replace(",", "."))

        texto_limpo = re.sub(r"[^0-9,.\-]", "", texto)

        if texto_limpo.count(",") == 1 and texto_limpo.count(".") >= 1:
            texto_limpo = texto_limpo.replace(".", "").replace(",", ".")
        elif texto_limpo.count(",") == 1 and texto_limpo.count(".") == 0:
            texto_limpo = texto_limpo.replace(",", ".")

        try:
            return float(texto_limpo)
        except ValueError:
            return 0.0

    return serie.apply(parse_valor).astype(float)


def carregar_roteiro(root: Path) -> pd.DataFrame:
    caminho = encontrar_arquivo(
        root,
        [
            "data/final/parceiros/gabi-goncalves/roteiro_territorial_davi_gabi_v1.csv",
            "data/final/parceiros/gabi-goncalves/roteiro_territorial_davi_gabi_v1.xlsx",
            "data/reference/parceiros/gabi-goncalves/agenda_conjunta_davi_gabi_v1.csv",
            "data/final/parceiros/gabi-goncalves/cruzamento_davi_gabi_v1.csv",
        ],
    )

    if caminho is None:
        raise FileNotFoundError(
            "Não encontrei o roteiro/cruzamento Davi + Gabi. "
            "Rode antes o Sprint 05."
        )

    print(f"[OK] Base para curadoria encontrada: {caminho}")

    df = ler_tabela(caminho)

    colunas_map = {
        "ordem_prioridade": ["ordem_prioridade", "ordem_agenda", "ranking_sinergia_davi_gabi", "rank"],
        "semana_roteiro": ["semana_roteiro", "semana_sugerida", "semana"],
        "dia_sugerido": ["dia_sugerido", "dia"],
        "turno_sugerido": ["turno_sugerido", "turno"],
        "municipio": ["municipio", "nm_municipio", "nome_municipio"],
        "macro_regiao": ["macro_regiao", "regiao"],
        "eixo_logistico": ["eixo_logistico"],
        "prioridade_sinergia_davi_gabi": ["prioridade_sinergia_davi_gabi", "prioridade"],
        "status_agenda_conjunta": ["status_agenda_conjunta", "status"],
        "score_sinergia_davi_gabi": ["score_sinergia_davi_gabi", "score"],
        "principal_lideranca": ["principal_lideranca", "nome_lideranca", "lideranca"],
        "partido_principal_lideranca": ["partido_principal_lideranca", "partido_lideranca", "partido"],
        "prefeito_2024": ["prefeito_2024", "prefeito", "nome_prefeito"],
        "partido_prefeito_2024": ["partido_prefeito_2024", "partido_prefeito"],
        "meta_votos_referencia_gabi": ["meta_votos_referencia_gabi", "meta_gabi", "meta"],
        "potencial_transferencia_10pct": ["potencial_transferencia_10pct", "potencial"],
        "tipo_agenda": ["tipo_agenda"],
        "acao_recomendada": ["acao_recomendada", "acao"],
        "objetivo_politico": ["objetivo_politico", "objetivo"],
        "observacao_logistica": ["observacao_logistica", "logistica"],
        "justificativa_sinergia": ["justificativa_sinergia", "justificativa"],
    }

    base = pd.DataFrame()

    for destino, candidatos in colunas_map.items():
        coluna = encontrar_coluna(df, candidatos)

        if coluna:
            base[destino] = df[coluna]
        else:
            base[destino] = ""

    if base["municipio"].astype(str).str.strip().eq("").all():
        raise RuntimeError("Não encontrei coluna de município válida na base de roteiro.")

    base["municipio"] = base["municipio"].astype(str).str.strip()
    base["municipio_key"] = base["municipio"].apply(normalizar_texto)

    campos_num = [
        "ordem_prioridade",
        "score_sinergia_davi_gabi",
        "meta_votos_referencia_gabi",
        "potencial_transferencia_10pct",
    ]

    for campo in campos_num:
        base[campo] = converter_numero(base[campo])

    base = base[
        (base["municipio_key"] != "")
        & (base["municipio"].astype(str).str.upper() != "NAN")
    ].copy()

    base = base.sort_values(
        by=["ordem_prioridade", "score_sinergia_davi_gabi"],
        ascending=[True, False],
    ).head(TOP_CURADORIA).reset_index(drop=True)

    base["ordem_curadoria"] = range(1, len(base) + 1)

    return base


def classificar_prioridade_curadoria(row: pd.Series) -> str:
    prioridade = str(row.get("prioridade_sinergia_davi_gabi", "")).strip()
    ordem = int(row.get("ordem_curadoria", 999))

    if prioridade == "Muito alta" or ordem <= 10:
        return "Imediata"

    if prioridade == "Alta" or ordem <= 20:
        return "Alta"

    if prioridade == "Média" or ordem <= 30:
        return "Média"

    return "Monitoramento"


def prazo_curadoria(prioridade: str) -> str:
    if prioridade == "Imediata":
        return "Até 48h"

    if prioridade == "Alta":
        return "Até 5 dias"

    if prioridade == "Média":
        return "Até 10 dias"

    return "Após rodada inicial"


def criar_matriz_curadoria(roteiro: pd.DataFrame) -> pd.DataFrame:
    df = roteiro.copy()

    df["prioridade_curadoria"] = df.apply(classificar_prioridade_curadoria, axis=1)
    df["prazo_curadoria"] = df["prioridade_curadoria"].apply(prazo_curadoria)

    df["relacao_gabi"] = "A CURAR"
    df["relacao_davi"] = "A CURAR"
    df["relacao_renan_filho"] = "A CURAR"
    df["relacao_renan_calheiros"] = "A CURAR"
    df["relacao_paulo_dantas"] = "A CURAR"

    df["grupo_politico_local"] = "A CURAR"
    df["alinhamento_governo_estadual"] = "A CURAR"
    df["alinhamento_davi"] = "A CURAR"
    df["alinhamento_gabi"] = "A CURAR"

    df["status_validacao_lideranca"] = "Pendente"
    df["status_validacao_prefeito"] = "Pendente"
    df["status_validacao_grupo_local"] = "Pendente"
    df["risco_politico"] = "A CURAR"
    df["conflito_apoio"] = "A CURAR"
    df["sensibilidade_local"] = "A CURAR"

    df["decisao_agenda"] = "Aguardando curadoria"
    df["agenda_publica_ou_reservada"] = "A CURAR"
    df["responsavel_curadoria"] = ""
    df["contato_local"] = ""
    df["data_validacao"] = ""
    df["proximo_passo"] = ""
    df["observacao_politica"] = ""

    df["pergunta_chave_curadoria"] = df.apply(
        lambda row: (
            f"Confirmar se {row['principal_lideranca']} em {row['municipio']} "
            "possui aderência real para operar agenda Davi + Gabi."
            if str(row.get("principal_lideranca", "")).strip()
            else f"Identificar liderança confiável em {row['municipio']} para sustentar agenda Davi + Gabi."
        ),
        axis=1,
    )

    df["criterio_para_avancar"] = (
        "Só avançar para agenda pública após validar relação política, ausência de conflito local, "
        "responsável pela mobilização e compatibilidade com o eixo Davi/Renan/Paulo Dantas."
    )

    ordem_colunas = [
        "ordem_curadoria",
        "prioridade_curadoria",
        "prazo_curadoria",
        "semana_roteiro",
        "dia_sugerido",
        "turno_sugerido",
        "municipio",
        "macro_regiao",
        "eixo_logistico",
        "prioridade_sinergia_davi_gabi",
        "status_agenda_conjunta",
        "score_sinergia_davi_gabi",
        "principal_lideranca",
        "partido_principal_lideranca",
        "prefeito_2024",
        "partido_prefeito_2024",
        "meta_votos_referencia_gabi",
        "potencial_transferencia_10pct",
        "tipo_agenda",
        "acao_recomendada",
        "objetivo_politico",
        "relacao_gabi",
        "relacao_davi",
        "relacao_renan_filho",
        "relacao_renan_calheiros",
        "relacao_paulo_dantas",
        "grupo_politico_local",
        "alinhamento_governo_estadual",
        "alinhamento_davi",
        "alinhamento_gabi",
        "status_validacao_lideranca",
        "status_validacao_prefeito",
        "status_validacao_grupo_local",
        "risco_politico",
        "conflito_apoio",
        "sensibilidade_local",
        "decisao_agenda",
        "agenda_publica_ou_reservada",
        "pergunta_chave_curadoria",
        "criterio_para_avancar",
        "responsavel_curadoria",
        "contato_local",
        "data_validacao",
        "proximo_passo",
        "observacao_politica",
        "observacao_logistica",
        "justificativa_sinergia",
        "municipio_key",
    ]

    for coluna in ordem_colunas:
        if coluna not in df.columns:
            df[coluna] = ""

    return df[ordem_colunas]


def gerar_resumo_curadoria(curadoria: pd.DataFrame) -> pd.DataFrame:
    resumo = (
        curadoria.groupby(["prioridade_curadoria"], as_index=False)
        .agg(
            municipios=("municipio", "count"),
            meta_gabi=("meta_votos_referencia_gabi", "sum"),
            potencial_10pct=("potencial_transferencia_10pct", "sum"),
        )
    )

    ordem = {
        "Imediata": 1,
        "Alta": 2,
        "Média": 3,
        "Monitoramento": 4,
    }

    resumo["ordem"] = resumo["prioridade_curadoria"].map(ordem).fillna(99).astype(int)
    resumo = resumo.sort_values("ordem").drop(columns=["ordem"]).reset_index(drop=True)

    return resumo


def gerar_checklist_curadoria() -> pd.DataFrame:
    itens = [
        {
            "etapa": 1,
            "bloco": "Relação política",
            "pergunta": "A liderança tem relação direta com Gabi?",
            "campo_relacionado": "relacao_gabi",
            "opcoes_sugeridas": "Forte; Média; Fraca; Contra; A CURAR",
        },
        {
            "etapa": 2,
            "bloco": "Relação política",
            "pergunta": "A liderança tem relação direta com Davi Maia?",
            "campo_relacionado": "relacao_davi",
            "opcoes_sugeridas": "Forte; Média; Fraca; Contra; A CURAR",
        },
        {
            "etapa": 3,
            "bloco": "Eixo estadual",
            "pergunta": "O grupo local possui alinhamento com Renan Filho, Renan Calheiros ou Paulo Dantas?",
            "campo_relacionado": "relacao_renan_filho / relacao_renan_calheiros / relacao_paulo_dantas",
            "opcoes_sugeridas": "Forte; Médio; Fraco; Oposição; A CURAR",
        },
        {
            "etapa": 4,
            "bloco": "Risco político",
            "pergunta": "Existe conflito local que possa impedir agenda Davi + Gabi?",
            "campo_relacionado": "conflito_apoio",
            "opcoes_sugeridas": "Sim; Não; A verificar",
        },
        {
            "etapa": 5,
            "bloco": "Agenda",
            "pergunta": "A agenda deve ser pública ou reservada?",
            "campo_relacionado": "agenda_publica_ou_reservada",
            "opcoes_sugeridas": "Pública; Reservada; Primeiro contato reservado",
        },
        {
            "etapa": 6,
            "bloco": "Decisão",
            "pergunta": "Qual decisão operacional após a curadoria?",
            "campo_relacionado": "decisao_agenda",
            "opcoes_sugeridas": "Agendar; Reunião reservada; Monitorar; Não avançar",
        },
    ]

    return pd.DataFrame(itens)


def carregar_json(caminho: Path) -> dict:
    if caminho.exists():
        return json.loads(caminho.read_text(encoding="utf-8"))

    return {}


def salvar_json(caminho: Path, dados: dict) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text(
        json.dumps(dados, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"[OK] JSON salvo: {caminho}")


def gerar_curadoria_json(curadoria: pd.DataFrame, resumo: pd.DataFrame) -> dict:
    pendentes = int(len(curadoria[curadoria["decisao_agenda"] == "Aguardando curadoria"]))

    return {
        "metadata": {
            "projeto": "Curadoria Política Davi Maia + Gabi Gonçalves",
            "versao": "sprint06_curadoria_politica",
            "atualizacao": datetime.now().strftime("%d/%m/%Y %H:%M"),
            "status": "Matriz de curadoria política criada; validações manuais pendentes."
        },
        "indicadores": {
            "municipios_para_curadoria": int(len(curadoria)),
            "curadorias_pendentes": pendentes,
            "prioridade_imediata": int(len(curadoria[curadoria["prioridade_curadoria"] == "Imediata"])),
            "prioridade_alta": int(len(curadoria[curadoria["prioridade_curadoria"] == "Alta"])),
            "prioridade_media": int(len(curadoria[curadoria["prioridade_curadoria"] == "Média"])),
            "meta_gabi_em_curadoria": int(curadoria["meta_votos_referencia_gabi"].sum()),
            "potencial_10pct_em_curadoria": int(curadoria["potencial_transferencia_10pct"].sum()),
        },
        "resumo_prioridade": [
            {
                "prioridade": row["prioridade_curadoria"],
                "municipios": int(row["municipios"]),
                "meta_gabi": int(row["meta_gabi"]),
                "potencial_10pct": int(row["potencial_10pct"]),
            }
            for _, row in resumo.iterrows()
        ],
        "curadoria": [
            {
                "ordem": int(row["ordem_curadoria"]),
                "prioridade": row["prioridade_curadoria"],
                "prazo": row["prazo_curadoria"],
                "municipio": row["municipio"],
                "lideranca": row["principal_lideranca"],
                "prefeito": row["prefeito_2024"],
                "score": round(float(row["score_sinergia_davi_gabi"]), 2),
                "relacao_gabi": row["relacao_gabi"],
                "relacao_davi": row["relacao_davi"],
                "risco": row["risco_politico"],
                "decisao": row["decisao_agenda"],
                "pergunta": row["pergunta_chave_curadoria"],
            }
            for _, row in curadoria.iterrows()
        ],
    }


def atualizar_base_dashboard(root: Path, curadoria: pd.DataFrame) -> None:
    caminho = (
        root
        / "data"
        / "dashboard"
        / "parceiros"
        / "gabi-goncalves"
        / "base_dashboard_gabi_v1.json"
    )

    dados = carregar_json(caminho)

    dados.setdefault("metadata", {})
    dados["metadata"]["versao"] = "sprint06_curadoria_politica"
    dados["metadata"]["atualizacao"] = datetime.now().strftime("%d/%m/%Y %H:%M")
    dados["metadata"]["status"] = "Curadoria política Davi + Gabi adicionada ao painel."

    dados.setdefault("indicadores_gabi", {})
    dados["indicadores_gabi"]["municipios_para_curadoria_politica"] = int(len(curadoria))
    dados["indicadores_gabi"]["curadorias_pendentes"] = int(
        len(curadoria[curadoria["decisao_agenda"] == "Aguardando curadoria"])
    )
    dados["indicadores_gabi"]["status_curadoria_politica"] = (
        "Matriz criada; relações políticas reais ainda precisam ser preenchidas manualmente."
    )

    dados["curadoria_politica_davi_gabi"] = [
        {
            "ordem": int(row["ordem_curadoria"]),
            "municipio": row["municipio"],
            "prioridade": row["prioridade_curadoria"],
            "prazo": row["prazo_curadoria"],
            "lideranca": row["principal_lideranca"],
            "decisao": row["decisao_agenda"],
        }
        for _, row in curadoria.head(20).iterrows()
    ]

    salvar_json(caminho, dados)


def atualizar_cruzamento_json(root: Path, curadoria: pd.DataFrame) -> None:
    caminho = (
        root
        / "data"
        / "dashboard"
        / "parceiros"
        / "gabi-goncalves"
        / "cruzamento_davi_gabi_v1.json"
    )

    dados = carregar_json(caminho)

    dados.setdefault("metadata", {})
    dados["metadata"]["versao"] = "sprint06_curadoria_politica"
    dados["metadata"]["atualizacao"] = datetime.now().strftime("%d/%m/%Y %H:%M")
    dados["metadata"]["status"] = "Curadoria política incorporada ao cruzamento Davi + Gabi."

    dados["curadoria_politica"] = [
        {
            "ordem": int(row["ordem_curadoria"]),
            "municipio": row["municipio"],
            "prioridade": row["prioridade_curadoria"],
            "pergunta_chave": row["pergunta_chave_curadoria"],
            "criterio_para_avancar": row["criterio_para_avancar"],
        }
        for _, row in curadoria.iterrows()
    ]

    salvar_json(caminho, dados)


def criar_curadoria_js() -> str:
    return limpar_texto(
        '''
        const CURADORIA_PATH = "../../data/dashboard/parceiros/gabi-goncalves/curadoria_politica_davi_gabi_v1.json";

        function formatarNumeroCuradoria(valor) {
          if (valor === null || valor === undefined || valor === "") {
            return "-";
          }

          const numero = Number(valor);

          if (Number.isNaN(numero)) {
            return String(valor);
          }

          return numero.toLocaleString("pt-BR");
        }

        async function carregarCuradoria() {
          try {
            const resposta = await fetch(CURADORIA_PATH, { cache: "no-store" });

            if (!resposta.ok) {
              throw new Error(`Erro ao carregar curadoria: ${resposta.status}`);
            }

            return await resposta.json();
          } catch (erro) {
            console.warn(erro.message);
            return null;
          }
        }

        function renderCuradoriaResumo(dados) {
          const grid = document.getElementById("curadoriaResumoGrid");

          if (!grid || !dados) {
            return;
          }

          const indicadores = dados.indicadores || {};

          const cards = [
            {
              rotulo: "Municípios para curadoria",
              valor: indicadores.municipios_para_curadoria,
              detalhe: "Base Davi + Gabi"
            },
            {
              rotulo: "Pendentes",
              valor: indicadores.curadorias_pendentes,
              detalhe: "Aguardando validação"
            },
            {
              rotulo: "Prioridade imediata",
              valor: indicadores.prioridade_imediata,
              detalhe: "Validar primeiro"
            },
            {
              rotulo: "Meta em curadoria",
              valor: indicadores.meta_gabi_em_curadoria,
              detalhe: "Votos de referência"
            }
          ];

          grid.innerHTML = cards.map((card) => `
            <article class="curadoria-mini-card">
              <span>${card.rotulo}</span>
              <strong>${formatarNumeroCuradoria(card.valor)}</strong>
              <small>${card.detalhe}</small>
            </article>
          `).join("");
        }

        function renderCuradoriaTabela(dados) {
          const tbody = document.getElementById("curadoriaTableBody");

          if (!tbody || !dados) {
            return;
          }

          const linhas = dados.curadoria || [];

          if (!linhas.length) {
            tbody.innerHTML = `
              <tr class="empty-row">
                <td colspan="7">Curadoria política ainda não disponível.</td>
              </tr>
            `;
            return;
          }

          tbody.innerHTML = linhas.slice(0, 20).map((item) => `
            <tr>
              <td>${item.ordem}</td>
              <td>${item.municipio}</td>
              <td>${item.prioridade}<br><small>${item.prazo}</small></td>
              <td>${item.lideranca || "-"}</td>
              <td>${item.relacao_gabi}</td>
              <td>${item.relacao_davi}</td>
              <td>${item.decisao}</td>
            </tr>
          `).join("");
        }

        async function inicializarCuradoria() {
          const dados = await carregarCuradoria();

          renderCuradoriaResumo(dados);
          renderCuradoriaTabela(dados);
        }

        document.addEventListener("DOMContentLoaded", inicializarCuradoria);
        '''
    )


def atualizar_painel(root: Path) -> None:
    painel_dir = root / "parceiros" / "gabi-goncalves"
    index_path = painel_dir / "index.html"
    css_path = painel_dir / "styles.css"
    curadoria_js_path = painel_dir / "curadoria.js"

    if not index_path.exists():
        print(f"[AVISO] index.html não encontrado: {index_path}")
        return

    html = index_path.read_text(encoding="utf-8")

    if 'href="#curadoria-politica"' not in html:
        html = html.replace(
            '<a href="#roteiro-territorial">Roteiro</a>',
            '<a href="#roteiro-territorial">Roteiro</a>\n                  <a href="#curadoria-politica">Curadoria</a>',
        )

    secao_curadoria = limpar_texto(
        '''
        <section class="section curadoria-section" id="curadoria-politica">
          <div class="section-header">
            <p class="eyebrow">Curadoria política</p>
            <h2>Validação política Davi Maia + Gabi Gonçalves</h2>
            <p>
              Matriz operacional para validar relações locais, riscos políticos, aderência com Gabi,
              aderência com Davi e compatibilidade com o eixo Renan Filho, Renan Calheiros e Paulo Dantas.
            </p>
          </div>

          <div class="curadoria-mini-grid" id="curadoriaResumoGrid"></div>

          <div class="panel-card curadoria-table-card">
            <div class="panel-header">
              <div>
                <p class="eyebrow">Matriz de validação</p>
                <h2>Municípios e lideranças para curadoria</h2>
              </div>
              <span class="status-pill">Sprint 06</span>
            </div>

            <div class="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Ordem</th>
                    <th>Município</th>
                    <th>Prioridade</th>
                    <th>Liderança</th>
                    <th>Relação Gabi</th>
                    <th>Relação Davi</th>
                    <th>Decisão</th>
                  </tr>
                </thead>
                <tbody id="curadoriaTableBody"></tbody>
              </table>
            </div>
          </div>
        </section>
        '''
    )

    if 'id="curadoria-politica"' not in html:
        alvo = '<section class="section roadmap" id="proximos-passos">'
        if alvo in html:
            html = html.replace(alvo, secao_curadoria + "\n\n      " + alvo)
        else:
            html = html.replace("</main>", secao_curadoria + "\n    </main>")

    if 'src="curadoria.js"' not in html:
        html = html.replace(
            '<script src="roteiro.js"></script>',
            '<script src="roteiro.js"></script>\n  <script src="curadoria.js"></script>',
        )

    if 'src="curadoria.js"' not in html:
        html = html.replace(
            '<script src="app.js"></script>',
            '<script src="app.js"></script>\n  <script src="curadoria.js"></script>',
        )

    index_path.write_text(html, encoding="utf-8")
    print(f"[OK] HTML atualizado com seção de curadoria: {index_path}")

    css = css_path.read_text(encoding="utf-8") if css_path.exists() else ""

    marcador_inicio = "/* ===== SPRINT06_CURADORIA_INICIO ===== */"
    marcador_fim = "/* ===== SPRINT06_CURADORIA_FIM ===== */"

    bloco_css = limpar_texto(
        f'''
        {marcador_inicio}

        .curadoria-section {{
          background:
            radial-gradient(circle at top left, rgba(226, 128, 178, .12), transparent 30%),
            linear-gradient(180deg, rgba(255,255,255,.96), rgba(234,240,255,.90));
        }}

        .curadoria-mini-grid {{
          display: grid;
          grid-template-columns: repeat(4, minmax(0, 1fr));
          gap: 14px;
          margin-bottom: 18px;
        }}

        .curadoria-mini-card {{
          padding: 18px;
          border-radius: 20px;
          border: 1px solid var(--line);
          background: rgba(255, 255, 255, .94);
          box-shadow: 0 14px 34px rgba(11, 31, 77, .08);
          border-top: 5px solid var(--pink-600);
        }}

        .curadoria-mini-card span {{
          display: block;
          color: var(--muted);
          font-size: 11px;
          font-weight: 900;
          text-transform: uppercase;
          letter-spacing: .08em;
        }}

        .curadoria-mini-card strong {{
          display: block;
          margin-top: 8px;
          color: var(--blue-700);
          font-size: 28px;
          line-height: 1;
          letter-spacing: -0.05em;
        }}

        .curadoria-mini-card small {{
          display: block;
          margin-top: 8px;
          color: var(--muted);
        }}

        .curadoria-table-card {{
          margin-top: 18px;
        }}

        .curadoria-table-card td small {{
          color: var(--muted);
          font-weight: 700;
        }}

        @media (max-width: 980px) {{
          .curadoria-mini-grid {{
            grid-template-columns: repeat(2, minmax(0, 1fr));
          }}
        }}

        @media (max-width: 680px) {{
          .curadoria-mini-grid {{
            grid-template-columns: 1fr;
          }}
        }}

        {marcador_fim}
        '''
    )

    padrao = rf"{re.escape(marcador_inicio)}.*?{re.escape(marcador_fim)}"

    if re.search(padrao, css, flags=re.DOTALL):
        css = re.sub(padrao, bloco_css.strip(), css, flags=re.DOTALL)
    else:
        css = css.rstrip() + "\n\n" + bloco_css.strip() + "\n"

    css_path.write_text(css, encoding="utf-8")
    print(f"[OK] CSS atualizado com estilos de curadoria: {css_path}")

    curadoria_js_path.write_text(criar_curadoria_js(), encoding="utf-8")
    print(f"[OK] curadoria.js criado/atualizado: {curadoria_js_path}")


def gerar_briefing_sprint06(curadoria: pd.DataFrame) -> str:
    imediata = len(curadoria[curadoria["prioridade_curadoria"] == "Imediata"])
    alta = len(curadoria[curadoria["prioridade_curadoria"] == "Alta"])
    media = len(curadoria[curadoria["prioridade_curadoria"] == "Média"])

    linhas = [
        "# Briefing — Sprint 06 — Curadoria Política Davi Maia + Gabi Gonçalves",
        "",
        "## Objetivo",
        "",
        "Criar uma matriz de curadoria política para validar os municípios, lideranças e agendas sugeridas no roteiro territorial Davi + Gabi.",
        "",
        "## Premissa metodológica",
        "",
        "O script não atribui automaticamente relações políticas reais. Os campos sensíveis foram criados como `A CURAR` ou `Pendente`, pois dependem de validação manual, entrevistas, leitura política local e confirmação com o grupo.",
        "",
        "## Resultado geral",
        "",
        f"- Municípios/lideranças para curadoria: {len(curadoria)}",
        f"- Prioridade imediata: {imediata}",
        f"- Prioridade alta: {alta}",
        f"- Prioridade média: {media}",
        "",
        "## Campos críticos criados",
        "",
        "- relacao_gabi",
        "- relacao_davi",
        "- relacao_renan_filho",
        "- relacao_renan_calheiros",
        "- relacao_paulo_dantas",
        "- grupo_politico_local",
        "- alinhamento_governo_estadual",
        "- alinhamento_davi",
        "- alinhamento_gabi",
        "- risco_politico",
        "- conflito_apoio",
        "- sensibilidade_local",
        "- decisao_agenda",
        "- agenda_publica_ou_reservada",
        "",
        "## Arquivos gerados",
        "",
        "- data/final/parceiros/gabi-goncalves/curadoria_politica_davi_gabi_v1.csv",
        "- data/final/parceiros/gabi-goncalves/curadoria_politica_davi_gabi_v1.xlsx",
        "- data/reference/parceiros/gabi-goncalves/checklist_curadoria_politica_davi_gabi_v1.csv",
        "- data/dashboard/parceiros/gabi-goncalves/curadoria_politica_davi_gabi_v1.json",
        "- docs/briefing_gabi_sprint06.md",
        "",
        "## Próximo sprint recomendado",
        "",
        "Sprint 07 — Relatório Executivo de Aprovação.",
        "",
        "O próximo passo é gerar um relatório executivo com a visão consolidada do painel, principais achados, roteiro territorial e matriz de curadoria para aprovação do Davi.",
    ]

    return "\n".join(linhas) + "\n"


def salvar_resultados(
    root: Path,
    curadoria: pd.DataFrame,
    resumo: pd.DataFrame,
    checklist: pd.DataFrame,
) -> None:
    final_dir = root / "data" / "final" / "parceiros" / "gabi-goncalves"
    reference_dir = root / "data" / "reference" / "parceiros" / "gabi-goncalves"
    dashboard_dir = root / "data" / "dashboard" / "parceiros" / "gabi-goncalves"
    docs_dir = root / "docs"

    final_dir.mkdir(parents=True, exist_ok=True)
    reference_dir.mkdir(parents=True, exist_ok=True)
    dashboard_dir.mkdir(parents=True, exist_ok=True)
    docs_dir.mkdir(parents=True, exist_ok=True)

    curadoria_csv = final_dir / "curadoria_politica_davi_gabi_v1.csv"
    curadoria_xlsx = final_dir / "curadoria_politica_davi_gabi_v1.xlsx"
    resumo_csv = reference_dir / "resumo_curadoria_politica_davi_gabi_v1.csv"
    checklist_csv = reference_dir / "checklist_curadoria_politica_davi_gabi_v1.csv"
    curadoria_json = dashboard_dir / "curadoria_politica_davi_gabi_v1.json"
    briefing_md = docs_dir / "briefing_gabi_sprint06.md"

    curadoria.to_csv(curadoria_csv, index=False, encoding="utf-8-sig")
    print(f"[OK] Curadoria política salva: {curadoria_csv}")

    resumo.to_csv(resumo_csv, index=False, encoding="utf-8-sig")
    print(f"[OK] Resumo de curadoria salvo: {resumo_csv}")

    checklist.to_csv(checklist_csv, index=False, encoding="utf-8-sig")
    print(f"[OK] Checklist de curadoria salvo: {checklist_csv}")

    try:
        with pd.ExcelWriter(curadoria_xlsx) as writer:
            curadoria.to_excel(writer, sheet_name="curadoria_politica", index=False)
            resumo.to_excel(writer, sheet_name="resumo_prioridade", index=False)
            checklist.to_excel(writer, sheet_name="checklist", index=False)

        print(f"[OK] XLSX consolidado salvo: {curadoria_xlsx}")
    except Exception as erro:
        print(f"[AVISO] Não foi possível salvar XLSX. CSVs foram gerados normalmente. Erro: {erro}")

    curadoria_json.write_text(
        json.dumps(gerar_curadoria_json(curadoria, resumo), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"[OK] JSON de curadoria salvo: {curadoria_json}")

    briefing_md.write_text(gerar_briefing_sprint06(curadoria), encoding="utf-8")
    print(f"[OK] Briefing salvo: {briefing_md}")


def imprimir_resumo(curadoria: pd.DataFrame, resumo: pd.DataFrame) -> None:
    print("")
    print("============================================================")
    print("RESUMO DO SPRINT 06")
    print("============================================================")
    print(f"Municípios/lideranças para curadoria: {len(curadoria)}")
    print(f"Pendentes: {len(curadoria[curadoria['decisao_agenda'] == 'Aguardando curadoria'])}")
    print(f"Meta Gabi em curadoria: {int(curadoria['meta_votos_referencia_gabi'].sum()):,}".replace(",", "."))
    print(f"Potencial 10% em curadoria: {int(curadoria['potencial_transferencia_10pct'].sum()):,}".replace(",", "."))
    print("")
    print("Resumo por prioridade:")
    print("------------------------------------------------------------")
    print(resumo.to_string(index=False))
    print("")
    print("Top 15 para curadoria:")
    print("------------------------------------------------------------")

    colunas = [
        "ordem_curadoria",
        "prioridade_curadoria",
        "prazo_curadoria",
        "municipio",
        "principal_lideranca",
        "relacao_gabi",
        "relacao_davi",
        "decisao_agenda",
    ]

    print(curadoria[colunas].head(15).to_string(index=False))
    print("============================================================")


def main() -> None:
    root = detectar_raiz_projeto()

    print("============================================================")
    print("SPRINT 06 — CURADORIA POLÍTICA DAVI MAIA + GABI GONÇALVES")
    print("============================================================")
    print(f"[INFO] Raiz detectada: {root}")

    roteiro = carregar_roteiro(root)
    curadoria = criar_matriz_curadoria(roteiro)
    resumo = gerar_resumo_curadoria(curadoria)
    checklist = gerar_checklist_curadoria()

    salvar_resultados(root, curadoria, resumo, checklist)
    atualizar_base_dashboard(root, curadoria)
    atualizar_cruzamento_json(root, curadoria)
    atualizar_painel(root)

    imprimir_resumo(curadoria, resumo)

    print("")
    print("SPRINT 06 CONCLUÍDO.")
    print("")
    print("Agora teste o painel:")
    print("  cd C:\\Users\\user\\Documents\\Workspace\\campanha_2026\\alagoas-political-intelligence")
    print("  python -m http.server 8000")
    print("")
    print("Abra:")
    print("  http://localhost:8000/parceiros/gabi-goncalves/")
    print("")
    print("Depois use Ctrl + F5 para atualizar os arquivos no navegador.")


if __name__ == "__main__":
    main()