# Arquitetura da Plataforma

## Diagrama de Camadas

```
┌─────────────────────────────────────────────────────────┐
│                    USUÁRIO / ENGENHEIRO                  │
└─────────────────────────┬───────────────────────────────┘
                          │  linguagem natural
┌─────────────────────────▼───────────────────────────────┐
│              CAMADA DE AGENTES (Claude Code Skills)      │
│                                                          │
│  ┌──────────────┐   ┌──────────────┐                    │
│  │ orchestrator │──►│  especialista│                    │
│  └──────────────┘   └──────┬───────┘                    │
│                            │ interpreta + seleciona      │
└────────────────────────────┼────────────────────────────┘
                             │ chama ferramenta MCP
┌────────────────────────────▼────────────────────────────┐
│                   CAMADA MCP (Bridge)                    │
│                                                          │
│  ┌──────────────┐   ┌──────────────┐   ┌────────────┐  │
│  │  calc-server │   │ report-server│   │  fs-server │  │
│  └──────┬───────┘   └──────┬───────┘   └────────────┘  │
└─────────┼──────────────────┼─────────────────────────── ┘
          │ chama função     │ gera documento
┌─────────▼──────────────────▼────────────────────────────┐
│              ENGINE DE CÁLCULO (Python)                  │
│                                                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────┐  │
│  │ concrete │  │  steel   │  │   geo    │  │ hydro  │  │
│  └──────────┘  └──────────┘  └──────────┘  └────────┘  │
│                                                          │
│  ┌──────────────────────────────────────────────────┐   │
│  │              VALIDATOR (obrigatório)             │   │
│  │  units • physical • normative • equilibrium      │   │
│  └──────────────────────────────────────────────────┘   │
│                                                          │
│  ┌──────────────────────────────────────────────────┐   │
│  │              REPORTER                            │   │
│  │  memorial • excel • pdf • checklist              │   │
│  └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

## Fluxo Detalhado de um Cálculo

```
1. ENTRADA
   Usuário: "Dimensione uma viga T de concreto C30, vão 6m, carga 30kN/m"

2. ORQUESTRADOR
   → identifica domínio: concreto estrutural
   → roteia para agente: concrete

3. AGENTE CONCRETE
   → interpreta: viga de concreto armado, flexão simples
   → identifica norma: NBR 6118:2014
   → seleciona método: seção T, estado limite último
   → prepara parâmetros de entrada

4. MCP CALL → calc-server
   → ferramenta: calculate_beam_flexure
   → entrada: {fck: 30, vao: 6.0, carga: 30, tipo: "T"}

5. PYTHON ENGINE
   → lib/concrete/beams.py::design_t_beam()
   → calcula Md, escolhe armadura, verifica deflexão

6. VALIDATOR (automático)
   → check_units: kN·m ✓
   → check_physical: As > 0 ✓
   → check_normative: As_min < As < As_max ✓
   → check_equilibrium: equilíbrio de forças ✓

7. RESULTADO ESTRUTURADO
   → As_calculada: 8.5 cm²
   → escolha: 4 φ 16mm (As = 8.04 cm²) — verifica com ρ_min
   → detalhamento: cobrimento 3cm, estribos φ8c/20cm

8. AGENTE CONCRETE (continuação)
   → explica cada etapa do cálculo
   → mostra hipóteses adotadas
   → identifica limitações

9. REPORTER
   → gera memorial de cálculo (Markdown → PDF)
   → gera planilha de resultados (Excel)
   → gera checklist de revisão

10. SAÍDA
    → Memorial PDF + Excel + Checklist
    → Aviso de responsabilidade técnica obrigatório
```

## Princípios de Design

### Separação de responsabilidades
- Agentes: interpretação, seleção de método, explicação
- Python: toda aritmética e lógica de cálculo
- MCP: protocolo de comunicação entre as camadas
- Validator: verificações determinísticas, sem LLM

### Contrato de dados (Pydantic)
Todo input e output de função Python tem schema Pydantic:
- Garante que unidades estão presentes
- Impede parâmetros ausentes
- Gera documentação automática

### Segundo método de verificação
Para cálculos críticos, dois métodos independentes são executados.
Se divergência > 20%, o agente avisa o engenheiro para revisão manual.
