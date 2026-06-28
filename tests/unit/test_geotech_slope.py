"""Testes de estabilidade de taludes — talude infinito e Fellenius.

Valores de referência calculados à mão (a conta está nos comentários).
Fontes:
  - Talude infinito: Das, "Fundamentos de Engenharia Geotécnica".
  - Fellenius (1936): método ordinário das fatias, ruptura circular.

Âncora friccional pura (c=0, sem água): FS = tanφ/tanβ.
  φ=30°, β=20° -> FS = tan30/tan20 = 0.5773503/0.3639702 = 1.58631.
"""

import math

import pytest

from lib.geotechnical.slope_stability import (
    FelleniusResult,
    InfiniteSlopeResult,
    Slice,
    fellenius_fs,
    infinite_slope_fs,
)
from lib.validators.slope_check import validate_slope


# --- talude infinito --------------------------------------------------------
def test_infinite_slope_frictional_anchor():
    # c=0, u=0 -> FS = (γ·z·cos²β·tanφ)/(γ·z·sinβ·cosβ) = tanφ/tanβ
    # φ=30°, β=20° -> FS = tan30/tan20 = 1.58631 ; classificação "estável"
    r = infinite_slope_fs(c_kpa=0.0, phi_deg=30.0, gamma_kn_m3=18.0,
                          z_m=4.0, beta_deg=20.0)
    assert isinstance(r, InfiniteSlopeResult)
    expected = math.tan(math.radians(30.0)) / math.tan(math.radians(20.0))
    assert r.fs == pytest.approx(expected, abs=1e-6)
    assert r.fs == pytest.approx(1.58631, abs=1e-4)
    assert r.classification == "estável"


def test_infinite_slope_with_cohesion():
    # c=10, φ=25, γ=18, z=3, β=15, u=0
    # cos²15 = 0.9330127 ; γ·z·cos²β = 54·0.9330127 = 50.382686
    # num = 10 + 50.382686·tan25 = 10 + 50.382686·0.4663077 = 10 + 23.49383 = 33.49383
    # den = γ·z·sinβ·cosβ = 54·(0.5·sin30) = 54·0.25 = 13.5
    # FS = 33.49383/13.5 = 2.48103
    r = infinite_slope_fs(c_kpa=10.0, phi_deg=25.0, gamma_kn_m3=18.0,
                          z_m=3.0, beta_deg=15.0)
    assert r.resisting_kpa == pytest.approx(33.49383, abs=1e-3)
    assert r.driving_kpa == pytest.approx(13.5, abs=1e-6)
    assert r.fs == pytest.approx(2.48103, abs=1e-3)
    assert r.classification == "estável"


def test_infinite_slope_with_seepage_reduces_fs():
    # mesmo caso, agora com poro-pressão u=20 kPa
    # num = 10 + (50.382686 − 20)·tan25 = 10 + 30.382686·0.4663077 = 10 + 14.16769 = 24.16769
    # FS = 24.16769/13.5 = 1.79020 (< 2.48103 sem água)
    dry = infinite_slope_fs(c_kpa=10.0, phi_deg=25.0, gamma_kn_m3=18.0,
                            z_m=3.0, beta_deg=15.0)
    wet = infinite_slope_fs(c_kpa=10.0, phi_deg=25.0, gamma_kn_m3=18.0,
                            z_m=3.0, beta_deg=15.0, u_kpa=20.0)
    assert wet.fs == pytest.approx(1.79020, abs=1e-3)
    assert wet.fs < dry.fs
    assert wet.classification == "estável"


def test_infinite_slope_unstable_classification():
    # c=0, φ=20, β=30 -> FS = tan20/tan30 = 0.3639702/0.5773503 = 0.63035 (< 1)
    r = infinite_slope_fs(c_kpa=0.0, phi_deg=20.0, gamma_kn_m3=18.0,
                          z_m=4.0, beta_deg=30.0)
    assert r.fs == pytest.approx(0.63035, abs=1e-4)
    assert r.classification == "instável"


def test_infinite_slope_rejects_invalid():
    with pytest.raises(ValueError):
        infinite_slope_fs(c_kpa=0.0, phi_deg=55.0, gamma_kn_m3=18.0,
                          z_m=4.0, beta_deg=20.0)  # φ>50
    with pytest.raises(ValueError):
        infinite_slope_fs(c_kpa=0.0, phi_deg=30.0, gamma_kn_m3=5.0,
                          z_m=4.0, beta_deg=20.0)  # γ<10
    with pytest.raises(ValueError):
        infinite_slope_fs(c_kpa=0.0, phi_deg=30.0, gamma_kn_m3=18.0,
                          z_m=0.0, beta_deg=20.0)  # z<=0
    with pytest.raises(ValueError):
        infinite_slope_fs(c_kpa=0.0, phi_deg=30.0, gamma_kn_m3=18.0,
                          z_m=4.0, beta_deg=0.0)  # β fora de (0,90)
    with pytest.raises(ValueError):
        infinite_slope_fs(c_kpa=-1.0, phi_deg=30.0, gamma_kn_m3=18.0,
                          z_m=4.0, beta_deg=20.0)  # c<0


# --- Fellenius (método ordinário das fatias) --------------------------------
def test_slice_defaults():
    s = Slice(w_kn=100.0, alpha_deg=10.0, dl_m=2.0)
    assert s.u_kpa == 0.0


