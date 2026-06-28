# INEMA Engenharia Civil — Plataforma de Agentes de IA

Plataforma de **agentes de IA para cálculos de engenharia civil**, construída sobre
Claude Code. O agente conversa em linguagem natural, interpreta o problema, escolhe o
método normativo e **delega toda a aritmética a uma engine determinística em Python** —
que valida o resultado e gera o memorial de cálculo com o devido aviso de
responsabilidade técnica.

> **Estado:** `v1.0.0` — Fases 1 a 6 concluídas · **359 testes** verdes (334 unitários +
> 25 E2E) · `ruff` limpo · `--selftest` do MCP server OK · 18 domínios de cálculo.

---

## Índice

1. [O que é](#o-que-é)
2. [Princípio central](#princípio-central)
3. [Por que existe (escopo e limites)](#por-que-existe-escopo-e-limites)
4. [Arquitetura](#arquitetura)
5. [Domínios e cálculos](#domínios-e-cálculos)
6. [Início rápido](#início-rápido)
7. [Como usar](#como-usar)
8. [Pipeline de validação](#pipeline-de-validação)
9. [Responsabilidade técnica](#responsabilidade-técnica)
10. [Estrutura do projeto](#estrutura-do-projeto)
11. [Agentes](#agentes)
12. [Testes e qualidade](#testes-e-qualidade)
13. [Como contribuir](#como-contribuir)
14. [Limitações](#limitações)
15. [Roadmap (fases)](#roadmap-fases)
16. [Referências normativas](#referências-normativas)
17. [Licença](#licença)

---

## O que é

Uma plataforma onde **engenheiros conversam com agentes de IA** para resolver cálculos de
engenharia civil — concreto armado, fundações, geotecnia, hidráulica, estruturas
metálicas, pavimentação, terraplenagem, taludes e orçamento. Cada cálculo entrega:

- o **resultado estruturado** (dados validados),
- um **relatório de validação** automática (4 verificações independentes),
- um **memorial de cálculo** em Markdown, passo a passo,
- o **aviso de responsabilidade técnica** obrigatório.

A IA cuida da parte que ela faz bem — **entender o problema, escolher o método, explicar
e documentar**. O número em si nunca sai do modelo de linguagem: sai do Python.

## Princípio central

> **LLMs não fazem contas. Python faz contas. LLMs orquestram, interpretam e documentam.**

Essa não é uma preferência estética — é a decisão de arquitetura que torna a plataforma
defensável. A literatura científica de ponta mostra que um LLM calculando "de cabeça"
é não-confiável (confiabilidade pode cair abaixo de 10% em problemas de engenharia
estrutural), enquanto **delegar o cálculo a uma ferramenta determinística** leva a
confiabilidade a mais de 99%. O racional completo está em
[`docs/13-avaliacao-viabilidade.md`](docs/13-avaliacao-viabilidade.md).

Consequências práticas, codificadas como regras invioláveis (ver [`CLAUDE.md`](CLAUDE.md)):

1. **Toda aritmética vai para Python via MCP** — o LLM nunca soma, multiplica ou interpola.
2. **Unidades são sempre verificadas com `pint`** antes de qualquer operação.
3. **Todo cálculo passa pela camada de validação** antes de ser apresentado.
4. **Abstenção:** se não existe ferramenta para o pedido, o agente **diz que não pode** —
   nunca inventa um número.
5. **Todo resultado carrega o aviso de responsabilidade técnica.**

## Por que existe (escopo e limites)

Esta plataforma é um **copiloto de apoio à engenharia — voltado a educação, pesquisa e
verificação cruzada.** Ela **não substitui**:

- o software de cálculo consagrado (TQS, Eberick/AltoQi, SAP2000, Robot);
- a responsabilidade técnica do engenheiro, formalizada via **ART**.

Onde ela agrega valor real:

- **Ensino e prototipagem** — interface em linguagem natural + memória de cálculo explicada.
- **Camada anti-erro-humano** — checagem de unidades, seleção de fórmula e consulta a normas.
- **Verificação cruzada** de resultados de outro software.

O posicionamento honesto e suas razões (mercado, academia, profissão no Brasil) estão em
[`docs/13-avaliacao-viabilidade.md`](docs/13-avaliacao-viabilidade.md).

## Arquitetura

Quatro camadas, com responsabilidades separadas:

```
┌──────────────────────────────────────────────────────────────┐
│  USUÁRIO / ENGENHEIRO  — linguagem natural                    │
└───────────────────────────┬──────────────────────────────────┘
                            │
┌───────────────────────────▼──────────────────────────────────┐
│  AGENTES (Claude Code / SKILL.md)                             │
│  orchestrator → especialista (concrete, foundations, steel…)  │
│  interpreta · escolhe método · explica · NUNCA calcula        │
└───────────────────────────┬──────────────────────────────────┘
                            │  chama ferramenta MCP
┌───────────────────────────▼──────────────────────────────────┐
│  MCP SERVER  (mcp/calc-server/server.py)                      │
│  ferramentas finas → orquestradores solve_* (lib/service.py)  │
└───────────────────────────┬──────────────────────────────────┘
                            │
┌───────────────────────────▼──────────────────────────────────┐
│  ENGINE PYTHON (determinística)                               │
│  cálculo (lib/<domínio>) → VALIDAÇÃO (lib/validators)         │
│                          → MEMORIAL (lib/reporting)           │
│  unidades pint · modelos Pydantic · aviso de responsabilidade │
└──────────────────────────────────────────────────────────────┘
```

**Fluxo de um cálculo:** o agente interpreta o enunciado → chama a ferramenta MCP →
`solve_*` roda o cálculo no núcleo Python → a validação obrigatória verifica unidades,
física, norma e equilíbrio → o memorial é gerado com o disclaimer → o agente explica cada
etapa e só apresenta como solução final se a validação aprovou.

Detalhes em [`docs/01-arquitetura.md`](docs/01-arquitetura.md).

## Domínios e cálculos

18 cálculos, cada um com um orquestrador `solve_*` (a fronteira testável em
`lib/service.py`) e uma ferramenta MCP correspondente. Resumo por domínio:

| Domínio | Cálculos | Normas / métodos |
|---|---|---|
| **Concreto armado** | viga (flexão), pilar (2ª ordem), sapata isolada, laje 1 e 2 direções | NBR 6118:2014, NBR 6122 |
| **Geotecnia / fundações** | capacidade de carga, recalque (elástico/adensamento), empuxo (Rankine/Coulomb), estaca por SPT | Vesic, Terzaghi, Aoki-Velloso × Décourt-Quaresma |
| **Hidráulica / saneamento** | conduto forçado, canal aberto, perda de carga | Hazen-Williams, Darcy-Weisbach, Manning |
| **Estruturas metálicas** | barra comprimida, ligação parafusada, solda de filete | NBR 8800:2008 |
| **Pavimentação / terra / taludes** | pavimento flexível, balanço corte/aterro, talude (infinito/Fellenius) | DNER/DNIT, NBR 11682 |
| **Orçamento** | custo direto + BDI | base tipo SINAPI (amostra) |
| **Suporte** | cargas, combinações, consulta/interpolação de norma, memória de projeto, relatório | NBR 6120, NBR 8681 |

➡️ **Lista exaustiva** (com cada `solve_*`, ferramenta MCP e norma): consulte o
[**Catálogo de Cálculos** — `docs/14-catalogo-calculos.md`](docs/14-catalogo-calculos.md).
A fonte de verdade que o agente consulta em tempo de execução é a ferramenta MCP
`listar_capacidades`.

## Início rápido

Pré-requisito: [`uv`](https://docs.astral.sh/uv/) (gerenciador de pacotes Python).

```bash
# 1. Instalar dependências (inclui as de desenvolvimento: pytest, ruff)
uv sync --extra dev

# 2. Rodar a suíte de testes
uv run pytest -q                       # 359 testes

# 3. Conferir a engine ponta a ponta (sem subir o servidor)
uv run python mcp/calc-server/server.py --selftest   # -> SELFTEST OK

# 4. Iniciar o MCP server de cálculos (stdio)
uv run python mcp/calc-server/server.py

# 5. Abrir o Claude Code neste diretório
claude
```

## Como usar

### a) Via Claude Code (linguagem natural)

Com o MCP server conectado, peça em português:

> *"Dimensione uma viga 25×50 cm de concreto C30, vão 5 m, carga permanente 10 kN/m e
> variável 10 kN/m."*

O agente `orchestrator` roteia para o agente `concrete`, que chama a ferramenta MCP
`dimensionar_viga_retangular`, e devolve o memorial completo (esforços, x/d, armadura,
detalhamento), a validação e o aviso de responsabilidade.

### b) Via Python (a engine direto)

Todo cálculo é uma função `solve_*` em `lib/service.py` que devolve o **bundle padrão**:

```python
from lib.service import solve_rectangular_beam

bundle = solve_rectangular_beam(
    b_cm=25, h_cm=50, fck_mpa=30, fyk_mpa=500,
    vao_m=5.0, g_knm=10, q_knm=10,
)

bundle["aprovado"]               # True  (== bundle["validacao"]["passed"])
bundle["resultado"]["as_adopted_cm2"]   # área de aço adotada
print(bundle["memorial_markdown"])      # memorial completo, em Markdown
```

O **contrato comum** de todo `solve_*`:

```python
{
  "resultado":         { ... },        # model_dump() do resultado Pydantic
  "validacao":         { "passed": bool, "checks": [...], "warnings": [...] },
  "memorial_markdown": "# Memorial — ... (termina com o aviso de responsabilidade)",
  "aviso":             "⚠️ RESPONSABILIDADE TÉCNICA ... Lei 6.496/77 ...",
  "aprovado":          bool,           # == validacao.passed
}
```

Quando `aprovado` é `False`, o resultado **não** deve ser apresentado como solução final:
o agente aponta o que reprovou (em `validacao.checks`) e orienta o ajuste.

### c) Exemplos prontos

A pasta [`examples/`](examples/) traz casos resolvidos pela própria engine (cada um com
`README.md` do problema + `solution.md` gerado): `viga-simples`, `pilar-esbelto`,
`sapata-isolada`, `muro-arrimo`, `estaca-spt`, `rede-agua`, `pilar-metalico`,
`ligacao-parafusada`, `pavimento-flexivel`, `terraplenagem`, `talude`, `orcamento-viga`.

## Pipeline de validação

**Nenhum resultado é apresentado sem passar pela validação** (`lib/validators/`, sem LLM):

1. **Unidades** — consistência dimensional recomputada com `pint`.
2. **Física** — faixas razoáveis (ex.: `fck ∈ [10, 100] MPa`, `x/d ≤ 0,628`, `σ_solo` plausível).
3. **Normativa** — limites prescritos (ex.: `As ≥ As,mín`, `As ≤ As,máx`, ductilidade, FS).
4. **Equilíbrio** — somatório de forças/momentos (ex.: `Rcc ≈ Rst` na seção).

Cada verificação devolve `ok` / `warning` / `fail`; um único `fail` reprova o cálculo.
Detalhes em [`docs/08-validacao-calculos.md`](docs/08-validacao-calculos.md).

## Responsabilidade técnica

Todo memorial termina com o aviso obrigatório:

> ⚠️ **RESPONSABILIDADE TÉCNICA** — Este cálculo é uma ferramenta de suporte à decisão de
> engenharia. A responsabilidade técnica e legal é exclusiva do engenheiro responsável
> pelo projeto, formalizada via ART (Anotação de Responsabilidade Técnica), conforme a
> **Lei 6.496/77**, a **Lei 5.194/66** e a Resolução CONFEA/CREA vigente.

No Brasil a responsabilidade é sempre de um profissional habilitado e nomeado via **ART** —
nunca de um software. O disclaimer **não transfere nem reduz** essa responsabilidade; só
explicita o que a lei já determina.

## Estrutura do projeto

```
inemaengenhariacivil/
├── lib/                       # engine de cálculo (Python determinístico)
│   ├── units/registry.py      # registry pint compartilhado + verificação dimensional
│   ├── concrete/              # beams, columns, slabs, footings
│   ├── structural/            # loads (NBR 6120), combinations (NBR 8681)
│   ├── geotechnical/          # bearing_capacity, settlement, earth_pressure, piles, slope_stability
│   ├── hydraulic/             # pipe_flow, open_channel, head_loss
│   ├── steel/                 # profiles, stability, connections (NBR 8800)
│   ├── pavement/ · earthwork/ # pavimento flexível · volumes/terraplenagem
│   ├── budget/                # base SINAPI (amostra) + montagem com BDI
│   ├── projects/store.py      # memória por projeto (JSON)
│   ├── norms/search.py        # busca léxica em tabelas de norma
│   ├── math/interpolation.py  # interpolação de tabelas (sem extrapolar)
│   ├── validators/            # pipeline de validação (units/física/norma/equilíbrio)
│   ├── reporting/             # disclaimer, memorial, relatório, export Excel/PDF
│   └── service.py             # orquestradores solve_* (fronteira testável)
├── mcp/calc-server/server.py  # MCP server (ferramentas finas) + --selftest
├── agents/                    # SKILL.md por agente (orchestrator + domínios)
├── normas/                    # NBR 6118/6120/6122/7190/8800 (READMEs + tabelas JSON)
├── data/sinapi_amostra.csv    # base de preços ILUSTRATIVA
├── docs/                      # arquitetura, validação, fases, catálogo, viabilidade…
├── examples/                  # casos resolvidos pela engine (README + solution.md)
├── templates/ · checklists/ · workflows/
└── tests/                     # unit/ (núcleos) + integration/ (E2E por domínio)
```

## Agentes

Os agentes vivem em `agents/<nome>/SKILL.md` (prompt + frontmatter). O **`orchestrator`** é
o ponto de entrada: lê o pedido, identifica o domínio e roteia para o especialista.
Especialistas: `concrete`, `foundations`, `loads`, `review`, `retaining-walls`,
`water-supply`, `sewage`, `steel`, `norms`, `budget`, `report`, `pavement`, `earthwork`,
`slope-stability`. Todos seguem o mesmo contrato: **interpretar, chamar a ferramenta MCP,
explicar, validar e nunca inventar número**. Como criar um agente:
[`docs/10-como-adicionar-agente.md`](docs/10-como-adicionar-agente.md).

## Testes e qualidade

```bash
uv run pytest -q                                  # 359 testes (unit + E2E)
uv run ruff check lib mcp tests                   # lint
uv run python mcp/calc-server/server.py --selftest  # smoke da engine ponta a ponta
```

- **TDD** em todo o código: cada função nasceu de um teste que falhou primeiro, com o
  valor de referência **calculado à mão** no comentário e a cláusula normativa citada.
- **`tests/unit/`** cobre cada núcleo de cálculo e validador; **`tests/integration/`** roda
  a pilha completa (`solve_*` → validação → memorial) para um caso aprovado de cada domínio
  e o ciclo de memória de projeto.

## Como contribuir

Adicionar um cálculo é uma **fatia vertical**: núcleo Pydantic + validador + memorial +
`solve_*` no service + ferramenta MCP + `SKILL.md` do agente — **tudo com TDD**. O passo a
passo está em [`CONTRIBUTING.md`](CONTRIBUTING.md) e
[`docs/11-como-adicionar-skill.md`](docs/11-como-adicionar-skill.md).

## Limitações

A engine usa **métodos consagrados, porém simplificados e documentados**. Hoje ficam
**fora de escopo** (o agente se abstém):

- concreto **protendido**, **madeira** (NBR 7190), **alvenaria estrutural**;
- pilar com `λ > 90`, armadura dupla de viga, cisalhamento/flecha (ELS) de viga;
- lajes com engaste (só apoios simples), flambagem local de aço (`Q ≠ 1`), FLT;
- estabilidade de talude por **Bishop/Morgenstern-Price** (só infinito e Fellenius);
- pavimento **rígido**/mecanístico; dinâmica/sísmica.

Os preços da base SINAPI são **amostra ilustrativa** (`data/sinapi_amostra.csv`) e devem
ser substituídos pela tabela vigente/regional. A busca em normas é **léxica**, não semântica.

## Roadmap (fases)

Todas as fases do plano ([`docs/06-fases-implementacao.md`](docs/06-fases-implementacao.md))
estão **concluídas**:

| Versão | Fase | Entrega |
|---|---|---|
| v0.1.0 | 1 — Fundação | viga de concreto + validação + MCP |
| v0.2.0 | 2 — Estrutural | pilares, lajes, sapatas, cargas, combinações, exports |
| v0.3.0 | 3 — Geo + Hidro | capacidade/recalque/empuxo/estacas + condutos/canal/perdas |
| v0.4.0 | 4 — Orçamento + Docs | SINAPI + BDI, memória de projeto, relatório |
| v0.5.0 | 5 — Normas + Metálicas | NBR 8800, consulta normativa, interpolação |
| **v1.0.0** | 6 — Polimento | pavimento/terra/taludes + E2E + docs completas |

## Referências normativas

NBR 6118:2014 (concreto), NBR 6120:2019 (ações), NBR 6122 (fundações), NBR 7190 (madeira —
estrutura prevista), NBR 8800:2008 (aço), NBR 8681 (combinações), NBR 11682 (taludes),
DNER/DNIT (pavimentação). As tabelas usadas estão em `normas/<NORMA>/tables/*.json`.

## Licença

Uso interno INEMA Engenharia Civil.
