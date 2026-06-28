> **Nota de escopo (gerado pela engine `lib.service.solve_pile_comparison`).**
> Capacidade de carga de estaca por SPT, comparando Aoki-Velloso × Décourt-Quaresma
> (validação por 2º método; aviso se a divergência de Rult exceder 20%). Número de
> estacas, bloco de coroamento, recalque do grupo e prova de carga estão fora do
> escopo — princípio da abstenção.

# Memorial de Cálculo — Capacidade de Carga de Estaca (Aoki-Velloso × Décourt-Quaresma)

**Norma:** NBR 6122  
**Método:** dois métodos semiempíricos por SPT, com validação por divergência

## 1. Dados de entrada

| Parâmetro | Valor |
|-----------|-------|
| Tipo de estaca | pre-moldada |
| Diâmetro D | 0.30 m |
| Comprimento L | 10.00 m |
| Área de ponta Ap | 0.0707 m² |
| Perímetro U | 0.942 m |
| Fator de segurança global FS | 2.0 |
| Faixa de SPT do perfil | N ∈ [8, 20] |

## 2. Resistências por método

| Método | Rp (kN) | Rl (kN) | Rult (kN) | Radm (kN) |
|--------|---------|---------|-----------|-----------|
| Aoki-Velloso | 646.3 | 592.8 | 1239.1 | 619.6 |
| Décourt-Quaresma | 565.5 | 534.1 | 1099.6 | 549.8 |

## 3. Comparação entre métodos

- Rult (Aoki-Velloso) = 1239.1 kN
- Rult (Décourt-Quaresma) = 1099.6 kN
- **Divergência relativa = 11.3% (limite 20%)**
- Métodos convergem: sim

## 4. Validação automática

| Verificação | Status | Detalhe |
|-------------|--------|---------|
| Aoki/units | ✓ | Rp=646.3 kN (dimensional ✓) |
| Aoki/physical | ✓ | SPT=ok; geometria=ok; resistencias=ok |
| Aoki/normative | ✓ | Rult_consistencia=ok; FS_consistencia=ok; FS_minimo=ok |
| Décourt/units | ✓ | Rp=565.5 kN (dimensional ✓) |
| Décourt/physical | ✓ | SPT=ok; geometria=ok; resistencias=ok |
| Décourt/normative | ✓ | Rult_consistencia=ok; FS_consistencia=ok; FS_minimo=ok |
| convergencia | ✓ | divergência 11.3% (limite 20%) |

**Resultado da validação:** APROVADO

---

⚠️ RESPONSABILIDADE TÉCNICA

Este cálculo é uma ferramenta de suporte à decisão de engenharia. A responsabilidade técnica e legal é exclusiva do engenheiro responsável pelo projeto, formalizada via ART (Anotação de Responsabilidade Técnica), conforme a Lei 6.496/77, a Lei 5.194/66 e a Resolução CONFEA/CREA vigente.
