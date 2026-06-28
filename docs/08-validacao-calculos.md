# Estratégia de Validação dos Cálculos

## Princípio

**Todo cálculo passa por no mínimo quatro verificações independentes antes de ser apresentado ao usuário.**

## Pipeline de Validação

```python
def validate_calculation(result: CalculationResult) -> ValidationReport:
    checks = [
        check_units(result),            # 1. Dimensional
        check_physical_bounds(result),  # 2. Física
        check_normative_limits(result), # 3. Normativa
        check_equilibrium(result),      # 4. Equilíbrio
    ]

    # Para cálculos críticos: segundo método
    if result.is_critical:
        alt_result = run_alternative_method(result.input)
        checks.append(compare_methods(result, alt_result))

    return ValidationReport(checks)
```

## Verificações Detalhadas

### 1. Verificação Dimensional (units_check.py)

Usa `pint` para garantir consistência dimensional.

```python
# Exemplo
Md = 50 * ureg.kilonewton * ureg.meter
b = 20 * ureg.centimeter
# Qualquer operação com unidades inconsistentes lança DimensionalityError
```

**Casos detectados:**
- kN/m² usado onde deveria ser kN/m³
- cm² retornado onde esperado cm
- Adimensional onde esperado unidade de força

### 2. Verificação Física (physical_check.py)

Limites físicos razoáveis para cada grandeza:

| Parâmetro | Mínimo | Máximo | Justificativa |
|-----------|--------|--------|---------------|
| fck | 10 MPa | 100 MPa | Concreto real |
| fyk | 250 MPa | 600 MPa | Aços comerciais |
| As | As_min | 8% b·h | NBR 6118 |
| x/d | 0 | 0.628 | Domínio 2/3 |
| σ_solo | 50 kPa | 1000 kPa | Solos comuns |

### 3. Verificação Normativa (normative_check.py)

Verifica limites prescritos nas normas:

```python
# NBR 6118 - armadura mínima de vigas
As_min = 0.0015 * b * d  # Tabela 17.3
assert As >= As_min, f"As={As:.2f} < As_min={As_min:.2f} (NBR 6118 Tab.17.3)"

# NBR 6118 - cobrimento mínimo
assert cobrimento >= cobrimento_min[classe_agressividade], "Cobrimento insuficiente"
```

### 4. Verificação de Equilíbrio (equilibrium_check.py)

Para estruturas: soma de forças e momentos = 0.

```python
# Verificação de equilíbrio de seção
soma_forcas = compressao_concreto + compressao_aco - tracao_aco
assert abs(soma_forcas) < 0.01 * Nd, "Equilíbrio de forças não satisfeito"
```

### 5. Comparação de Métodos (para cálculos críticos)

Para estacas: Aoki-Velloso vs Décourt-Quaresma.

```python
R_aoki = aoki_velloso(spt_data, pile_type, diameter)
R_decourt = decourt_quaresma(spt_data, pile_type, diameter)

divergence = abs(R_aoki - R_decourt) / max(R_aoki, R_decourt)
if divergence > 0.20:
    warn(f"Divergência de {divergence:.0%} entre métodos. Revisão recomendada.")
```

## Saída da Validação

```json
{
  "passed": true,
  "checks": [
    {"name": "units", "status": "ok", "detail": "kN·m ✓"},
    {"name": "physical", "status": "ok", "detail": "As=4.85cm² dentro dos limites"},
    {"name": "normative", "status": "ok", "detail": "As ≥ As_min=1.32cm² (NBR 6118 Tab.17.3)"},
    {"name": "equilibrium", "status": "ok", "detail": "ΣF = 0.003 kN ≈ 0 ✓"}
  ],
  "warnings": [],
  "method_comparison": null
}
```

## Aviso de Responsabilidade Técnica

**Obrigatório em TODA saída ao usuário:**

```
⚠️ RESPONSABILIDADE TÉCNICA

Este cálculo é uma ferramenta de suporte à decisão de engenharia.
A responsabilidade técnica e legal é exclusiva do engenheiro responsável
pelo projeto, conforme a Lei 5.194/66 e Resolução CONFEA/CREA vigente.

Hipóteses adotadas: [listadas acima]
Limitações: [listadas acima]
Norma de referência: [citada acima]
```
