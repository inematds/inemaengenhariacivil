"""Testes da camada de validação obrigatória dos cálculos."""

from lib.concrete.beams import design_rectangular_beam
from lib.validators.normative_check import check_normative_beam
from lib.validators.physical_check import check_physical_beam
from lib.validators.validate import validate_beam


def _good_beam():
    return design_rectangular_beam(
        b_cm=25.0, h_cm=50.0, fck_mpa=30.0, fyk_mpa=500.0,
        vao_m=5.0, g_knm=10.0, q_knm=10.0,
    )


def test_validate_good_beam_passes_all_categories():
    rep = validate_beam(_good_beam())
    assert rep.passed is True
    names = {c.name for c in rep.checks}
    assert {"units", "physical", "normative", "equilibrium"} <= names
    assert all(c.status != "fail" for c in rep.checks)


def test_physical_check_flags_domain_4():
    # x/d > 0.628 (domínio 4, ruptura frágil) deve falhar
    r = _good_beam().model_copy(update={"x_over_d": 0.70})
    checks = check_physical_beam(r)
    assert any(c.status == "fail" for c in checks)


def test_normative_check_flags_below_as_min():
    r = _good_beam().model_copy(update={"as_adopted_cm2": 0.10})
    checks = check_normative_beam(r)
    assert any(c.status == "fail" for c in checks)


def test_equilibrium_holds_for_designed_section():
    rep = validate_beam(_good_beam())
    eq = next(c for c in rep.checks if c.name == "equilibrium")
    assert eq.status == "ok"
