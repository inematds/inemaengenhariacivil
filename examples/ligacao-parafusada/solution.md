> **Gerado pela engine `lib.service.solve_bolted_connection`** (força 200 kN, M20
> fub = 800 MPa, chapa t = 9,5 mm fu = 400 MPa). Memorial determinístico — toda a
> aritmética vem do núcleo `lib/steel/connections.py`, validado por
> `lib/validators/steel_connections_check.py`.

# Memorial de Cálculo — Ligação Parafusada (cortante)

**Norma:** NBR 8800:2008  
**Elemento:** Ligação por parafusos solicitada ao cortante (ELU)

## 1. Dados de entrada

| Parâmetro | Valor |
|-----------|-------|
| Força solicitante de cálculo | 200.00 kN |
| Diâmetro do parafuso db | 20 mm |
| Resistência à ruptura do parafuso fub | 800 MPa |
| Espessura da chapa t | 9.5 mm |
| Resistência à ruptura da chapa fu | 400 MPa |
| Número de planos de corte | 1 |
| Plano de corte na parte | rosqueada |
| Coeficiente de ponderação γa2 | 1.35 |

## 2. Resistência por parafuso

- Área bruta do parafuso: Ab = π·db²/4 = 3.142 cm²
- Cortante (§6.3.3.2): Fv,Rd = 74.47 kN
- Pressão de contato (§6.3.3.3, 2,4·db·t·fu/γa2): Fc,Rd = 135.11 kN
- **Resistência governante: Rd = 74.47 kN (cortante)**

## 3. Número de parafusos

- n = ⌈força/Rd⌉ = **3** parafuso(s)
- **Capacidade total da ligação: n·Rd = 223.40 kN**

## 4. Validação automática

| Verificação | Status | Detalhe |
|-------------|--------|---------|
| materiais_positivos | ✓ | fub=800 MPa, fu=400 MPa (devem ser > 0) |
| resistencias_positivas | ✓ | Fv,Rd=74.47 kN, Fc,Rd=135.11 kN (> 0) |
| governante_minimo | ✓ | Rd_parafuso=74.47 ≈ min(Fv,Rd, Fc,Rd)=74.47 kN (cortante) |
| numero_parafusos | ✓ | n=3 parafuso(s) (>= 1) |
| capacidade_total | ✓ | n·Rd=223.40 ≈ capacidade=223.40 kN e ≥ força=200.00 kN |
| bitola_usual | ✓ | db=20 mm (faixa usual [12.5, 25] mm) |

**Resultado da validação:** APROVADO

---

⚠️ RESPONSABILIDADE TÉCNICA

Este cálculo é uma ferramenta de suporte à decisão de engenharia. A responsabilidade técnica e legal é exclusiva do engenheiro responsável pelo projeto, formalizada via ART (Anotação de Responsabilidade Técnica), conforme a Lei 6.496/77, a Lei 5.194/66 e a Resolução CONFEA/CREA vigente.
