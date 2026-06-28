# Como Adicionar uma Nova Skill

## Quando Criar uma Nova Skill vs. Expandir Existente

**Nova skill:** responsabilidade nova, entradas/saídas diferentes.
**Expandir existente:** mesmo tipo de cálculo, parâmetro adicional.

## Passo a Passo

### 1. Criar o módulo Python

Em `lib/<domínio>/`:

```python
# lib/concrete/prestressed.py
from pydantic import BaseModel
import numpy as np
from lib.units.converter import ensure_consistent_units

class PrestressedBeamInput(BaseModel):
    fck_mpa: float          # resistência do concreto
    fpk_mpa: float          # resistência do cabo
    Md_kNm: float           # momento fletor de cálculo
    b_cm: float
    h_cm: float

class PrestressedBeamOutput(BaseModel):
    Ap_calc_cm2: float      # área de cabo calculada
    prestress_loss_pct: float
    validation: dict

def design_prestressed_beam(inp: PrestressedBeamInput) -> PrestressedBeamOutput:
    """
    Dimensionamento de viga protendida conforme NBR 6118:2014 §17.6
    """
    # TODO: implementar
    pass
```

### 2. Registrar ferramenta no MCP server

Em `mcp/calc-server/tools.py`:

```python
@server.tool()
async def calculate_prestressed_beam(
    fck_mpa: float,
    fpk_mpa: float,
    Md_kNm: float,
    b_cm: float,
    h_cm: float,
) -> dict:
    """Dimensiona viga protendida conforme NBR 6118."""
    from lib.concrete.prestressed import design_prestressed_beam, PrestressedBeamInput
    result = design_prestressed_beam(PrestressedBeamInput(
        fck_mpa=fck_mpa, fpk_mpa=fpk_mpa,
        Md_kNm=Md_kNm, b_cm=b_cm, h_cm=h_cm,
    ))
    return result.model_dump()
```

### 3. Criar testes unitários

```python
# tests/unit/test_prestressed_beam.py
def test_prestressed_beam_simple():
    """Viga protendida — referência: Pfeil (2002) p.215"""
    result = design_prestressed_beam(PrestressedBeamInput(
        fck_mpa=40, fpk_mpa=1860,
        Md_kNm=300, b_cm=25, h_cm=70
    ))
    assert abs(result.Ap_calc_cm2 - 8.2) < 0.1
```

### 4. Documentar

Criar `docs/skills/prestressed-beam.md` seguindo o template de `docs/04-skills.md`.

### 5. Adicionar fixture de referência

```json
{
  "id": "prestressed_beam_001",
  "source": "Pfeil, W. (2002). Concreto Protendido. p.215",
  "input": {},
  "expected_output": {}
}
```

## Checklist de Nova Skill

- [ ] Módulo Python criado com tipos Pydantic
- [ ] Ferramenta registrada no MCP server
- [ ] Verificação de unidades com `pint`
- [ ] Testes unitários com referência bibliográfica
- [ ] Tolerância numérica definida (padrão: 0.1%)
- [ ] Fixture de referência em `tests/fixtures/`
- [ ] Limitações documentadas na função
