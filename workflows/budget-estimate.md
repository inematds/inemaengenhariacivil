# Workflow: Estimativa de Orçamento

## Gatilho

Usuário solicita orçamento paramétrico ou detalhado de obra civil.

## Fluxo

### Passo 1 — Identificar Tipo de Orçamento

- **Paramétrico:** estimativa rápida por m² ou unidade (precisão ±30%)
- **Sintético:** por grandes grupos (fundação, estrutura, acabamento) (±20%)
- **Analítico:** composição unitária detalhada com SINAPI (±10%)

Perguntar ao usuário qual nível de detalhe é necessário.

### Passo 2 — Coletar Dados

- [ ] Tipo de obra (residencial, comercial, industrial, infraestrutura)
- [ ] Área ou quantidade de serviço
- [ ] Localização (estado/município para SINAPI regional)
- [ ] Data de referência (mês/ano)
- [ ] Padrão construtivo

### Passo 3 — Buscar Composições SINAPI

Chamar ferramenta MCP: `search_sinapi`
- Entrada: descrição do serviço, UF, mês/ano
- Saída: código SINAPI, custo unitário sem BDI

### Passo 4 — Calcular Quantitativos

Chamar ferramenta MCP: `calculate_quantities`
- Entrada: projetos ou estimativas
- Saída: quantitativos por serviço

### Passo 5 — Calcular BDI

Chamar ferramenta MCP: `calculate_bdi`
- Componentes: administração central, risco, despesas financeiras, lucro
- Referência: Acórdão TCU 2622/2013

### Passo 6 — Montar Planilha Orçamentária

Chamar ferramenta MCP: `generate_budget_spreadsheet`
- Formato: código SINAPI, descrição, unidade, quantidade, custo unit., total
- Agrupamento por etapa da obra

### Passo 7 — Curva ABC

Identificar os 20% de itens que representam 80% do custo (Pareto).

### Passo 8 — Gerar Documentação

Planilha Excel formatada + relatório resumo + cronograma físico-financeiro básico

## Saída Esperada

1. Planilha orçamentária completa (Excel)
2. Resumo por etapa e total geral
3. BDI calculado e justificado
4. Curva ABC dos principais itens
5. Prazo estimado de execução
6. Cronograma físico-financeiro (percentual por mês)
