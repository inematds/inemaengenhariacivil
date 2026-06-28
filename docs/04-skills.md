# Lista de Skills

Skills são unidades de cálculo independentes e reutilizáveis. Cada skill tem uma responsabilidade única e pode ser chamada por qualquer agente.

## Skills Estruturais

### Concreto Armado
| Skill | Descrição | Norma | Entrada | Saída |
|-------|-----------|-------|---------|-------|
| `beam-bending` | Flexão simples e composta | NBR 6118 §17 | Md, fck, seção | As, detalhamento |
| `beam-shear` | Cisalhamento em vigas | NBR 6118 §17.4 | Vd, bw, d | Asw, espaçamento |
| `beam-torsion` | Torção em vigas | NBR 6118 §17.5 | Td, seção | Asl, Asw |
| `column-buckling` | Flambagem de pilares | NBR 6118 §15 | Nd, Md, índice esb. | As, verificação |
| `slab-armature` | Armadura de lajes | NBR 6118 §19 | p, vão, tipo | As por faixa |
| `footing-design` | Dimensionamento de sapatas | NBR 6118 §22 | Nd, Msd, σ_solo | dimensões, As |
| `crack-control` | Controle de fissuração | NBR 6118 §17.3.3 | Mk, armadura | wk |
| `deflection-check` | Verificação de flechas | NBR 6118 §17.3.2 | EI, vão, carga | flecha imediata/total |

### Estruturas Metálicas
| Skill | Descrição | Norma | Entrada | Saída |
|-------|-----------|-------|---------|-------|
| `steel-profile` | Seleção de perfil | NBR 8800 | Md, Vd, Nd | perfil recomendado |
| `weld-design` | Dimensionamento de solda | NBR 8800 §6.2 | força, tipo | tamanho do cordão |
| `bolt-design` | Dimensionamento de parafusos | NBR 8800 §6.3 | força, diâmetro | número de parafusos |
| `lateral-buckling` | Flambagem lateral com torção | NBR 8800 §5.4 | perfil, Lb | Mn resistente |

### Madeira
| Skill | Descrição | Norma |
|-------|-----------|-------|
| `timber-beam` | Viga de madeira | NBR 7190 |
| `timber-column` | Coluna de madeira | NBR 7190 |
| `timber-connection` | Ligações em madeira | NBR 7190 |

---

## Skills Geotécnicas

| Skill | Descrição | Método | Entrada | Saída |
|-------|-----------|--------|---------|-------|
| `pile-aoki-velloso` | Capacidade de estaca | Aoki-Velloso | SPT, tipo, diâm. | Rp + Rs = R |
| `pile-decourt` | Capacidade de estaca | Décourt-Quaresma | SPT, tipo, diâm. | Pu |
| `pile-comparison` | Comparação de métodos | Ambos | SPT | tabela comparativa |
| `footing-bearing` | Capacidade de carga de sapata | Terzaghi, Meyerhof | SPT, B, L | q_adm |
| `settlement-elastic` | Recalque elástico | Teoria da elasticidade | E_solo, carga | δ |
| `rankine-pressure` | Empuxo de Rankine | Rankine | φ, γ, H | Ka, Kp, E |
| `coulomb-pressure` | Empuxo de Coulomb | Coulomb | φ, δ, γ, H | Ka, Kp, E |
| `retaining-wall-check` | Verificação muro de arrimo | — | geometria, cargas | FS desliz., tomba. |

---

## Skills Hidráulicas

| Skill | Descrição | Método | Entrada | Saída |
|-------|-----------|--------|---------|-------|
| `hazen-williams` | Perda de carga em tubulações | Hazen-Williams | Q, D, L, C | hf |
| `darcy-weisbach` | Perda de carga (alternativo) | Darcy-Weisbach | Q, D, L, f | hf |
| `manning-channel` | Escoamento em canal aberto | Manning | n, S, seção | Q, v |
| `pipe-sizing` | Dimensionamento de tubulação | Hazen-Williams | Q, v_max, hf_max | D nominal |
| `pump-head` | Altura manométrica de bomba | — | reservatórios, hf | Hm |
| `rainfall-idf` | Chuva intensa (IDF) | — | cidade, TR, tc | i (mm/h) |
| `runoff-rational` | Vazão de projeto | Método racional | C, i, A | Q (m³/s) |

---

## Skills Utilitárias

| Skill | Descrição |
|-------|-----------|
| `unit-converter` | Conversão e verificação dimensional (pint) |
| `load-combinator` | Combinações de ações NBR 6118/6120 |
| `interpolate-table` | Interpolação linear/bilinear em tabelas de norma |
| `second-method-check` | Executa método alternativo e compara |
| `excel-export` | Exporta resultados para planilha Excel |
| `pdf-export` | Gera PDF a partir de template Markdown |
| `checklist-runner` | Executa checklist JSON e gera relatório |
| `memorial-generator` | Gera memorial de cálculo padronizado |

---

## Estrutura de uma Skill (template)

```
skills/
└── beam-bending/
    ├── README.md          # Descrição, objetivo, exemplos
    ├── input_schema.json  # Schema Pydantic em JSON
    ├── output_schema.json # Schema de saída
    └── examples/
        ├── example_01.json
        └── example_02.json
```

### README.md de uma skill (template)

```markdown
# Skill: beam-bending

**Objetivo:** Dimensionamento à flexão simples de vigas de concreto armado.

**Norma:** NBR 6118:2014, §17.2

## Entradas

| Parâmetro | Unidade | Descrição |
|-----------|---------|-----------|
| fck | MPa | Resistência característica do concreto |
| fyk | MPa | Resistência característica do aço (500 padrão) |
| Md | kN·m | Momento fletor de cálculo |
| b | cm | Largura da seção |
| h | cm | Altura total da seção |
| d | cm | Altura útil (ou calculada automaticamente) |

## Saídas

| Parâmetro | Unidade | Descrição |
|-----------|---------|-----------|
| As_calc | cm² | Área de armadura calculada |
| As_min | cm² | Armadura mínima NBR 6118 Tab. 17.3 |
| As_adotada | cm² | Armadura adotada (≥ As_calc e ≥ As_min) |
| x | cm | Posição da linha neutra |
| phi | — | Coeficiente de segurança atingido |

## Limitações

- Válido apenas para flexão simples (sem esforço normal)
- Não cobre seções T nem seção dupla armada (skills separadas)
- Fck entre 20 e 90 MPa

## Casos de Uso

1. Viga simplesmente apoiada sob carga distribuída
2. Viga contínua na seção de momento máximo positivo
3. Pré-dimensionamento rápido
```
