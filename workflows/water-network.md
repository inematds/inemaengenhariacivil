# Workflow: Dimensionamento de Rede de Abastecimento de Água

## Gatilho

Usuário solicita dimensionamento de rede de distribuição de água.

## Fluxo

### Passo 1 — Coletar Dados

- [ ] População de projeto (ou número de economias)
- [ ] Per capita de consumo (L/hab/dia) ou padrão NBR
- [ ] Coeficientes K1 (dia de maior consumo) e K2 (hora de maior consumo)
- [ ] Traçado da rede (comprimentos, cotas)
- [ ] Pressão disponível na entrada

### Passo 2 — Calcular Vazões

Chamar ferramenta MCP: `calculate_water_demand`
- Q_dia_médio = per_capita × pop / 86400
- Q_dia_max = K1 × Q_dia_médio
- Q_hora_max = K2 × Q_dia_max

### Passo 3 — Dimensionar Tubulações

Para cada trecho:
Chamar ferramenta MCP: `size_pipe`
- Entrada: Q, velocidade máxima, material (PVC, PEAD, FoFo)
- Saída: diâmetro nominal, velocidade real

### Passo 4 — Calcular Perdas de Carga

Chamar ferramenta MCP: `calculate_head_loss_network`
- Método: Hazen-Williams
- Saída: hf por trecho, pressão em cada nó

### Passo 5 — Verificar Pressões

Chamar ferramenta MCP: `check_pressures`
- Pressão mínima: 10 mca (NBR 12218)
- Pressão máxima: 50 mca (NBR 12218)
- Se algum nó falhar: redimensionar

### Passo 6 — Dimensionar Reservatório

Chamar ferramenta MCP: `size_reservoir`
- Volume mínimo = 1/4 do consumo diário médio

### Passo 7 — Validação

Pipeline de validação:
- Velocidades dentro dos limites (0.6 a 3.0 m/s)
- Pressões dentro dos limites em todos os nós
- Reservatório adequado

### Passo 8 — Gerar Documentação

Memorial + planilha com quadro de tubulações + mapa de pressões

## Saída Esperada

1. Diâmetros de cada trecho
2. Pressões em todos os nós
3. Volume do reservatório
4. Quadro resumo de materiais (quantitativos)
5. Memorial de cálculo completo
