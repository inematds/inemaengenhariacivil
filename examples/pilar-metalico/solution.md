> **Gerado pela engine `lib.service.solve_compression`** (W250x22,3, KL = 300 cm,
> fy = 250 MPa). Memorial determinístico — toda a aritmética vem do núcleo Python
> `lib/steel/stability.py`, validado por `lib/validators/steel_check.py`.

# Memorial de Cálculo — Barra Comprimida de Aço (flambagem por flexão)

**Norma:** NBR 8800:2008  
**Elemento:** Perfil laminado comprimido — flambagem global por flexão (ELU)

## 1. Dados de entrada

| Parâmetro | Valor |
|-----------|-------|
| Perfil | W250x22,3 |
| Comprimento de flambagem KL | 300 cm |
| Resistência ao escoamento fy | 250 MPa |
| Módulo de elasticidade E | 200000 MPa |
| Coeficiente de flambagem local Q | 1.00 |
| Área da seção A | 28.40 cm² |
| Inércia no eixo de flambagem Iy | 122.0 cm⁴ |

## 2. Flambagem elástica e esbeltez reduzida

- Carga de flambagem de Euler: Ne = π²·E·Iy/(KL)² = 267.58 kN
- Esbeltez reduzida: λ0 = √(Q·A·fy/Ne) = 1.6289
- Fator de redução por flambagem: χ = 0.3305

## 3. Força axial resistente de cálculo

- Coeficiente de ponderação: γa1 = 1.10
- **Nc,Rd = χ·Q·A·fy/γa1 = 213.33 kN**

## 4. Validação automática

| Verificação | Status | Detalhe |
|-------------|--------|---------|
| units | ✓ | Ne=267.6 kN (dimensional ✓) |
| physical | ✓ | fy=ok; lambda0=ok; resistencias=ok |
| normative | ✓ | chi_faixa=ok; NcRd_consistencia=ok |

**Resultado da validação:** APROVADO

---

⚠️ RESPONSABILIDADE TÉCNICA

Este cálculo é uma ferramenta de suporte à decisão de engenharia. A responsabilidade técnica e legal é exclusiva do engenheiro responsável pelo projeto, formalizada via ART (Anotação de Responsabilidade Técnica), conforme a Lei 6.496/77, a Lei 5.194/66 e a Resolução CONFEA/CREA vigente.
