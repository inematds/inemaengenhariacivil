"""Testes da camada de validação obrigatória dos cálculos."""

from lib.concrete.beams import design_rectangular_beam
from lib.concrete.columns import design_rectangular_column
from lib.concrete.footings import design_square_footing
from lib.concrete.slabs import design_one_way_slab, design_two_way_slab
from lib.validators.normative_check import check_normative_beam
from lib.validators.physical_check import check_physical_beam
from lib.validators.validate import (
    validate_beam,
    validate_column,
    validate_footing,
    validate_slab,
)


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


# ------------------------------------------------------------- sapata (footing)

def _good_footing():
    return design_square_footing(
        nk_kn=800.0, sigma_adm_kpa=300.0,
        pilar_a_cm=30.0, pilar_b_cm=30.0,
        fck_mpa=25.0, fyk_mpa=500.0,
    )


def test_validate_good_footing_passes_all_categories():
    rep = validate_footing(_good_footing())
    assert rep.passed is True
    names = {c.name for c in rep.checks}
    assert {"units", "physical", "normative"} <= names
    assert all(c.status != "fail" for c in rep.checks)


def test_validate_footing_flags_soil_overstress():
    bad = design_square_footing(
        nk_kn=1000.0, sigma_adm_kpa=200.0,
        pilar_a_cm=30.0, pilar_b_cm=30.0,
        fck_mpa=25.0, fyk_mpa=500.0,
    )
    rep = validate_footing(bad)
    assert rep.passed is False
    assert any(c.status == "fail" for c in rep.checks)


def test_validate_footing_flags_sigma_adm_out_of_range():
    # σ_adm fora da faixa física [50, 1000] kPa -> reprova
    r = _good_footing().model_copy(update={"sigma_adm_kpa": 20.0})
    rep = validate_footing(r)
    assert rep.passed is False


# ------------------------------------------------------------- pilar (column)

def _good_column():
    return design_rectangular_column(
        nk_kn=900.0, mk_topo_knm=27.0,
        b_cm=40.0, h_cm=30.0, le_cm=400.0,
        fck_mpa=25.0, fyk_mpa=500.0,
    )


def test_validate_good_column_passes_all_categories():
    rep = validate_column(_good_column())
    assert rep.passed is True
    names = {c.name for c in rep.checks}
    assert {"units", "physical", "normative", "capacidade"} <= names
    assert all(c.status != "fail" for c in rep.checks)


def test_validate_column_flags_below_as_min():
    r = _good_column().model_copy(update={"as_adopted_cm2": 0.10})
    rep = validate_column(r)
    assert rep.passed is False


def test_validate_column_flags_capacity_shortfall():
    # As insuficiente para o momento total -> capacidade < solicitação
    r = _good_column().model_copy(
        update={"as_adopted_cm2": 0.10, "as_min_cm2": 0.05})
    rep = validate_column(r)
    cap = next(c for c in rep.checks if c.name == "capacidade")
    assert cap.status == "fail"


# --------------------------------------------------------------- laje (slab)

def _good_one_way():
    return design_one_way_slab(lx_m=4.0, g_knm2=1.5, q_knm2=2.0, h_cm=10.0,
                               fck_mpa=25.0, fyk_mpa=500.0)


def _good_two_way():
    return design_two_way_slab(lx_m=4.0, ly_m=5.0, g_knm2=2.0, q_knm2=3.0, h_cm=12.0,
                               fck_mpa=25.0, fyk_mpa=500.0)


def test_validate_good_one_way_slab_passes():
    rep = validate_slab(_good_one_way())
    assert rep.passed is True
    names = {c.name for c in rep.checks}
    assert {"units", "physical", "normative"} <= names
    assert all(c.status != "fail" for c in rep.checks)


def test_validate_good_two_way_slab_passes():
    rep = validate_slab(_good_two_way())
    assert rep.passed is True
    assert all(c.status != "fail" for c in rep.checks)


def test_validate_slab_flags_below_as_min():
    r = _good_one_way().model_copy(update={"as_x_cm2_m": 0.05})
    rep = validate_slab(r)
    assert rep.passed is False
