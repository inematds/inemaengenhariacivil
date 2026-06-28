> **Nota de escopo (gerado pela engine `lib.service.solve_earth_pressure_rankine`).**
> Empuxo de terra ativo/passivo por Rankine, solo não coesivo, por metro de muro.
> Empuxo de água, sobrecargas, coesão e a estabilidade do muro (deslizamento,
> tombamento, capacidade da base) estão fora do escopo — princípio da abstenção.

# Memorial de Cálculo — Empuxo de Terra (Rankine)

**Norma:** NBR 11682 / Teoria de Rankine  
**Método:** Rankine — empuxo por metro de muro

## 1. Dados de entrada

| Parâmetro | Valor |
|-----------|-------|
| Peso específico γ | 18.0 kN/m³ |
| Altura do muro H | 4.00 m |
| Ângulo de atrito φ | 30.0° |

## 2. Coeficientes de empuxo

- Coeficiente ativo: Ka = 0.3333
- Coeficiente passivo: Kp = 3.0000

## 3. Empuxos (E = 0,5·γ·H²·K)

- **Empuxo ativo: Ea = 48.00 kN/m**
- Empuxo passivo: Ep = 432.00 kN/m
- Ponto de aplicação: z = H/3 = 1.333 m da base (distribuição triangular)

## 4. Validação automática

| Verificação | Status | Detalhe |
|-------------|--------|---------|
| units | ✓ | Ea=48.00 kN/m (dimensional ✓) |
| physical | ✓ | phi=ok; gamma=ok; coeficientes=ok |
| normative | ✓ | Ka_lt_Kp=ok; ponto_aplicacao=ok |

**Resultado da validação:** APROVADO

---

⚠️ RESPONSABILIDADE TÉCNICA

Este cálculo é uma ferramenta de suporte à decisão de engenharia. A responsabilidade técnica e legal é exclusiva do engenheiro responsável pelo projeto, formalizada via ART (Anotação de Responsabilidade Técnica), conforme a Lei 6.496/77, a Lei 5.194/66 e a Resolução CONFEA/CREA vigente.