def test_fellenius_two_slices_frictional():
    # c=0, φ=30, sem água; FS = Σ(W·cosα·tanφ)/Σ(W·sinα)
    # res = tan30·(100·cos10 + 100·cos30) = 0.5773503·185.08332 = 106.85792
    # drv = 100·sin10 + 100·sin30 = 17.36482 + 50 = 67.36482
    # FS = 106.85792/67.36482 = 1.58626
    slices = [
        Slice(w_kn=100.0, alpha_deg=10.0, dl_m=2.0),
        Slice(w_kn=100.0, alpha_deg=30.0, dl_m=2.0),
    ]
    r = fellenius_fs(slices, c_kpa=0.0, phi_deg=30.0)
    assert isinstance(r, FelleniusResult)
    assert r.resisting_kn_m == pytest.approx(106.85792, abs=1e-3)
    assert r.driving_kn_m == pytest.approx(67.36482, abs=1e-3)
    assert r.fs == pytest.approx(1.58626, abs=1e-4)
    assert r.n_slices == 2
    assert r.classification == "estável"


def test_fellenius_three_slices_with_cohesion():
    # c=10, φ=20, sem água. tan20 = 0.3639702
    # S1 W=100 α=-10 ΔL=2.0: 10·2 + 100·cos10·tan20 = 20 + 35.84408 = 55.84408
    # S2 W=200 α=15  ΔL=2.2: 10·2.2 + 200·cos15·tan20 = 22 + 70.31366 = 92.31366
    # S3 W=150 α=35  ΔL=2.5: 10·2.5 + 150·cos35·tan20 = 25 + 44.72204 = 69.72204
    # res = 217.87978 ; drv = 100·sin(-10)+200·sin15+150·sin35 = -17.36482+51.7638+86.03646
    #     = 120.43544 ; FS = 217.87978/120.43544 = 1.80910
    slices = [
        Slice(w_kn=100.0, alpha_deg=-10.0, dl_m=2.0),
        Slice(w_kn=200.0, alpha_deg=15.0, dl_m=2.2),
        Slice(w_kn=150.0, alpha_deg=35.0, dl_m=2.5),
    ]
    r = fellenius_fs(slices, c_kpa=10.0, phi_deg=20.0)
    assert r.resisting_kn_m == pytest.approx(217.87978, abs=1e-2)
    assert r.driving_kn_m == pytest.approx(120.43544, abs=1e-3)
    assert r.fs == pytest.approx(1.80910, abs=1e-3)
    assert r.classification == "estável"


def test_fellenius_with_pore_pressure_critical():
    # 1 fatia: c=5, φ=25, W=200, α=20, ΔL=3, u=10
    # res = 5·3 + (200·cos20 − 10·3)·tan25 = 15 + (187.93852−30)·0.4663077
    #     = 15 + 157.93852·0.4663077 = 15 + 73.64793 = 88.64793
    # drv = 200·sin20 = 68.40402 ; FS = 88.64793/68.40402 = 1.29594 -> "crítico"
    slices = [Slice(w_kn=200.0, alpha_deg=20.0, dl_m=3.0, u_kpa=10.0)]
    r = fellenius_fs(slices, c_kpa=5.0, phi_deg=25.0)
    assert r.resisting_kn_m == pytest.approx(88.64793, abs=1e-3)
    assert r.driving_kn_m == pytest.approx(68.40402, abs=1e-3)
    assert r.fs == pytest.approx(1.29594, abs=1e-3)
    assert r.classification == "crítico"


def test_fellenius_rejects_invalid():
    with pytest.raises(ValueError):
        fellenius_fs([], c_kpa=10.0, phi_deg=20.0)  # sem fatias
    with pytest.raises(ValueError):
        fellenius_fs([Slice(w_kn=100.0, alpha_deg=10.0, dl_m=2.0)],
                     c_kpa=10.0, phi_deg=55.0)  # φ>50
    with pytest.raises(ValueError):
        fellenius_fs([Slice(w_kn=100.0, alpha_deg=10.0, dl_m=2.0)],
                     c_kpa=-1.0, phi_deg=20.0)  # c<0
    with pytest.raises(ValueError):
        # todas as fatias com α<0 -> Σ W·sinα <= 0 (FS indefinido)
        fellenius_fs([Slice(w_kn=100.0, alpha_deg=-10.0, dl_m=2.0)],
                     c_kpa=10.0, phi_deg=20.0)


# --- validação --------------------------------------------------------------
def test_validate_slope_infinite_stable():
    r = infinite_slope_fs(c_kpa=10.0, phi_deg=25.0, gamma_kn_m3=18.0,
                          z_m=3.0, beta_deg=15.0)
    rep = validate_slope(r)
    assert rep.passed is True
    assert any(c.name == "units" and c.status == "ok" for c in rep.checks)


def test_validate_slope_fellenius_stable():
    slices = [
        Slice(w_kn=100.0, alpha_deg=10.0, dl_m=2.0),
        Slice(w_kn=100.0, alpha_deg=30.0, dl_m=2.0),
    ]
    r = fellenius_fs(slices, c_kpa=0.0, phi_deg=30.0)
    rep = validate_slope(r)
    assert rep.passed is True
    assert any(c.name == "units" and c.status == "ok" for c in rep.checks)


def test_validate_slope_warns_when_critical():
    # FS em [1, 1.5) -> warning (alerta normativo), mas passed True
    slices = [Slice(w_kn=200.0, alpha_deg=20.0, dl_m=3.0, u_kpa=10.0)]
    r = fellenius_fs(slices, c_kpa=5.0, phi_deg=25.0)  # FS ≈ 1.296
    rep = validate_slope(r)
    assert rep.passed is True
    assert any("1.5" in w or "1,5" in w for w in rep.warnings)


def test_validate_slope_fails_when_unstable():
    # FS < 1 -> fail normativo, passed False
    r = infinite_slope_fs(c_kpa=0.0, phi_deg=20.0, gamma_kn_m3=18.0,
                          z_m=4.0, beta_deg=30.0)  # FS ≈ 0.63
    rep = validate_slope(r)
    assert rep.passed is False
