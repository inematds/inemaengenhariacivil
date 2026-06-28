# Estratégia de Testes

## Três Camadas

### Camada 1 — Testes Unitários Python (gratuitos, < 5s)

**O que testam:** cada função de cálculo individualmente.

**Como:** resultado calculado vs. referência de livro-texto com tolerância numérica de 0.1%.

**Localização:** `tests/unit/`

```python
# Exemplo: tests/unit/test_concrete_beams.py
def test_beam_flexure_simple_case():
    """Viga retangular 20x40cm, C25, fyk500, Md=50kN·m — Fusco p.142"""
    result = design_rectangular_beam(
        fck_mpa=25.0,
        fyk_mpa=500.0,
        Md_kNm=50.0,
        b_cm=20.0,
        h_cm=40.0,
    )
    assert abs(result.As_calc_cm2 - 4.85) < 0.05  # tolerância 0.1%
    assert result.x_cm < result.d_cm * 0.45  # domínio 2/3 NBR 6118
```

**Fixtures de referência:** `tests/fixtures/`
- Resultados baseados em Fusco (2010), Montoya (2010), Chaves (2016)
- Arquivo JSON por caso: entrada + saída esperada + fonte bibliográfica

### Camada 2 — Testes de Integração Python (gratuitos, < 30s)

**O que testam:** fluxo completo via Python sem LLM.
Entrada estruturada → cálculo → validação → saída estruturada.

**Como:** pipeline completo mas sem chamar Claude.

```python
# Exemplo: tests/integration/test_footing_pipeline.py
def test_footing_full_pipeline():
    """Sapata isolada: entrada → cálculo → validação → saída"""
    input_data = FootingInput(Nd=800, Msdx=30, Msdy=0, sigma_solo=150)
    result = run_footing_pipeline(input_data)

    assert result.validation.passed
    assert result.excel_path.exists()
    assert result.memorial_path.exists()
```

### Camada 3 — Testes E2E com Claude (pagos, ~$0.20/run por teste)

**O que testam:** que o agente interpreta corretamente o problema e chama as ferramentas certas.

**Não testam:** os números (isso é responsabilidade das camadas 1 e 2).

**Como:** sessão real com `claude -p`, verifica ferramentas chamadas e estrutura da saída.

---

## Fixtures de Referência

Cada fixture em `tests/fixtures/` segue o formato:

```json
{
  "id": "concrete_beam_rectangular_001",
  "description": "Viga retangular sob flexão simples",
  "source": "Fusco, P.B. (2010). Técnica de armar as estruturas de concreto. p.142",
  "input": {
    "fck_mpa": 25.0,
    "fyk_mpa": 500.0,
    "Md_kNm": 50.0,
    "b_cm": 20.0,
    "h_cm": 40.0
  },
  "expected_output": {
    "As_calc_cm2": 4.85,
    "x_cm": 7.2,
    "domain": "2"
  },
  "tolerance_percent": 0.1
}
```

---

## Cobertura de Testes (meta)

| Módulo | Cobertura Mínima |
|--------|-----------------|
| `lib/concrete/` | 95% |
| `lib/geotechnical/` | 90% |
| `lib/hydraulic/` | 90% |
| `lib/validators/` | 100% |
| `lib/units/` | 100% |

---

## Rodando os Testes

```bash
# Testes unitários (rápidos)
pytest tests/unit/ -v

# Testes de integração
pytest tests/integration/ -v

# Todos os testes com cobertura
pytest --cov=lib --cov-report=term-missing

# Teste específico
pytest tests/unit/test_concrete_beams.py::test_beam_flexure_simple_case -v
```
