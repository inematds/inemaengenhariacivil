# Lista de Agentes

## Agente Raiz

### `orchestrator`
**Responsabilidade:** Receber o problema do usuário, identificar o domínio correto, rotear para o agente especialista adequado.

**Não faz:** cálculos, interpretação de normas, geração de documentos.

**Entradas:** linguagem natural (qualquer problema de engenharia)
**Saídas:** handoff para agente especialista com contexto estruturado

---

## Agentes Estruturais

### `structural/concrete`
**Responsabilidade:** Cálculos de concreto armado conforme NBR 6118.
**Capacidades:** vigas, pilares, lajes, blocos, paredes
**Normas:** NBR 6118:2014, NBR 6120:2019, NBR 6123:1988
**Ferramentas MCP:** `calculate_beam_flexure`, `calculate_column_buckling`, `calculate_slab_armature`

### `structural/steel`
**Responsabilidade:** Estruturas metálicas conforme NBR 8800.
**Capacidades:** perfis, ligações parafusadas, ligações soldadas, flambagem lateral
**Normas:** NBR 8800:2008, NBR 6355:2012
**Ferramentas MCP:** `select_steel_profile`, `design_weld`, `design_bolt_connection`

### `structural/timber`
**Responsabilidade:** Estruturas de madeira conforme NBR 7190.
**Capacidades:** vigas, colunas, tesouras, ligações
**Normas:** NBR 7190:1997
**Ferramentas MCP:** `calculate_timber_beam`, `calculate_timber_column`

### `structural/masonry`
**Responsabilidade:** Alvenaria estrutural conforme NBR 15812.
**Capacidades:** paredes portantes, blocos, graute
**Normas:** NBR 15812:2010, NBR 15961:2011

---

## Agentes Geotécnicos

### `geotechnical/foundations`
**Responsabilidade:** Dimensionamento de fundações conforme NBR 6122.
**Capacidades:** sapatas, blocos, radier, estacas, tubulões
**Normas:** NBR 6122:2010, NBR 6484:2020 (SPT)
**Ferramentas MCP:** `calculate_footing`, `calculate_pile_capacity`

### `geotechnical/retaining-walls`
**Responsabilidade:** Muros de arrimo e estruturas de contenção.
**Capacidades:** empuxo ativo/passivo, deslizamento, tombamento, ruptura
**Normas:** NBR 11682:2009

### `geotechnical/slope-stability`
**Responsabilidade:** Estabilidade de taludes e encostas.
**Capacidades:** fator de segurança, superfície de ruptura
**Normas:** NBR 11682:2009

---

## Agentes Hidráulicos

### `hydraulic/water-supply`
**Responsabilidade:** Redes de abastecimento de água.
**Capacidades:** dimensionamento de tubulações, reservatórios, recalque
**Normas:** NBR 12218:2017, NBR 5626:2020
**Ferramentas MCP:** `calculate_pipe_flow`, `calculate_head_loss`

### `hydraulic/sewage`
**Responsabilidade:** Redes de esgoto sanitário.
**Capacidades:** coletores, poços de visita, emissários
**Normas:** NBR 9649:1986, NBR 9800:1987

### `hydraulic/stormwater`
**Responsabilidade:** Drenagem pluvial urbana.
**Capacidades:** bacias de contribuição, tempo de concentração, dimensionamento
**Referências:** Manual DAEE, manuais municipais

---

## Agentes de Infraestrutura

### `roads/pavement`
**Responsabilidade:** Dimensionamento de pavimentos.
**Capacidades:** pavimento flexível, rígido, número N
**Referências:** DNIT 005/2003, método USACE

### `roads/earthwork`
**Responsabilidade:** Terraplanagem e movimentação de terra.
**Capacidades:** volumes de corte/aterro, compactação, empréstimos

---

## Agentes de Suporte

### `budget`
**Responsabilidade:** Orçamentação de obras civis.
**Capacidades:** composições SINAPI, BDI, cronograma físico-financeiro
**Integrações:** SINAPI (CSV), planilhas Excel

### `review`
**Responsabilidade:** Revisão técnica independente de cálculos existentes.
**Capacidades:** verificação de hipóteses, limitações, conformidade normativa
**Saídas:** relatório de revisão com parecer técnico

### `report`
**Responsabilidade:** Geração de documentação técnica.
**Capacidades:** memorial de cálculo, relatório técnico, laudo, parecer
**Saídas:** Markdown → PDF, Excel

### `norms`
**Responsabilidade:** Consulta e interpretação de normas técnicas.
**Capacidades:** localizar tabelas, interpolar valores, identificar requisitos
**Base de dados:** `normas/` (tabelas JSON extraídas das NBRs)

---

## Tabela Resumo

| Agente | Domínio | Normas Principais |
|--------|---------|-------------------|
| orchestrator | Geral | — |
| concrete | Concreto armado | NBR 6118 |
| steel | Estruturas metálicas | NBR 8800 |
| timber | Madeira | NBR 7190 |
| masonry | Alvenaria | NBR 15812 |
| foundations | Fundações | NBR 6122 |
| retaining-walls | Muros | NBR 11682 |
| slope-stability | Taludes | NBR 11682 |
| water-supply | Água | NBR 12218, 5626 |
| sewage | Esgoto | NBR 9649 |
| stormwater | Drenagem | DAEE |
| pavement | Pavimentação | DNIT 005 |
| earthwork | Terraplenagem | — |
| budget | Orçamento | SINAPI |
| review | Revisão | — |
| report | Documentação | ABNT NBR 14724 |
| norms | Normas | Todas |
