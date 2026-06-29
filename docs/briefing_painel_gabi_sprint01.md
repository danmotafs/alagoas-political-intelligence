# Briefing — Sprint 01 — Painel Parceiro Gabi Gonçalves

## Objetivo

Criar a estrutura inicial do painel individualizado da Gabi Gonçalves dentro do projeto alagoas-political-intelligence, mantendo Davi Maia como eixo político principal e a Gabi como parceira de pré-campanha para Deputada Estadual.

## Decisão estratégica

O painel da Gabi não será um projeto isolado neste momento. Ele será criado como módulo parceiro dentro do projeto principal do Davi Maia.

Estrutura de acesso prevista:

- Painel principal Davi Maia: /dashboard_v2/
- Painel parceiro Gabi Gonçalves: /parceiros/gabi-goncalves/

## Identidade visual

A identidade do painel da Gabi foi baseada na logomarca enviada:

- Azul principal: #1A4392
- Azul escuro: #0B1F4D
- Amarelo destaque: #F1D214
- Rosa campanha: #E280B2
- Fundo claro: #F6F8FC

## Arquivos criados

- parceiros/gabi-goncalves/index.html
- parceiros/gabi-goncalves/styles.css
- parceiros/gabi-goncalves/app.js
- parceiros/gabi-goncalves/assets/logo-gabi-2026.png
- data/dashboard/parceiros/gabi-goncalves/base_dashboard_gabi_v1.json
- data/dashboard/parceiros/gabi-goncalves/meta_eleitoral_gabi_estadual_2026.json
- data/dashboard/parceiros/gabi-goncalves/cruzamento_davi_gabi_v1.json
- docs/briefing_painel_gabi_sprint01.md
- scripts/setup/criar_painel_gabi_sprint01.py

## Modelo político adotado

O Davi Maia é tratado como eixo principal da rede de inteligência política.

A Gabi Gonçalves passa a ser analisada como parceira estadual, com painel próprio, identidade visual própria e futura camada de cruzamento territorial com a base do Davi.

## Próximos sprints sugeridos

### Sprint 02 — Base Eleitoral da Gabi

- Definir meta eleitoral estadual.
- Criar campos próprios:
  - relacao_gabi
  - aderencia_gabi
  - grupo_politico_gabi
  - status_articulacao_gabi
  - prioridade_visita_gabi
- Gerar primeira base de municípios prioritários.

### Sprint 03 — Rede de Lideranças

- Cruzar vereadores, prefeitos, partidos, votação e potencial de apoio.
- Criar ranking de lideranças estratégicas para a Gabi.

### Sprint 04 — Cruzamento Davi x Gabi

- Identificar municípios de alta sinergia.
- Mapear agendas conjuntas recomendadas.
- Criar score de eficiência territorial da parceria.

### Sprint 05 — Publicação

- Validar localmente.
- Subir ao GitHub.
- Publicar no GitHub Pages.

## Link previsto após publicação

https://danmotafs.github.io/alagoas-political-intelligence/parceiros/gabi-goncalves/
