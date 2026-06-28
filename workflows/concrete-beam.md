# Workflow: Dimensionamento de Viga de Concreto Armado

## Gatilho

Usuário solicita dimensionamento ou verificação de viga de concreto.

## Fluxo

### Passo 1 — Coletar Dados

Verificar se o usuário forneceu:
- [ ] Tipo de viga (biapoiada, contínua, em balanço)
- [ ] Vão (m)
- [ ] Seção transversal (b x h em cm) ou pedir pré-dimensionamento
- [ ] Cargas (kN/m, kN pontuais)
- [ ] fck (MPa) — padrão: 25 MPa se não informado
- [ ] Classe de agressividade — padrão: CA-II se não informado

Se faltar dado crítico, perguntar ao usuário antes de prosseguir.

### Passo 2 — Calcular Esforços

Chamar ferramenta MCP: `calculate_beam_forces`
- Entrada: tipo de viga, vão, cargas
- Saída: Mmax (kN·m), Vmax (kN), diagrama

### Passo 3 — Combinações de Ações

Chamar ferramenta MCP: `apply_load_combinations`
- Norma: NBR 6118 §11.7 + NBR 6120
- Saída: Md, Vd (valores de cálculo)

### Passo 4 — Dimensionamento à Flexão

Chamar ferramenta MCP: `calculate_beam_flexure`
- Entrada: Md, fck, seção, tipo (retangular ou T)
- Saída: As_calc, x (linha neutra), domínio

### Passo 5 — Dimensionamento ao Cisalhamento

Chamar ferramenta MCP: `calculate_beam_shear`
- Entrada: Vd, bw, d, fck, fyk
- Saída: Asw, espaçamento de estribos

### Passo 6 — Validação

Pipeline automático:
- Verificação de unidades
- Verificação de limites físicos
- Verificação normativa (As_min, As_max, cobrimento)
- Verificação de equilíbrio

### Passo 7 — Verificações ELS (se solicitado)

- Flecha imediata e a longo prazo
- Controle de fissuração

### Passo 8 — Gerar Documentação

Chamar ferramenta MCP: `generate_memorial`
- Saída: memorial.md, planilha.xlsx, checklist preenchido

### Passo 9 — Aviso de Responsabilidade

Sempre incluir o aviso padrão de responsabilidade técnica.

## Saída Esperada

1. Armadura calculada e adotada (bitola e quantidade)
2. Resumo de verificações (todas passando)
3. Hipóteses adotadas
4. Limitações do cálculo
5. Memorial de cálculo (PDF/Markdown)
6. Planilha Excel
7. Checklist de revisão preenchido
