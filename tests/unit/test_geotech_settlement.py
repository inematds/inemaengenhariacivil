"""Testes de recalque — elástico imediato e adensamento primário.

Valores de referência calculados à mão (a conta está nos comentários).
Fontes:
  - Recalque elástico: teoria da elasticidade (Timoshenko/Boussinesq),
    s = q·B·(1−ν²)·Iw / Es.
  - Adensamento primário (Terzaghi): s = Cc/(1+e0)·H·log10((σ0+Δσ)/σ0).
"""

import pytest

from lib.geotechnical.settlement import (
    ConsolidationSettlementResult,
    ElasticSettlementResult,
    consolidation_settlement,
    elastic_settlement,
)
from lib.validators.geotech_check import validate_settlement


def test_elastic_settlement():
    # q=200 kPa, B=2 m, ν=0.3, Iw=0.88, Es=20000 kPa (20 MPa)
    # s = 200·2·(1−0.09)·0.88 / 20000
    #   = 400·0.91·0.88 / 20000 = 320.32/20000 = 0.016016 m = 16.016 mm
    r = elastic_settlement(q_kpa=200.0, b_m=2.0, poisson_nu=0.3, iw=0.88, es_kpa=20000.0)
    assert isinstance(r, ElasticSettlementResult)
    assert r.settlement_m == pytest.approx(0.016016, abs=1e-5)
    assert r.settlement_mm == pytest.approx(16.016, abs=1e-2)


def test_consolidation_settlement():
    # Cc=0.3, e0=0.8, H=5 m, σ0=100 kPa, Δσ=50 kPa
    # s = 0.3/1.8·5·log10(150/100) = 0.166667·5·0.176091
    #   = 0.833333·0.176091 = 0.146743 m = 146.74 mm
    r = consolidation_settlement(cc=0.3, e0=0.8, h_m=5.0, sigma0_kpa=100.0,
                                 delta_sigma_kpa=50.0)
    assert isinstance(r, ConsolidationSettlementResult)
    assert r.settlement_m == pytest.approx(0.146743, abs=1e-5)
    assert r.settlement_mm == pytest.approx(146.74, abs=1e-2)


def test_consolidation_zero_added_stress_no_settlement():
    # Δσ=0 -> log10(1)=0 -> recalque nulo
    r = consolidation_settlement(cc=0.3, e0=0.8, h_m=5.0, sigma0_kpa=100.0,
                                 delta_sigma_kpa=0.0)
    assert r.settlement_m == pytest.approx(0.0, abs=1e-12)


def test_validate_settlement_elastic_and_consolidation():
    re = elastic_settlement(q_kpa=200.0, b_m=2.0, poisson_nu=0.3, iw=0.88, es_kpa=20000.0)
    rep_e = validate_settlement(re)
    assert rep_e.passed is True
    assert any(c.name == "units" and c.status == "ok" for c in rep_e.checks)

    # recalque de adensamento de 146.7 mm > 25 mm -> warning (mas passa)
    rc = consolidation_settlement(cc=0.3, e0=0.8, h_m=5.0, sigma0_kpa=100.0,
                                  delta_sigma_kpa=50.0)
    rep_c = validate_settlement(rc)
    assert rep_c.passed is True
    assert any("mm" in w for w in rep_c.warnings)


def test_elastic_settlement_rejects_invalid():
    with pytest.raises(ValueError):
        elastic_settlement(q_kpa=200.0, b_m=2.0, poisson_nu=0.7, iw=0.88, es_kpa=20000.0)  # ν>0.5
    with pytest.raises(ValueError):
        elastic_settlement(q_kpa=200.0, b_m=2.0, poisson_nu=0.3, iw=0.88, es_kpa=0.0)  # Es<=0
    with pytest.raises(ValueError):
        elastic_settlement(q_kpa=0.0, b_m=2.0, poisson_nu=0.3, iw=0.88, es_kpa=20000.0)  # q<=0


def test_consolidation_rejects_invalid():
    with pytest.raises(ValueError):
        consolidation_settlement(cc=0.3, e0=4.0, h_m=5.0, sigma0_kpa=100.0,
                                 delta_sigma_kpa=50.0)  # e0>3
    with pytest.raises(ValueError):
        consolidation_settlement(cc=-0.1, e0=0.8, h_m=5.0, sigma0_kpa=100.0,
                                 delta_sigma_kpa=50.0)  # Cc<=0
    with pytest.raises(ValueError):
        consolidation_settlement(cc=0.3, e0=0.8, h_m=5.0, sigma0_kpa=0.0,
                                 delta_sigma_kpa=50.0)  # σ0<=0
