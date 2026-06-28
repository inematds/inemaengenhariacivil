# Workflow: Dimensionamento de Fundação em Estacas

## Gatilho

Usuário solicita projeto ou verificação de fundação em estacas.

## Fluxo

### Passo 1 — Coletar Dados

- [ ] Carga do pilar (Nd, Msd)
- [ ] Sondagem SPT disponível (número de golpes por camada)
- [ ] Tipo de estaca pretendido (pré-moldada, hélice, franki, etc.)
- [ ] Restrições de execução (vibração, barulho, espaço)

### Passo 2 — Análise da Sondagem

Chamar ferramenta MCP: `analyze_spt`
- Entrada: planilha SPT (profundidade, Nspt por camada, tipo de solo)
- Saída: perfil estratigráfico simplificado

### Passo 3 — Capacidade de Carga (Dois Métodos)

Chamar em paralelo:
- `calculate_pile_aoki_velloso` — método Aoki-Velloso
- `calculate_pile_decourt` — método Décourt-Quaresma

### Passo 4 — Comparação de Métodos

Chamar ferramenta MCP: `compare_pile_methods`
- Se divergência > 20%: alertar engenheiro
- Adotar valor mais conservador

### Passo 5 — Definir Número de Estacas

Chamar ferramenta MCP: `design_pile_group`
- Entrada: Nd, capacidade por estaca, tipo de bloco
- Saída: número de estacas, arranjo, dimensões do bloco

### Passo 6 — Dimensionar o Bloco

Chamar ferramenta MCP: `design_pile_cap`
- Entrada: número de estacas, Nd, Msd, fck
- Saída: armadura do bloco (modelo de biela-tirante)

### Passo 7 — Validação Completa

Pipeline automático de validação:
- Capacidade de carga verificada (FS >= 2.0)
- Recalque estimado
- Verificação do bloco (punção, flexão)

### Passo 8 — Gerar Documentação

Memorial + planilha + planta de locação de estacas (descrição textual)

## Saída Esperada

1. Tipo e diâmetro da estaca recomendados
2. Comprimento estimado
3. Número de estacas por pilar
4. Dimensões e armadura do bloco
5. Comparativo dos dois métodos
6. Alertas de divergência (se houver)
7. Memorial de cálculo completo
