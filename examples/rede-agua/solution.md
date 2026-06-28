> **Nota de escopo (gerado pela engine `lib.service.solve_pipe_flow`, método Hazen-Williams).**
> Perda de carga distribuída e velocidade em conduto forçado de água (seção plena).
> Bombeamento, linha piezométrica, golpe de aríete e redes malhadas estão fora do
> escopo — princípio da abstenção. Perdas localizadas somam-se à parte com `perda_de_carga`.

# Memorial de Cálculo — Escoamento em Conduto Forçado

**Método:** Hazen-Williams (SI)  
**Referência:** Azevedo Netto, *Manual de Hidráulica*, 8ª ed.

## 1. Dados de entrada

| Parâmetro | Valor |
|-----------|-------|
| Vazão Q | 0.0500 m³/s |
| Diâmetro D | 0.300 m |
| Comprimento L | 1000.0 m |
| Coeficiente de Hazen-Williams C | 130 |

## 2. Resultados

- Velocidade média: V = Q/A = 0.707 m/s
- **Perda de carga distribuída: hf = 1.778 m**

## 3. Validação automática

| Verificação | Status | Detalhe |
|-------------|--------|---------|
| units | ✓ | Q=0.0500 m³/s = A·V (dimensional ✓) |
| physical | ✓ | diametro=ok; comprimento=ok; perda_carga=ok; coef_C=ok |
| velocidade | ✓ | V=0.71 m/s (faixa 0.5–3.0) |

**Resultado da validação:** APROVADO

---

⚠️ RESPONSABILIDADE TÉCNICA

Este cálculo é uma ferramenta de suporte à decisão de engenharia. A responsabilidade técnica e legal é exclusiva do engenheiro responsável pelo projeto, formalizada via ART (Anotação de Responsabilidade Técnica), conforme a Lei 6.496/77, a Lei 5.194/66 e a Resolução CONFEA/CREA vigente.
