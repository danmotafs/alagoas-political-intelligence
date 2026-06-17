from pathlib import Path
import json

import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[2]

INPUT_PATH = BASE_DIR / "data" / "final" / "ranking_estrategico_alagoas_2024.csv"

DASHBOARD_DIR = BASE_DIR / "dashboard"
OUTPUT_HTML = DASHBOARD_DIR / "dashboard_estrategico_alagoas.html"


def formatar_numero(valor: float) -> str:
    return f"{valor:,.0f}".replace(",", ".")


def formatar_percentual(valor: float) -> str:
    return f"{valor:.2f}%".replace(".", ",")


def carregar_dados() -> pd.DataFrame:
    if not INPUT_PATH.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {INPUT_PATH}")

    df = pd.read_csv(INPUT_PATH)

    colunas_obrigatorias = {
        "rank",
        "municipio",
        "populacao_estimada_2024",
        "eleitorado_2024",
        "taxa_eleitorado_pct",
        "participacao_eleitorado_pct",
        "indice_estrategico_pct",
        "prioridade_politica",
    }

    faltantes = colunas_obrigatorias - set(df.columns)
    if faltantes:
        raise KeyError(f"Colunas ausentes no ranking: {faltantes}")

    return df


def gerar_html(df: pd.DataFrame) -> str:
    total_municipios = len(df)
    populacao_total = df["populacao_estimada_2024"].sum()
    eleitorado_total = df["eleitorado_2024"].sum()
    taxa_eleitorado_estadual = eleitorado_total / populacao_total * 100

    top20 = df.head(20).copy()
    top10 = df.head(10).copy()

    top10_eleitorado = top10["eleitorado_2024"].sum()
    top10_participacao = top10_eleitorado / eleitorado_total * 100

    maceio = df[df["municipio"].str.upper().isin(["MACEIÓ", "MACEIO"])].iloc[0]
    arapiraca = df[df["municipio"].str.upper() == "ARAPIRACA"].iloc[0]

    municipios_top20 = top20["municipio"].tolist()
    eleitorado_top20 = top20["eleitorado_2024"].astype(int).tolist()
    indice_top20 = top20["indice_estrategico_pct"].round(4).tolist()

    tabela_top20 = ""
    for _, row in top20.iterrows():
        tabela_top20 += f"""
        <tr>
            <td>{int(row["rank"])}</td>
            <td>{row["municipio"]}</td>
            <td>{formatar_numero(row["populacao_estimada_2024"])}</td>
            <td>{formatar_numero(row["eleitorado_2024"])}</td>
            <td>{formatar_percentual(row["participacao_eleitorado_pct"])}</td>
            <td>{formatar_percentual(row["indice_estrategico_pct"])}</td>
            <td><span class="badge">{row["prioridade_politica"]}</span></td>
        </tr>
        """

    html = f"""
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <title>Alagoas Political Intelligence | Dashboard Executivo</title>
    <script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>

    <style>
        body {{
            margin: 0;
            font-family: Arial, Helvetica, sans-serif;
            background: #f4f6f8;
            color: #17212b;
        }}

        .container {{
            width: 94%;
            max-width: 1380px;
            margin: 0 auto;
            padding: 28px 0 50px 0;
        }}

        .header {{
            background: linear-gradient(135deg, #0f172a, #1e3a5f);
            color: white;
            padding: 34px;
            border-radius: 18px;
            margin-bottom: 24px;
            box-shadow: 0 12px 30px rgba(0,0,0,0.15);
        }}

        .header h1 {{
            margin: 0;
            font-size: 34px;
            letter-spacing: -0.5px;
        }}

        .header p {{
            margin: 10px 0 0 0;
            font-size: 17px;
            color: #dbeafe;
        }}

        .tag {{
            display: inline-block;
            margin-top: 18px;
            padding: 8px 12px;
            background: rgba(255,255,255,0.12);
            border: 1px solid rgba(255,255,255,0.25);
            border-radius: 999px;
            font-size: 13px;
            color: #e0f2fe;
        }}

        .cards {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 18px;
            margin-bottom: 24px;
        }}

        .card {{
            background: white;
            padding: 22px;
            border-radius: 16px;
            box-shadow: 0 8px 22px rgba(15, 23, 42, 0.08);
            border: 1px solid #e5e7eb;
        }}

        .card h3 {{
            margin: 0 0 8px 0;
            font-size: 14px;
            color: #64748b;
            font-weight: 600;
            text-transform: uppercase;
        }}

        .card .value {{
            font-size: 30px;
            font-weight: 800;
            color: #0f172a;
        }}

        .grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 22px;
            margin-bottom: 24px;
        }}

        .panel {{
            background: white;
            border-radius: 16px;
            padding: 22px;
            box-shadow: 0 8px 22px rgba(15, 23, 42, 0.08);
            border: 1px solid #e5e7eb;
        }}

        .panel h2 {{
            margin: 0 0 12px 0;
            font-size: 20px;
            color: #0f172a;
        }}

        .insights {{
            background: #0f172a;
            color: white;
            border-radius: 16px;
            padding: 26px;
            margin-bottom: 24px;
            box-shadow: 0 8px 22px rgba(15, 23, 42, 0.18);
        }}

        .insights h2 {{
            margin-top: 0;
            color: #f8fafc;
        }}

        .insights ul {{
            margin-bottom: 0;
            line-height: 1.7;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 14px;
        }}

        th {{
            background: #0f172a;
            color: white;
            padding: 12px;
            text-align: left;
        }}

        td {{
            padding: 11px 12px;
            border-bottom: 1px solid #e5e7eb;
        }}

        tr:hover {{
            background: #f8fafc;
        }}

        .badge {{
            display: inline-block;
            padding: 5px 9px;
            background: #e0f2fe;
            color: #075985;
            border-radius: 999px;
            font-weight: 700;
            font-size: 12px;
        }}

        .footer {{
            margin-top: 28px;
            color: #64748b;
            font-size: 13px;
            text-align: center;
        }}

        @media (max-width: 900px) {{
            .cards, .grid {{
                grid-template-columns: 1fr;
            }}

            .header h1 {{
                font-size: 26px;
            }}
        }}
    </style>
</head>

<body>
    <div class="container">

        <div class="header">
            <h1>Alagoas Political Intelligence</h1>
            <p>Dashboard Executivo de Inteligência Territorial e Eleitoral — Municípios de Alagoas | 2024</p>
            <div class="tag">Entrega 01 · Ranking Estratégico Municipal · Expansão Política 2026-2028</div>
        </div>

        <div class="cards">
            <div class="card">
                <h3>Municípios Analisados</h3>
                <div class="value">{total_municipios}</div>
            </div>

            <div class="card">
                <h3>População Estimada</h3>
                <div class="value">{formatar_numero(populacao_total)}</div>
            </div>

            <div class="card">
                <h3>Eleitorado 2024</h3>
                <div class="value">{formatar_numero(eleitorado_total)}</div>
            </div>

            <div class="card">
                <h3>Taxa Estadual de Eleitorado</h3>
                <div class="value">{formatar_percentual(taxa_eleitorado_estadual)}</div>
            </div>
        </div>

        <div class="insights">
            <h2>Leitura Estratégica Inicial</h2>
            <ul>
                <li>Maceió concentra {formatar_percentual(maceio["participacao_eleitorado_pct"])} do eleitorado estadual.</li>
                <li>Arapiraca representa {formatar_percentual(arapiraca["participacao_eleitorado_pct"])} do eleitorado estadual.</li>
                <li>Somadas, Maceió e Arapiraca concentram {formatar_percentual(maceio["participacao_eleitorado_pct"] + arapiraca["participacao_eleitorado_pct"])} dos eleitores de Alagoas.</li>
                <li>O Top 10 municipal concentra {formatar_percentual(top10_participacao)} do eleitorado estadual.</li>
                <li>A segunda camada estratégica está nos municípios médios do interior, com destaque para Rio Largo, Palmeira dos Índios, União dos Palmares, Marechal Deodoro, Penedo e São Miguel dos Campos.</li>
                <li>A próxima entrega deve aprofundar Quebrangulo, Palmeira dos Índios e municípios de influência regional para uma leitura 2028.</li>
            </ul>
        </div>

        <div class="grid">
            <div class="panel">
                <h2>Top 20 por Eleitorado</h2>
                <div id="grafico-eleitorado"></div>
            </div>

            <div class="panel">
                <h2>Top 20 por Índice Estratégico</h2>
                <div id="grafico-indice"></div>
            </div>
        </div>

        <div class="panel">
            <h2>Top 20 Municípios Prioritários</h2>
            <table>
                <thead>
                    <tr>
                        <th>Rank</th>
                        <th>Município</th>
                        <th>População 2024</th>
                        <th>Eleitorado 2024</th>
                        <th>Part. Eleitoral</th>
                        <th>Índice Estratégico</th>
                        <th>Prioridade</th>
                    </tr>
                </thead>
                <tbody>
                    {tabela_top20}
                </tbody>
            </table>
        </div>

        <div class="footer">
            Alagoas Political Intelligence · Dados oficiais IBGE/TSE · Pipeline ETL próprio · Dashboard gerado automaticamente
        </div>

    </div>

    <script>
        const municipiosTop20 = {json.dumps(municipios_top20, ensure_ascii=False)};
        const eleitoradoTop20 = {json.dumps(eleitorado_top20, ensure_ascii=False)};
        const indiceTop20 = {json.dumps(indice_top20, ensure_ascii=False)};

        Plotly.newPlot("grafico-eleitorado", [{{
            x: eleitoradoTop20.slice().reverse(),
            y: municipiosTop20.slice().reverse(),
            type: "bar",
            orientation: "h",
            text: eleitoradoTop20.slice().reverse().map(v => v.toLocaleString("pt-BR")),
            textposition: "auto"
        }}], {{
            margin: {{ l: 150, r: 30, t: 20, b: 40 }},
            height: 520,
            xaxis: {{ title: "Eleitorado 2024" }},
            yaxis: {{ title: "" }}
        }}, {{
            responsive: true,
            displayModeBar: false
        }});

        Plotly.newPlot("grafico-indice", [{{
            x: indiceTop20.slice().reverse(),
            y: municipiosTop20.slice().reverse(),
            type: "bar",
            orientation: "h",
            text: indiceTop20.slice().reverse().map(v => v.toFixed(2).replace(".", ",") + "%"),
            textposition: "auto"
        }}], {{
            margin: {{ l: 150, r: 30, t: 20, b: 40 }},
            height: 520,
            xaxis: {{ title: "Índice Estratégico (%)" }},
            yaxis: {{ title: "" }}
        }}, {{
            responsive: true,
            displayModeBar: false
        }});
    </script>

</body>
</html>
"""

    return html


def salvar_dashboard(html: str) -> None:
    DASHBOARD_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_HTML.write_text(html, encoding="utf-8")

    print("\nDashboard gerado com sucesso:")
    print(OUTPUT_HTML)


def main() -> None:
    print("Gerando Dashboard Executivo HTML v1.0")

    df = carregar_dados()
    html = gerar_html(df)

    salvar_dashboard(html)

    print("\nAbra o arquivo no navegador:")
    print(OUTPUT_HTML)


if __name__ == "__main__":
    main()