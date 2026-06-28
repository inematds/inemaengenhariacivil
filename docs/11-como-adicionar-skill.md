# Como Adicionar uma Nova Skill (cálculo)

Uma **skill** aqui é uma *capacidade de cálculo*: a fatia vertical completa que vai do
núcleo Python determinístico até a ferramenta MCP que o agente aciona. Toda skill nova
passa pelos mesmos seis estágios, **sempre por TDD** (o teste vem antes do código):

```
teste (hand-calc + norma)            ← escreva primeiro, veja falhar (RED)
  └─ núcleo  lib/<domínio>/<x>.py     ← aritmética + Pydantic + abstenção (ValueError)
       └─ validador lib/validators/<domínio>_check.py   ← unidades (pint) + física + norma
            └─ memorial lib/reporting/memorial.py        ← render_*  (embute o DISCLAIMER)
                 └─ orquestrador lib/service.py           ← solve_*  (devolve o bundle)
                      └─ ferramenta MCP mcp/calc-server/server.py  ← @mcp.tool() fino
```

Regras do projeto (de `CLAUDE.md`) que valem para **toda** skill:

1. **LLM nunca faz aritmética.** Todo número nasce no núcleo Python.
2. **Unidades verificadas com `pint`** antes de qualquer operação (no validador).
3. **Validação obrigatória** antes de apresentar (`lib/validators/`).
4. **Disclaimer obrigatório** em toda saída (vem do `reporting`, nunca redigido à mão).
5. **Abstenção:** fora da faixa de validade → levante `ValueError`/`KeyError`; nunca chute.

## Quando criar uma nova skill vs. expandir uma existente

- **Nova skill:** responsabilidade nova, entradas/saídas diferentes, norma/método próprios.
- **Expandir existente:** mesmo cálculo com um parâmetro a mais → estenda o núcleo e o
  teste correspondentes, sem criar arquivos novos.

---

## Passo a Passo (TDD)

### 1. Teste primeiro — com hand-calc citando a norma (RED)

Crie `tests/unit/test_<domínio>_<x>.py`. O caso de referência traz o cálculo manual no
comentário, **citando a norma/fonte e a página**, e uma tolerância numérica explícita
(padrão 0,1 %). Esse comentário é o que torna o teste auditável.

```python
# tests/unit/test_<domínio>_<x>.py
import pytest

from lib.<domínio>.<x> import design_<x>


def test_<x>_caso_referencia():
    """Hand-calc — NBR XXXX:AAAA §Y / <Autor (ano), p.NN>.

    Dados: ...; à mão: <fórmula> = <valor> <unidade>.
    """
    r = design_<x>(param_a=..., param_b=...)
    assert r.saida_principal == pytest.approx(<valor_esperado>, rel=1e-3)


def test_<x>_fora_de_faixa_abstem():
    # Entrada fisicamente inválida → abstenção (não inventa número).
    with pytest.raises(ValueError):
        design_<x>(param_a=<valor_invalido>, param_b=...)
```

Rode e **veja falhar** (`uv run pytest tests/unit/test_<domínio>_<x>.py -q`).

### 2. Núcleo — `lib/<domínio>/<x>.py` (faz o teste passar, GREEN)

A aritmética vive aqui, determinística e sem efeitos colaterais. Saída em um modelo
**Pydantic** (serializável). Constantes de faixa de validade no topo; fora delas,
**abstenha-se** com `ValueError`. **Não** insira o disclaimer aqui (entra na integração).

```python
# lib/<domínio>/<x>.py
"""<Cálculo> — <método>. Fonte: NBR XXXX:AAAA §Y."""
from __future__ import annotations

from pydantic import BaseModel

# faixas de validade (abstenção fora delas)
PARAM_A_MIN, PARAM_A_MAX = ..., ...


class <X>Result(BaseModel):
    """Resultado de <cálculo> (eco das entradas + derivados + metadados)."""
    param_a: float
    param_b: float
    saida_principal: float
    metodo: str = "<método / norma>"
    warnings: list[str] = []


def design_<x>(param_a: float, param_b: float) -> <X>Result:
    """Calcula <…> conforme NBR XXXX:AAAA §Y. Abstém-se fora da faixa física."""
    if not (PARAM_A_MIN <= param_a <= PARAM_A_MAX):
        raise ValueError(f"param_a={param_a} fora da faixa [{PARAM_A_MIN}, {PARAM_A_MAX}].")
    saida = ...  # fórmula da norma
    return <X>Result(param_a=param_a, param_b=param_b, saida_principal=saida)
```

### 3. Validador — `lib/validators/<domínio>_check.py`

Cada domínio tem seu validador, que devolve um `ValidationReport`
(`lib/validators/report.py`) montado com objetos `Check` (`ok`/`warning`/`fail`). O
validador faz três famílias de checagem:

- **unidades:** reconstrói a fórmula com `pint` (`Q_`, `ensure` de `lib.units.registry`)
  e confere que a grandeza fecha dimensionalmente;
- **física:** parâmetros dentro de faixas razoáveis;
- **normativa:** consistência interna e limites da norma (estes podem ser `warning`).

`passed` é verdadeiro quando **nenhuma** checagem é `fail` (um `warning` aprova, mas
sinaliza).

