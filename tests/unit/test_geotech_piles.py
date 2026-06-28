"""Testes de capacidade de estaca por SPT — Aoki-Velloso e Décourt-Quaresma.

Valores de referência calculados à mão (a conta está nos comentários).
Fontes:
  - Aoki, N. & Velloso, D.A. (1975). Coeficientes K, α por solo; F1, F2 por estaca.
  - Décourt, L. & Quaresma, A.R. (1978). Coeficiente C por solo; rl = 10·(N/3+1).

Perfil A (estaca pré-moldada D=0,30 m; Ap=π·0,30²/4=0,0706858 m²; U=π·0,30=0,942478 m):
  camada 1: argila        N=5  3 m
  camada 2: argila arenosa N=8  3 m
  camada 3: areia         N=20 3 m (ponta) -> L=9 m
"""

import pytest

from lib.geotechnical.piles import (
    PileCapacityResult,
    PileComparisonResult,
    SoilLayer,
    aoki_velloso,
    comparar_metodos_estaca,
    decourt_quaresma,
)
from lib.validators.geotech_check import validate_pile

PERFIL_A = [
    SoilLayer(n_spt=5, soil_type="argila", thickness_m=3.0),
    SoilLayer(n_spt=8, soil_type="argila arenosa", thickness_m=3.0),
    SoilLayer(n_spt=20, soil_type="areia", thickness_m=3.0),
]


def test_aoki_velloso_perfil_a():
    # F1=1.75, F2=3.5 (pré-moldada). Ap=0.0706858, U=0.942478, L=9
    # Ponta (areia K=1000, N=20): qp=K·N/F1=1000·20/1.75=11428.57 kPa
    #   Rp = qp·Ap = 11428.57·0.0706858 = 807.84 kN
    # Lateral fl=α·K·N/F2 ; contrib=fl·U·ΔL (U·ΔL=0.942478·3=2.827433)
    #   c1 argila (K=200,α=0.06,N=5): fl=0.06·200·5/3.5=17.1429 -> 48.470 kN
    #   c2 argila arenosa (K=350,α=0.024,N=8): fl=0.024·350·8/3.5=19.20 -> 54.287 kN
    #   c3 areia (K=1000,α=0.014,N=20): fl=0.014·1000·20/3.5=80.0 -> 226.195 kN
    #   Rl = 328.95 kN
    # Rult = 807.84 + 328.95 = 1136.79 kN ; Radm(FS=2) = 568.40 kN
    r = aoki_velloso(PERFIL_A, pile_type="pre-moldada", diameter_m=0.30, fs=2.0)
    assert isinstance(r, PileCapacityResult)
    assert r.ap_m2 == pytest.approx(0.0706858, abs=1e-6)
    assert r.u_m == pytest.approx(0.942478, abs=1e-6)
    assert r.length_m == pytest.approx(9.0, abs=1e-9)
    assert r.rp_kn == pytest.approx(807.84, abs=0.5)
    assert r.rl_kn == pytest.approx(328.95, abs=0.5)
    assert r.rult_kn == pytest.approx(1136.79, abs=1.0)
    assert r.radm_kn == pytest.approx(568.40, abs=0.5)


def test_decourt_quaresma_perfil_a():
    # Ponta (areia C=400, Np=20): qp=C·Np=400·20=8000 kPa
    #   Rp = 8000·0.0706858 = 565.49 kN
    # Lateral: Ns=média(5,8,20)=11 ; rl=10·(11/3+1)=46.6667 kPa
    #   Rl = rl·U·L = 46.6667·0.942478·9 = 46.6667·8.48230 = 395.84 kN
    # Rult = 565.49 + 395.84 = 961.33 kN ; Radm(FS=2) = 480.66 kN
    r = decourt_quaresma(PERFIL_A, pile_type="pre-moldada", diameter_m=0.30, fs=2.0)
    assert isinstance(r, PileCapacityResult)
    assert r.rp_kn == pytest.approx(565.49, abs=0.5)
    assert r.rl_kn == pytest.approx(395.84, abs=0.5)
    assert r.rult_kn == pytest.approx(961.33, abs=1.0)
    assert r.radm_kn == pytest.approx(480.66, abs=0.5)


def test_comparar_metodos_convergem():
    # Rult_aoki=1136.79, Rult_decourt=961.33
    # divergência = |1136.79−961.33|/1136.79 = 175.46/1136.79 = 0.1543 (15.4%) < 20%
    cmp = comparar_metodos_estaca(PERFIL_A, pile_type="pre-moldada", diameter_m=0.30, fs=2.0)
    assert isinstance(cmp, PileComparisonResult)
    assert cmp.divergencia == pytest.approx(0.1543, abs=0.005)
    assert cmp.convergem is True
    assert not any("diverg" in w.lower() for w in cmp.warnings)


def test_comparar_metodos_diverge_emite_aviso():
    # Perfil único: areia N=50, 10 m, pré-moldada D=0.30
    # Aoki:    Rp=2019.60 ; Rl=200·9.424778=1884.96 ; Rult=3904.55
    # Décourt: Rp=20000·0.0706858=1413.72 ; rl=10·(50/3+1)=176.667 ; Rl=1665.04 ; Rult=3078.76
    # divergência = |3904.55−3078.76|/3904.55 = 0.2115 (21.2%) > 20% -> aviso
    perfil = [SoilLayer(n_spt=50, soil_type="areia", thickness_m=10.0)]
    cmp = comparar_metodos_estaca(perfil, pile_type="pre-moldada", diameter_m=0.30, fs=2.0)
    assert cmp.divergencia > 0.20
    assert cmp.convergem is False
    assert any("diverg" in w.lower() for w in cmp.warnings)


def test_validate_pile_passes():
    r = aoki_velloso(PERFIL_A, pile_type="pre-moldada", diameter_m=0.30, fs=2.0)
    rep = validate_pile(r)
    assert rep.passed is True
    assert any(c.name == "units" and c.status == "ok" for c in rep.checks)
    rep_d = validate_pile(decourt_quaresma(PERFIL_A, pile_type="pre-moldada",
                                           diameter_m=0.30, fs=2.0))
    assert rep_d.passed is True


def test_piles_reject_invalid():
    with pytest.raises(ValueError):
        aoki_velloso([SoilLayer(n_spt=60, soil_type="areia", thickness_m=3.0)],
                     pile_type="pre-moldada", diameter_m=0.30)  # N>50
    with pytest.raises(ValueError):
        aoki_velloso([SoilLayer(n_spt=10, soil_type="rocha", thickness_m=3.0)],
                     pile_type="pre-moldada", diameter_m=0.30)  # solo não tabelado
    with pytest.raises(ValueError):
        aoki_velloso(PERFIL_A, pile_type="helice", diameter_m=0.30)  # estaca não tabelada
    with pytest.raises(ValueError):
        aoki_velloso(PERFIL_A, pile_type="pre-moldada", diameter_m=0.0)  # D<=0
    with pytest.raises(ValueError):
        decourt_quaresma([], pile_type="pre-moldada", diameter_m=0.30)  # perfil vazio
