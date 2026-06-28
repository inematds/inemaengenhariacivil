> **Nota de escopo (gerado pela engine `lib.service.solve_rectangular_column`).**
> O caso **literal** do README (20×50 cm, engastado-livre, L = 4,0 m ⇒
> le = 2·L = 8,0 m; no eixo fraco b = 20 cm ⇒ i = 5,77 cm ⇒ **λ ≈ 139**) está
> **FORA do método simplificado** (pilar-padrão + curvatura aproximada vale só para
> λ ≤ 90, NBR 6118 15.8.3.1). A engine **recusa** essa entrada (`ValueError`) —
> princípio da abstenção: λ > 90 exige método mais refinado (item 15.8.3.2).
>
> Para gerar um exemplo **em escopo**, analisa-se o **eixo de menor inércia**
> (b = 20 cm) com o pilar **contraventado** nessa direção, de modo que
> le = L = 4,0 m ⇒ **λ ≈ 69** (classe *médio*, com efeitos de 2ª ordem).
>
> Conversão dos valores de *cálculo* do README para *característicos* (÷ γf = 1,4):
> Nd = 800 → Nk = 571,4 kN; Md1 = 40 → Mk = 28,57 kN·m. Como a flexão é em torno
> do eixo de menor inércia, a dimensão da direção analisada entra como **h = 20 cm**
> (e b = 50 cm é a dimensão perpendicular).

# Memorial de Cálculo — Pilar de Concreto Armado

**Norma:** NBR 6118:2014  
**Elemento:** Pilar retangular — flexão composta normal com 2ª ordem (ELU)

## 1. Dados de entrada

| Parâmetro | Valor |
|-----------|-------|
| Seção (b × h) | 50 × 20 cm |
| Comprimento de flambagem le | 400 cm |
| Concreto | C30 (fck = 30 MPa) |
| Aço | CA-50 (fyk = 500 MPa) |
| Distância d' (eixo da armadura) | 4.5 cm |
| Carga normal característica Nk | 571.40 kN |
| Momento de topo característico Mk | 28.57 kN·m |

## 2. Esforços de cálculo

- Força normal: Nd = γf·Nk = **799.96 kN**
- Momento de 1ª ordem: M1d,A = γf·Mk = 40.00 kN·m
- fcd = fck/1,4 = 21.43 MPa · fyd = fyk/1,15 = 434.78 MPa

## 3. Esbeltez (NBR 6118 15.8.2)

- Raio de giração: i = 5.77 cm
- **Índice de esbeltez: λ = le/i = 69.3**
- Esbeltez-limite: λ1 = 35.0
- Classificação: **medio**

## 4. Efeitos de 2ª ordem (pilar-padrão, curvatura aproximada)

- Força normal adimensional: ν = 0.373
- Curvatura: 1/r = 0.02500 1/m
- Momento de 2ª ordem: M2d = 32.00 kN·m
- Momento mínimo: M1d,mín = 16.80 kN·m
- **Momento total de cálculo: Md,tot = 72.00 kN·m**

## 5. Armadura longitudinal (simétrica)

- As,cálculo = 13.00 cm²
- As,mín = 4.00 cm² · As,máx = 80.00 cm²
- **As,adotada = 13.00 cm²** (governado por: ELU)
- Detalhamento: **17 Ø 10.0 mm (As,ef = 13.35 cm²)**

## 6. Validação automática

| Verificação | Status | Detalhe |
|-------------|--------|---------|
| units | ✓ | ν=0.373 (dimensional ✓) |
| physical | ✓ | materiais=ok; geometria=ok; As_positivo=ok; nu=ok; esbeltez=ok |
| normative | ✓ | As_min=ok; As_max=ok; emenda=ok; esbeltez=ok |
| capacidade | ✓ | MRd=72.0 ≥ Md,tot=72.0 kN·m (N=Nd) |

**Resultado da validação:** APROVADO

---

⚠️ RESPONSABILIDADE TÉCNICA

Este cálculo é uma ferramenta de suporte à decisão de engenharia. A responsabilidade técnica e legal é exclusiva do engenheiro responsável pelo projeto, formalizada via ART (Anotação de Responsabilidade Técnica), conforme a Lei 6.496/77, a Lei 5.194/66 e a Resolução CONFEA/CREA vigente.
