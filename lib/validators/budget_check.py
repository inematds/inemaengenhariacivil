"""Validação obrigatória do domínio de ORÇAMENTO.

Arquivo próprio do domínio (não toca nos validadores compartilhados). Reverifica de
forma determinística a aritmética do orçamento antes de ele ser apresentado:
preços > 0, quantidades ≥ 0, BDI ∈ [0, 40] %, custo de cada item recomputado,
subtotal coerente com a soma dos itens e total = subtotal·(1 + BDI). Sem LLM.

Importa apenas ``Check``/``ValidationReport`` de :mod:`lib.validators.report` (estável).
"""

from __future__ import annotations

from lib.budget.estimate import BDI_MAX_PCT, BDI_MIN_PCT, OrcamentoResult
from lib.validators.report import Check, ValidationReport

TOL = 1e-6  # tolerância absoluta das reconstruções aritméticas


def _fold(name: str, subs: list[Check]) -> Check:
    """Resume uma lista de checagens em uma só (fail > warning > ok)."""
    status = "ok"
    for c in subs:
        if c.status == "fail":
            status = "fail"
            break
        if c.status == "warning":
            status = "warning"
    detail = "; ".join(f"{c.name}={c.status}" for c in subs)
    return Check(name=name, status=status, detail=detail)


def validate_orcamento(r: OrcamentoResult) -> ValidationReport:
    """Valida a coerência aritmética de um :class:`OrcamentoResult`.

    Recalcula custos, subtotal, valor do BDI e total e compara com os valores do
    resultado. Devolve um :class:`ValidationReport` (``passed=False`` se qualquer
    checagem falhar). Determinístico e independente do LLM.
    """
    # --- física: preços > 0, quantidades ≥ 0 -------------------------------
    phys: list[Check] = []
    precos_ok = all(it.preco_unitario > 0 for it in r.itens)
    phys.append(Check(
        name="precos_positivos",
        status="ok" if precos_ok else "fail",
        detail=("todos os preços unitários > 0" if precos_ok
                else "há preço unitário ≤ 0 (preço inválido)"),
    ))
    qtd_ok = all(it.quantidade >= 0 for it in r.itens)
    phys.append(Check(
        name="quantidades_nao_negativas",
        status="ok" if qtd_ok else "fail",
        detail=("todas as quantidades ≥ 0" if qtd_ok
                else "há quantidade negativa"),
    ))

    # --- normativa: BDI na faixa e aritmética coerente ---------------------
    norm: list[Check] = []
    bdi_ok = BDI_MIN_PCT - TOL <= r.bdi_pct <= BDI_MAX_PCT + TOL
    norm.append(Check(
        name="bdi_faixa",
        status="ok" if bdi_ok else "fail",
        detail=f"BDI={r.bdi_pct:.2f}% (faixa [{BDI_MIN_PCT:.0f}, {BDI_MAX_PCT:.0f}]%)",
    ))

    custos_ok = all(
        abs(it.custo - it.quantidade * it.preco_unitario) <= TOL * max(abs(it.custo), 1.0)
        for it in r.itens
    )
    norm.append(Check(
        name="custos_itens",
        status="ok" if custos_ok else "fail",
        detail=("custo = quantidade × preço em todos os itens" if custos_ok
                else "custo de item ≠ quantidade × preço unitário"),
    ))

    soma = sum(it.custo for it in r.itens)
    sub_ok = abs(soma - r.subtotal) <= TOL * max(abs(r.subtotal), 1.0)
    norm.append(Check(
        name="subtotal_coerente",
        status="ok" if sub_ok else "fail",
        detail=f"Σ custos={soma:.2f} ≈ subtotal={r.subtotal:.2f}",
    ))

    valor_bdi_calc = r.subtotal * (r.bdi_pct / 100.0)
    vbdi_ok = abs(valor_bdi_calc - r.valor_bdi) <= TOL * max(abs(r.valor_bdi), 1.0)
    norm.append(Check(
        name="valor_bdi_coerente",
        status="ok" if vbdi_ok else "fail",
        detail=f"subtotal·BDI={valor_bdi_calc:.2f} ≈ valor_bdi={r.valor_bdi:.2f}",
    ))

    total_calc = r.subtotal * (1.0 + r.bdi_pct / 100.0)
    tot_ok = abs(total_calc - r.total) <= TOL * max(abs(r.total), 1.0)
    norm.append(Check(
        name="total_coerente",
        status="ok" if tot_ok else "fail",
        detail=f"subtotal·(1+BDI)={total_calc:.2f} ≈ total={r.total:.2f}",
    ))

    checks = [_fold("physical", phys), _fold("normative", norm)]
    passed = not any(c.status == "fail" for c in checks)
    warnings = [c.detail for c in (phys + norm) if c.status == "warning"]
    warnings += list(r.warnings)
    return ValidationReport(passed=passed, checks=checks, warnings=warnings)
