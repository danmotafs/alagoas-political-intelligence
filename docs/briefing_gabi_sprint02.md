# Briefing — Sprint 02 — Base Eleitoral Gabi Gonçalves

## Objetivo

Criar a primeira base eleitoral própria da Gabi Gonçalves dentro do projeto alagoas-political-intelligence.

A Gabi é tratada como Deputada Estadual em mandato e candidata à reeleição em 2026.

## Decisão metodológica

A base gerada neste sprint é preliminar. Ela usa como insumos as bases municipais já existentes no projeto matriz do Davi Maia:

- base municipal de população e eleitorado;
- ranking estratégico municipal;
- base política municipal de prefeitos;
- inteligência municipal de vereadores.

## Meta eleitoral

A meta operacional preliminar definida no script foi de 45.000 votos.

Essa meta deve ser revisada após entrada da votação histórica da Gabi em 2022, base de apoiadores, municípios de mandato e alianças formalizadas.

## Arquivos gerados

- data/final/parceiros/gabi-goncalves/base_eleitoral_gabi_v1.csv
- data/final/parceiros/gabi-goncalves/base_eleitoral_gabi_v1.xlsx
- data/reference/parceiros/gabi-goncalves/campos_curadoria_gabi_v1.csv
- data/dashboard/parceiros/gabi-goncalves/base_dashboard_gabi_v1.json
- data/dashboard/parceiros/gabi-goncalves/meta_eleitoral_gabi_estadual_2026.json
- data/dashboard/parceiros/gabi-goncalves/cruzamento_davi_gabi_v1.json

## Campos de curadoria criados

- relacao_gabi
- aderencia_gabi
- grupo_politico_gabi
- status_articulacao_gabi
- prioridade_visita_gabi
- lideranca_chave_gabi
- responsavel_articulacao
- agenda_recomendada
- risco_politico
- proximo_passo

## Próximo sprint recomendado

Sprint 03 — Rede de Lideranças da Gabi.

Nesse sprint, a base de vereadores e lideranças deve ser aberta por município para identificar os nomes mais relevantes para articulação política e agenda territorial.
