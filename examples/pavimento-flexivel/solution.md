> **Nota de escopo (gerado pela engine `lib.service.solve_flexible_pavement`).**
> Pavimento flexível pelo método empírico do DNER/DNIT (CBR do subleito × número N).
> Pavimento rígido, método mecanístico-empírico (MeDiNa), drenagem e expansão do
> subleito estão fora do escopo — princípio da abstenção.

# Memorial de Cálculo — Pavimento Flexível (DNER/DNIT)

**Método:** DNER/DNIT empírico (CBR / número N)  
**Referência:** DNER (1981) / DNIT (2006), Manual de Pavimentação

## 1. Dados de entrada

| Parâmetro | Valor |
|-----------|-------|
| CBR do subleito | 10.0% |
| Número N de tráfego | 1e+06 |
| Coeficiente K do revestimento | 2.0 |
| Coeficiente K da base | 1.0 |
| Coeficiente K da sub-base | 1.0 |

## 2. Espessuras de material granular equivalente exigidas

Ajuste do ábaco DNER: H = 77,67·N^0,0482·CBR^−0,598 (cm).

- Sobre o subleito (CBR = 10%): **Hm = 38.15 cm**
- Sobre a sub-base (CBR = 20%): H20 = 25.20 cm

## 3. Espessuras adotadas por camada

| Camada | Espessura (cm) |
|--------|----------------|
| Revestimento betuminoso R | 2.0 (mín. DNER 2.0) |
| Base B | 22.0 |
| Sub-base S | 15.0 |
| **Espessura total** | **39.0** |

## 4. Verificação das inequações de equivalência estrutural (DNER)

| Inequação | Σ esp.·K (cm) | H exigido (cm) | Atende |
|-----------|---------------|----------------|--------|
| sobre_subbase | 26.0 | 25.2 | ✓ |
| sobre_subleito | 41.0 | 38.1 | ✓ |

## 5. Validação automática

| Verificação | Status | Detalhe |
|-------------|--------|---------|
| units | ✓ | Hm=38.15 cm (reconstrução da equação DNER ✓) |
| physical | ✓ | cbr_subleito=ok; numero_N=ok; espessuras_minimas=ok; coeficientes_K=ok; soma_espessuras=ok |
| normative | ✓ | sobre_subbase=ok; sobre_subleito=ok; revestimento_minimo=ok |

**Resultado da validação:** APROVADO

---

⚠️ RESPONSABILIDADE TÉCNICA

Este cálculo é uma ferramenta de suporte à decisão de engenharia. A responsabilidade técnica e legal é exclusiva do engenheiro responsável pelo projeto, formalizada via ART (Anotação de Responsabilidade Técnica), conforme a Lei 6.496/77, a Lei 5.194/66 e a Resolução CONFEA/CREA vigente.
