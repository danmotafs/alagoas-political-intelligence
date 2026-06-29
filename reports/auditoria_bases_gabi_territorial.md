# Auditoria das Bases Territoriais da Gabi Gonçalves

Data de geração: 29/06/2026 14:45:30

## 1. Objetivo

Esta auditoria verifica quais bases da Gabi Gonçalves já existem no projeto, quais colunas estão disponíveis e se é possível iniciar a territorialização por seção eleitoral, local de votação, bairro ou região.

## 2. Bases verificadas

| Tipo | Existe | Encoding | Separador | Arquivo | Colunas / Chaves | Ocorrências de Gabi na amostra | Erro |
|---|---:|---|---|---|---|---:|---|
| csv | True | utf-8-sig | , | C:\Users\user\Documents\Workspace\campanha_2026\alagoas-political-intelligence\data\final\parceiros\gabi-goncalves\base_eleitoral_gabi_v1.csv | ranking_gabi_preliminar / municipio / eleitorado / populacao / score_gabi_preliminar / prioridade_visita_gabi / status_articulacao_gabi / meta_votos_referencia_gabi / ranking_base_davi / indice_estrategico_base_davi / prefeito_2024 / partido_prefeito_2024 / votos_prefeito_2024 / margem_vitoria_prefeito / vereadores_mapeados / votos_vereadores_total / potencial_transferencia_vereadores_5pct / potencial_transferencia_vereadores_10pct / potencial_transferencia_vereadores_15pct / relacao_gabi / aderencia_gabi / grupo_politico_gabi / observacao_curadoria_gabi / justificativa_prioridade_gabi / municipio_key | 1 |  |
| csv | True | utf-8-sig | , | C:\Users\user\Documents\Workspace\campanha_2026\alagoas-political-intelligence\data\final\parceiros\gabi-goncalves\cruzamento_davi_gabi_v1.csv | ranking_sinergia_davi_gabi / municipio / prioridade_sinergia_davi_gabi / status_agenda_conjunta / score_sinergia_davi_gabi / ranking_gabi_preliminar / prioridade_visita_gabi / score_gabi_preliminar / ranking_davi_ref / score_davi_ref / ranking_base_davi / indice_estrategico_base_davi / eleitorado / populacao / meta_votos_referencia_gabi / liderancas_mapeadas / principal_lideranca / partido_principal_lideranca / votos_principal_lideranca / prioridade_principal_lideranca / votos_liderancas_total / potencial_transferencia_10pct / prefeito_2024 / partido_prefeito_2024 / relacao_gabi / aderencia_gabi / grupo_politico_gabi / semana_sugerida / acao_recomendada / formato_agenda_recomendada / justificativa_sinergia / municipio_key | 2 |  |
| csv | True | utf-8-sig | , | C:\Users\user\Documents\Workspace\campanha_2026\alagoas-political-intelligence\data\final\parceiros\gabi-goncalves\curadoria_politica_davi_gabi_v1.csv | ordem_curadoria / prioridade_curadoria / prazo_curadoria / semana_roteiro / dia_sugerido / turno_sugerido / municipio / macro_regiao / eixo_logistico / prioridade_sinergia_davi_gabi / status_agenda_conjunta / score_sinergia_davi_gabi / principal_lideranca / partido_principal_lideranca / prefeito_2024 / partido_prefeito_2024 / meta_votos_referencia_gabi / potencial_transferencia_10pct / tipo_agenda / acao_recomendada / objetivo_politico / relacao_gabi / relacao_davi / relacao_renan_filho / relacao_renan_calheiros / relacao_paulo_dantas / grupo_politico_local / alinhamento_governo_estadual / alinhamento_davi / alinhamento_gabi / status_validacao_lideranca / status_validacao_prefeito / status_validacao_grupo_local / risco_politico / conflito_apoio / sensibilidade_local / decisao_agenda / agenda_publica_ou_reservada / pergunta_chave_curadoria / criterio_para_avancar / responsavel_curadoria / contato_local / data_validacao / proximo_passo / observacao_politica / observacao_logistica / justificativa_sinergia / municipio_key | 30 |  |
| csv | True | utf-8-sig | , | C:\Users\user\Documents\Workspace\campanha_2026\alagoas-political-intelligence\data\final\parceiros\gabi-goncalves\rede_liderancas_gabi_v1.csv | ranking_lideranca_gabi / municipio / ranking_gabi_preliminar / prioridade_visita_gabi / status_articulacao_gabi / nome_lideranca / tipo_lideranca / partido / situacao_eleitoral / votos_2024 / rank_local_lideranca / participacao_votos_lideranca_pct / score_lideranca_gabi / prioridade_lideranca_gabi / status_curadoria_lideranca / potencial_transferencia_5pct / potencial_transferencia_10pct / potencial_transferencia_15pct / eleitorado / populacao / meta_votos_referencia_gabi / prefeito_2024 / partido_prefeito_2024 / relacao_gabi / aderencia_gabi / grupo_politico_gabi / abordagem_recomendada / responsavel_articulacao / telefone_contato / observacao_curadoria / risco_politico / proximo_passo / municipio_key | 51 |  |
| csv | True | utf-8-sig | , | C:\Users\user\Documents\Workspace\campanha_2026\alagoas-political-intelligence\data\final\parceiros\gabi-goncalves\resumo_liderancas_municipio_gabi_v1.csv | municipio / municipio_key / ranking_gabi_preliminar / prioridade_visita_gabi / status_articulacao_gabi / liderancas_mapeadas / votos_liderancas_total / potencial_transferencia_5pct / potencial_transferencia_10pct / potencial_transferencia_15pct / maior_score_lideranca / principal_lideranca / partido_principal_lideranca / votos_principal_lideranca / prioridade_principal_lideranca | 0 |  |
| csv | True | utf-8-sig | , | C:\Users\user\Documents\Workspace\campanha_2026\alagoas-political-intelligence\data\final\parceiros\gabi-goncalves\roteiro_territorial_davi_gabi_v1.csv | ordem_prioridade / semana_roteiro / semana_numero / ordem_na_semana / dia_sugerido / turno_sugerido / municipio / macro_regiao / eixo_logistico / prioridade_sinergia_davi_gabi / status_agenda_conjunta / score_sinergia_davi_gabi / principal_lideranca / partido_principal_lideranca / prefeito_2024 / partido_prefeito_2024 / meta_votos_referencia_gabi / potencial_transferencia_10pct / tipo_agenda / acao_recomendada / objetivo_politico / formato_agenda_recomendada / justificativa_sinergia / preparacao_previa / observacao_logistica / produto_esperado / responsavel_preparacao / contato_local / data_sugerida / status_execucao / observacao_politica / municipio_key | 4 |  |
| json | True | utf-8 |  | C:\Users\user\Documents\Workspace\campanha_2026\alagoas-political-intelligence\data\dashboard\parceiros\gabi-goncalves\base_dashboard_gabi_v1.json | metadata / identidade_visual / indicadores_alagoas / indicadores_gabi / ranking_municipios / liderancas / oportunidades / proximos_passos / resumo_liderancas_municipio / oportunidades_sinergia / roteiro_territorial_davi_gabi / resumo_semanal_roteiro / curadoria_politica_davi_gabi |  |  |
| json | True | utf-8 |  | C:\Users\user\Documents\Workspace\campanha_2026\alagoas-political-intelligence\data\dashboard\parceiros\gabi-goncalves\cruzamento_davi_gabi_v1.json | metadata / eixo_politico / cards / municipios_alta_sinergia_preliminar / campos_futuros / liderancas_prioritarias_preliminares / municipios_com_maior_rede_liderancas / indicadores / municipios_alta_sinergia / agenda_conjunta_recomendada / roteiro_territorial / resumo_semanal_roteiro / curadoria_politica |  |  |
| json | True | utf-8 |  | C:\Users\user\Documents\Workspace\campanha_2026\alagoas-political-intelligence\data\dashboard\parceiros\gabi-goncalves\curadoria_politica_davi_gabi_v1.json | metadata / indicadores / resumo_prioridade / curadoria |  |  |
| json | True | utf-8 |  | C:\Users\user\Documents\Workspace\campanha_2026\alagoas-political-intelligence\data\dashboard\parceiros\gabi-goncalves\meta_eleitoral_gabi_estadual_2026.json | metadata / meta_eleitoral_gabi_2026 / cenarios_meta / cenarios_transferencia_vereadores |  |  |
| json | True | utf-8 |  | C:\Users\user\Documents\Workspace\campanha_2026\alagoas-political-intelligence\data\dashboard\parceiros\gabi-goncalves\roteiro_territorial_davi_gabi_v1.json | metadata / indicadores / resumo_semanal / roteiro |  |  |
| csv | True | utf-8-sig | ; | C:\Users\user\Documents\Workspace\campanha_2026\alagoas-political-intelligence\data\final\locais_votacao_top10.csv | municipio / local_votacao / endereco_local_votacao / qtd_secoes / qtd_vereadores / votos_totais / chave_local | 3 |  |
| csv | True | utf-8-sig | ; | C:\Users\user\Documents\Workspace\campanha_2026\alagoas-political-intelligence\data\final\mapa_influencia_geografico.csv | municipio / vereador / partido / zona / secao / votos / percentual / ranking_secao / prioridade_territorial / potencial_transferencia_local / local_votacao / endereco_local_votacao / latitude / longitude / bairro / distrito / status_geocodificacao / consulta_geocoding / qtd_secoes_local / qtd_vereadores_local / votos_totais_local / total_votos_vereador_municipio / total_secoes_com_votos | 0 |  |
| csv | True | utf-8-sig | ; | C:\Users\user\Documents\Workspace\campanha_2026\alagoas-political-intelligence\data\final\mapa_influencia_vereadores_top10.csv | municipio / vereador / partido / zona / secao / votos / percentual / ranking_secao / prioridade_territorial / potencial_transferencia_local / local_votacao / endereco_local_votacao / total_votos_vereador_municipio / total_secoes_com_votos | 0 |  |
| csv | True | utf-8-sig | ; | C:\Users\user\Documents\Workspace\campanha_2026\alagoas-political-intelligence\data\final\polos_eleitorais_top10.csv | municipio / ranking_polo_municipal / ranking_polo_geral / local_votacao / endereco_local_votacao / latitude / longitude / bairro / distrito / status_geocodificacao / qtd_secoes / qtd_vereadores / votos_totais / vereador_principal / partido_vereador_principal / votos_vereador_principal / percentual_dominancia / indice_influencia_local / classificacao_local / potencial_agenda_davi | 3 |  |
| csv | True | utf-8-sig | ; | C:\Users\user\Documents\Workspace\campanha_2026\alagoas-political-intelligence\data\final\redutos_vereadores_top10.csv | municipio / vereador / partido / ranking_reduto_geral / local_principal / endereco_local_principal / latitude / longitude / bairro / distrito / status_geocodificacao / votos_local_principal / votos_totais_vereador / percentual_local_principal / qtd_secoes_controladas / total_secoes_vereador / indice_reduto / classificacao_reduto | 5 |  |
| csv | True | utf-8-sig | ; | C:\Users\user\Documents\Workspace\campanha_2026\alagoas-political-intelligence\data\final\redutos_qualificados_top10.csv | ranking_reduto_qualificado / municipio / vereador / partido / local_principal / endereco_local_principal / latitude / longitude / bairro / distrito / status_geocodificacao / votos_local_principal / votos_totais_vereador / percentual_local_principal / qtd_secoes_controladas / total_secoes_vereador / indice_reduto / classificacao_reduto / status_reduto / nivel_reduto / potencial_transferencia / prioridade_agenda / observacao_estrategica | 1 |  |

