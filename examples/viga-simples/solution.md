# Memorial de Cálculo — Viga de Concreto Armado

**Norma:** NBR 6118:2014  
**Elemento:** Viga retangular biapoiada — flexão simples (ELU)

## 1. Dados de entrada

| Parâmetro | Valor |
|-----------|-------|
| Seção (b × h) | 25 × 50 cm |
| Altura útil d | 45.7 cm |
| Concreto | C25 (fck = 25 MPa) |
| Aço | CA-50 (fyk = 500 MPa) |
| Vão | 5.00 m |
| Carga permanente g (excl. PP) | 10.00 kN/m |
| Carga variável q | 15.00 kN/m |

## 2. Esforços

- Peso próprio: pp = 3.125 kN/m
- Carga de cálculo: p_d = 1,4·(g + pp) + 1,4·q = 39.38 kN/m
- Momento de cálculo: **Md = p_d·L²/8 = 123.05 kN·m**

## 3. Materiais

- fcd = fck/1,4 = 17.86 MPa
- fyd = fyk/1,15 = 434.78 MPa

## 4. Flexão (estado-limite último)

- Linha neutra: x = 9.69 cm
- x/d = 0.212 (dúctil)
- Braço de alavanca: z = 41.82 cm

## 5. Armadura longitudinal

- As,cálculo = 6.77 cm²
- As,mín = 1.88 cm² · As,máx = 50.00 cm²
- **As,adotada = 6.77 cm²** (governado por: ELU)
- Detalhamento: **6 Ø 12.5 mm** (As,ef = 7.36 cm²)

## 6. Validação automática

| Verificação | Status | Detalhe |
|-------------|--------|---------|
| units | ✓ | Md=123.05 kN·m (dimensional ✓) |
| physical | ✓ | fck=ok; fyk=ok; geometria=ok; As_positivo=ok; dominio=ok |
| normative | ✓ | As_min=ok; As_max=ok; ductilidade=ok |
| equilibrium | ✓ | Rcc=294.2 kN ≈ Rst=294.2 kN (ΣF≈0) |

**Resultado da validação:** APROVADO

---

⚠️ RESPONSABILIDADE TÉCNICA

Este cálculo é uma ferramenta de suporte à decisão de engenharia. A responsabilidade técnica e legal é exclusiva do engenheiro responsável pelo projeto, formalizada via ART (Anotação de Responsabilidade Técnica), conforme a Lei 6.496/77, a Lei 5.194/66 e a Resolução CONFEA/CREA vigente.
