> **Nota de escopo (gerado pela engine `lib.service.solve_infinite_slope`).**
> Estabilidade de talude infinito (ruptura plana paralela à face), solo c-φ com
> poro-pressão informada. Bishop simplificado, Morgenstern-Price, busca da superfície
> crítica e taludes reforçados estão fora do escopo — princípio da abstenção.

# Memorial de Cálculo — Estabilidade de Talude Infinito

**Norma:** NBR 11682 / Das, Fundamentos de Engenharia Geotécnica  
**Método:** Talude infinito (Das)

## 1. Dados de entrada

| Parâmetro | Valor |
|-----------|-------|
| Coesão c | 10.0 kPa |
| Ângulo de atrito φ | 25.0° |
| Peso específico γ | 18.0 kN/m³ |
| Profundidade da ruptura z | 3.00 m |
| Inclinação do talude β | 20.0° |
| Poro-pressão na base u | 0.0 kPa |

## 2. Fator de segurança (FS = [c + (γ·z·cos²β − u)·tanφ] / (γ·z·sinβ·cosβ))

- Tensão resistente (numerador): 32.235 kPa
- Tensão atuante (denominador): 17.355 kPa
- **Fator de segurança: FS = 1.857**
- Classificação: **estável** (FS,mín usual ≥ 1.5, NBR 11682)

## 3. Validação automática

| Verificação | Status | Detalhe |
|-------------|--------|---------|
| units | ✓ | FS=1.857 (num/den em kPa, dimensional ✓) |
| physical | ✓ | phi=ok; gamma=ok; coesao=ok; geometria=ok; FS_positivo=ok |
| normative | ✓ | classificacao=ok; FS_minimo=ok |

**Resultado da validação:** APROVADO

---

⚠️ RESPONSABILIDADE TÉCNICA

Este cálculo é uma ferramenta de suporte à decisão de engenharia. A responsabilidade técnica e legal é exclusiva do engenheiro responsável pelo projeto, formalizada via ART (Anotação de Responsabilidade Técnica), conforme a Lei 6.496/77, a Lei 5.194/66 e a Resolução CONFEA/CREA vigente.
