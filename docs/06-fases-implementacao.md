# Plano de Implementação em Fases

> **Estado: CONCLUÍDO — v1.0.0.** As Fases 1 a 6 estão implementadas, testadas
> (suíte unitária + E2E verde) e documentadas. Os checkboxes abaixo registram as
> entregas concretizadas. Para a lista operacional de cálculos disponíveis, ver
> [`14-catalogo-calculos.md`](14-catalogo-calculos.md); para contribuir com novos
> cálculos, ver [`../CONTRIBUTING.md`](../CONTRIBUTING.md).

## Fase 1 — Fundação (Semanas 1-2)

**Objetivo:** Sistema funcionando ponta a ponta para um caso simples.

### Entregas

- [x] Estrutura de diretórios criada
- [x] `lib/units/converter.py` com `pint` (verificação dimensional)
- [x] `lib/concrete/beams.py` — flexão simples (seção retangular)
- [x] `lib/validators/units_check.py`
- [x] `lib/validators/physical_check.py`
- [x] MCP server `calc-server` com 3 ferramentas básicas
- [x] Agente `concrete` com SKILL.md básico
- [x] Template de memorial de cálculo (`templates/memorial-calculo.md`)
- [x] Checklist de viga (`checklists/viga-concreto.json`)
- [x] Testes unitários: `tests/unit/test_concrete_beams.py`
- [x] Exemplo completo: `examples/viga-simples/`

### Critério de Conclusão

Usuário digita: *"Dimensione uma viga 25x50cm de concreto C30, vão 5m, carga 20kN/m"*

Sistema entrega:
1. Cálculo completo com todas as etapas explicadas
2. Memorial de cálculo em Markdown
3. Checklist de revisão preenchido
4. Aviso de responsabilidade técnica

---

## Fase 2 — Estrutural Core (Semanas 3-5)

**Objetivo:** Cobertura completa de concreto armado e fundações.

### Entregas

- [x] `lib/concrete/columns.py` — pilares com flambagem
- [x] `lib/concrete/slabs.py` — lajes (maciça, nervurada)
- [x] `lib/concrete/footings.py` — sapatas isoladas
- [x] `lib/structural/loads.py` — cargas NBR 6120
- [x] `lib/structural/combinations.py` — combinações NBR 6118 6.3
- [x] `lib/reporting/excel_export.py`
- [x] `lib/reporting/pdf_export.py`
- [x] Agentes: `foundations`, `loads`
- [x] Agente `review` para revisão cruzada
- [x] Testes de integração com fixtures de referência
- [x] Exemplos: `examples/pilar-esbelto/`, `examples/sapata-isolada/`

---

## Fase 3 — Geotecnia + Hidráulica (Semanas 6-8)

**Objetivo:** Fundações e redes prediais e urbanas.

### Entregas

- [x] `lib/geotechnical/bearing_capacity.py`
- [x] `lib/geotechnical/settlement.py`
- [x] `lib/geotechnical/earth_pressure.py` (Rankine, Coulomb)
- [x] `lib/geotechnical/piles.py` (Aoki-Velloso, Décourt-Quaresma)
- [x] `lib/hydraulic/pipe_flow.py` (Hazen-Williams, Darcy-Weisbach)
- [x] `lib/hydraulic/open_channel.py` (Manning)
- [x] `lib/hydraulic/head_loss.py`
- [x] Agentes: `retaining-walls`, `water-supply`, `sewage`
- [x] Normas JSON: `normas/NBR6122/tables/`
- [x] Workflow completo: `workflows/pile-foundation.md`

---

## Fase 4 — Orçamento + Documentação (Semanas 9-10)

**Objetivo:** Orçamentação e geração profissional de documentos.

### Entregas

- [x] Agente `budget` com integração SINAPI (CSV local)
- [x] `lib/reporting/memorial.py` — geração automática de memorial
- [x] Agente `report` com templates profissionais
- [x] Sistema de memória por projeto (`memory/projects/`)
- [x] Agente `orchestrator` completo
- [x] Workflow: `workflows/budget-estimate.md`
- [x] Templates: laudo pericial, relatório técnico

---

## Fase 5 — Normas + Metálicas (Semanas 11-12)

**Objetivo:** Estruturas metálicas e base de consulta normativa.

### Entregas

- [x] `lib/steel/profiles.py`, `connections.py`, `stability.py`
- [x] Base de tabelas NBR 8800 em JSON
- [x] Agentes: `steel`, `norms`
- [x] `lib/math/interpolation.py` para tabelas de norma
- [x] Agente `norms` com busca semântica em tabelas

---

## Fase 6 — Polimento e Estradas (Semanas 13-14)

**Objetivo:** Completude, qualidade e documentação final.

### Entregas

- [x] Agentes: `pavement`, `earthwork`, `slope-stability`
- [x] Suite completa de testes E2E
- [x] Documentação `docs/` completa
- [x] Guia de contribuição
- [x] Exemplos completos por domínio (um por agente)
- [x] `pytest` passando 100%

---

## Marcos de Versão

| Versão | Fase | Capacidade Principal | Status |
|--------|------|---------------------|--------|
| v0.1.0 | Fase 1 | Viga de concreto simples | ✅ concluída |
| v0.2.0 | Fase 2 | Concreto armado completo | ✅ concluída |
| v0.3.0 | Fase 3 | Geotecnia + Hidráulica | ✅ concluída |
| v0.4.0 | Fase 4 | Orçamento + Documentos | ✅ concluída |
| v0.5.0 | Fase 5 | Estruturas metálicas | ✅ concluída |
| v1.0.0 | Fase 6 | Plataforma completa | ✅ concluída |