```python
# lib/validators/<domínio>_check.py
from lib.units.registry import Q_, ensure
from lib.validators.report import Check, ValidationReport
from lib.<domínio>.<x> import <X>Result

TOL = 1e-3


def validate_<x>(r: <X>Result) -> ValidationReport:
    # unidades: reconstrói saida_principal com pint e compara
    val = ensure(Q_(r.param_a, "<unidade_a>") * ..., "<unidade_saida>")
    ref = max(abs(r.saida_principal), 1.0)
    units = Check(name="units",
                  status="ok" if abs(val - r.saida_principal) <= TOL * ref else "fail",
                  detail=f"saida={val:.3f} (dimensional ✓)")

    checks = [units]
    checks.append(Check(name="param_a", status="ok" if PARAM_A_MIN <= r.param_a else "fail",
                        detail=f"param_a={r.param_a}"))
    passed = not any(c.status == "fail" for c in checks)
    warnings = [c.detail for c in checks if c.status == "warning"] + list(r.warnings)
    return ValidationReport(passed=passed, checks=checks, warnings=warnings)
```

### 4. Memorial — `lib/reporting/memorial.py`

Adicione `render_<x>_memorial(r, rep) -> str`. O memorial é Markdown legível (dados,
fórmula, resultado, validação) e **termina embutindo o `DISCLAIMER`** — é ele que carrega
a `RESPONSABILIDADE TÉCNICA` e a `Lei 6.496/77` exigidas em toda saída.

```python
# em lib/reporting/memorial.py
from lib.reporting.disclaimer import DISCLAIMER

def render_<x>_memorial(r, rep) -> str:
    linhas = [f"# Memorial — <Cálculo> ({r.metodo})", ""]
    linhas += [f"- saída principal: {r.saida_principal:.3f}", ""]
    # ... etapas e resultado da validação (rep) ...
    linhas += ["---", "", DISCLAIMER]
    return "\n".join(linhas)
```

### 5. Orquestrador — `solve_<x>` em `lib/service.py`

O `solve_*` costura núcleo → validação → memorial e devolve o **bundle padrão** via o
helper `_bundle(r, rep, memorial)` (5 chaves: `resultado`, `validacao`,
`memorial_markdown`, `aviso`, `aprovado`). É a fronteira testável; o MCP é só transporte.

```python
# em lib/service.py
from lib.<domínio>.<x> import design_<x>
from lib.validators.<domínio>_check import validate_<x>
from lib.reporting.memorial import render_<x>_memorial


def solve_<x>(param_a: float, param_b: float) -> dict:
    """Resolve <cálculo> e devolve o pacote completo (dados serializáveis)."""
    r = design_<x>(param_a=param_a, param_b=param_b)
    rep = validate_<x>(r)
    memorial = render_<x>_memorial(r, rep)
    return _bundle(r, rep, memorial)
```

### 6. Ferramenta MCP — `@mcp.tool()` em `mcp/calc-server/server.py`

A ferramenta é **fina**: tipa as entradas, chama `solve_<x>` e devolve o bundle. Nenhuma
lógica de cálculo aqui. Acrescente também a entrada em `listar_capacidades` (é a fonte de
verdade de "o que existe"; o que não está lá, o agente recusa).

```python
# em mcp/calc-server/server.py
@mcp.tool()
def <nome_da_ferramenta>(param_a: float, param_b: float) -> dict:
    """<Cálculo> conforme NBR XXXX:AAAA §Y. Abstém-se fora da faixa física."""
    return solve_<x>(param_a=param_a, param_b=param_b)
```

```python
# dentro de listar_capacidades(), na lista "calculos":
"<nome_da_ferramenta> — <cálculo>, <método/norma>",
```

### 7. Cobertura E2E e fixtures

- Acrescente o caso **aprovado** ao dicionário `_CASOS_APROVADOS` de
  `tests/integration/test_e2e_dominios.py` (entradas que passam na validação). A suíte
  já asserta as 5 chaves, `aprovado is True` e o aviso no memorial.
- Se o `--selftest` do server deve cobrir a skill, inclua um bundle dela em `_selftest()`.
- (Opcional, recomendado) Fixture de referência em `tests/fixtures/` com fonte, entrada e
  saída esperada, e um exemplo em `examples/<x>/`.

### 8. Portões verdes (rode antes de concluir)

```bash
uv run pytest -q
uv run ruff check lib mcp tests
uv run python mcp/calc-server/server.py --selftest    # → "SELFTEST OK"
```

---

## Checklist de Nova Skill

- [ ] Teste escrito **primeiro**, com hand-calc citando a norma e tolerância explícita
- [ ] Núcleo em `lib/<domínio>/<x>.py` com modelo Pydantic e abstenção (`ValueError`)
- [ ] Validador `validate_<x>` retornando `ValidationReport` (unidades `pint` + física + norma)
- [ ] `render_<x>_memorial` embutindo o `DISCLAIMER`
- [ ] `solve_<x>` em `lib/service.py` usando `_bundle` (5 chaves)
- [ ] Ferramenta `@mcp.tool()` fina + entrada em `listar_capacidades`
- [ ] Caso aprovado em `tests/integration/test_e2e_dominios.py`
- [ ] `pytest`, `ruff` e `--selftest` verdes
