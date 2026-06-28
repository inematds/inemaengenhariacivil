# Workflow: Capacidade de Carga de Fundação em Estacas (por SPT)

## Gatilho

Usuário solicita a capacidade de carga de uma estaca a partir de sondagem SPT.

## Princípio

Números só vêm do `calc-server` (MCP). A ferramenta `capacidade_estaca` roda os **dois
métodos semiempíricos** (Aoki-Velloso e Décourt-Quaresma), valida ambos e compara o
resultado — o agente nunca calcula à mão (princípio da abstenção).

## Fluxo real

### Passo 1 — Coletar dados

- [ ] Perfil de sondagem SPT: para cada camada atravessada, o número de golpes `N`, o
      tipo de solo (texto da tabela de Aoki-Velloso) e a espessura (m). A ponta da estaca
      fica na base da última camada; o comprimento L é a soma das espessuras.
- [ ] Tipo de estaca: `pre-moldada`, `metalica`, `franki` ou `escavada`.
- [ ] Diâmetro D (m).
- [ ] Fator de segurança global FS (default 2,0, NBR 6122).

### Passo 2 — Montar o perfil

Estruture o perfil como a lista `layers` de objetos:

```json
[
  {"n_spt": 8,  "soil_type": "argila siltosa", "thickness_m": 4.0},
  {"n_spt": 20, "soil_type": "areia siltosa",  "thickness_m": 6.0}
]
```

Tabelas de consulta (espelham o núcleo): `normas/NBR6122/tables/aoki_velloso_k_alpha.json`,
`aoki_velloso_f1_f2.json` e `decourt_c.json`.

### Passo 3 — Calcular e comparar (uma chamada)

Chamar a ferramenta MCP `capacidade_estaca`:

```
capacidade_estaca(layers, pile_type="pre-moldada", diameter_m=0.30, fs=2.0, tol=0.20)
```

Internamente (`lib.service.solve_pile_comparison` → `comparar_metodos_estaca`):
- **Aoki-Velloso (1975):** Rp = (K·Np/F1)·Ap ; Rl = Σ (α·K·Nl/F2)·U·ΔL.
- **Décourt-Quaresma (1978):** Rp = C·Np·Ap ; Rl = 10·(Ns/3 + 1)·U·L.
- **Comparação:** divergência relativa de Rult; `convergem = divergência ≤ 20%`.

### Passo 4 — Validação automática

A resposta traz `validacao` com as checagens de **ambos** os métodos (unidades, física,
normativa, FS) e a checagem de **convergência**:
- Se a divergência > 20%: a validação emite **aviso** e `convergem = false` — alertar o
  engenheiro e adotar o valor mais conservador (menor Radm).
- `aprovado` reflete a validação dos dois métodos (a divergência entra como aviso).

### Passo 5 — Apresentar

Apresente o `memorial_markdown` retornado (tabela Aoki × Décourt com Rp/Rl/Rult/Radm e a
divergência) e o aviso de responsabilidade (`aviso`).

## Saída esperada

1. Rult e Radm por cada método (Aoki-Velloso e Décourt-Quaresma).
2. Divergência relativa e situação de convergência (≤ 20%).
3. Comprimento e geometria da estaca consideradas.
4. Memorial de cálculo comparativo completo.
5. Alerta de divergência (se houver) e o aviso de responsabilidade técnica.

## Fora do escopo (abster-se)

Definição do número de estacas e arranjo, dimensionamento do bloco de coroamento
(biela-tirante), recalque do grupo, atrito negativo e prova de carga — não há ferramenta:
avisar o usuário. A escolha do método de execução e do FS é do engenheiro.