## 3. Arquivo oficial de votação por seção do TSE

- Arquivo: `C:\Users\user\Documents\Workspace\campanha_2026\alagoas-political-intelligence\data\raw\tse_2024\votacao_secao_2024_AL.csv`
- Existe: True
- Encoding detectado: latin-1
- Separador detectado: `;`
- Linhas lidas: 431472
- Ocorrências encontradas com termos GABI/GABRIELA/GONÇALVES: 4879

### Colunas do arquivo TSE

- DT_GERACAO
- HH_GERACAO
- ANO_ELEICAO
- CD_TIPO_ELEICAO
- NM_TIPO_ELEICAO
- NR_TURNO
- CD_ELEICAO
- DS_ELEICAO
- DT_ELEICAO
- TP_ABRANGENCIA
- SG_UF
- SG_UE
- NM_UE
- CD_MUNICIPIO
- NM_MUNICIPIO
- NR_ZONA
- NR_SECAO
- CD_CARGO
- DS_CARGO
- NR_VOTAVEL
- NM_VOTAVEL
- QT_VOTOS
- NR_LOCAL_VOTACAO
- SQ_CANDIDATO
- NM_LOCAL_VOTACAO
- DS_LOCAL_VOTACAO_ENDERECO

## 4. Interpretação

Foram encontradas ocorrências ligadas à Gabi/Gabriela/Gonçalves no arquivo oficial de votação por seção. O próximo passo é validar qual registro corresponde exatamente à Gabi Gonçalves e gerar a base territorial.

