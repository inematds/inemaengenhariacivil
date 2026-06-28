"""Testes de pilar retangular de concreto armado com flambagem (NBR 6118:2014 cap.15).

Valores de referência calculados à mão (a conta está nos comentários). Coeficientes:
gamma_f=1.4, gamma_c=1.4, gamma_s=1.15; eps_cu=3.5permil, eps_c2=2.0permil; Es=210 GPa.

Esbeltez: i=h/sqrt(12); lambda=le/i; lambda1=(25+12.5*e1/h)/alpha_b limitado a [35,90].
2a ordem (15.8.3.3.2): nu=Nd/(Ac*fcd); 1/r=0.005/(h*(nu+0.5))<=0.005/h (h em metros);
M2d=Nd*le^2/10*(1/r); Md,tot=alpha_b*M1d,A+M2d>=M1d,min=Nd*(0.015+0.03*h[m]).
"""

import pytest

from lib.concrete.columns import (
    ColumnResult,
    column_moment_capacity,
    design_rectangular_column,
)


# ---------------------------------------------------- caso esbeltez média (médio)

def _medium_column():
    # Nk=900, Mk_topo=27, b=40, h=30 (direção analisada), le=400, C25, CA-50
    return design_rectangular_column(
        nk_kn=900.0, mk_topo_knm=27.0,
        b_cm=40.0, h_cm=30.0, le_cm=400.0,
        fck_mpa=25.0, fyk_mpa=500.0,
    )


def test_column_slenderness_and_class_medium():
    # Nd=1.4*900=1260; M1d,A=1.4*27=37.8
    # i=30/sqrt(12)=8.6603; lambda=400/8.6603=46.19
    # e1=37.8/1260=0.03 m; e1/h=0.10; lambda1_raw=25+12.5*0.10=26.25 -> limite 35
    # lambda1<lambda<=90 -> "medio"
    r = _medium_column()
    assert isinstance(r, ColumnResult)
    assert r.nd_kn == pytest.approx(1260.0, abs=1e-6)
    assert r.m1d_a_knm == pytest.approx(37.8, abs=1e-6)
    assert r.i_cm == pytest.approx(8.6603, abs=1e-3)
    assert r.esbeltez == pytest.approx(46.19, abs=0.05)
    assert r.lambda1 == pytest.approx(35.0, abs=1e-6)
    assert r.classe == "medio"


def test_column_second_order_curvature_medium():
    # nu=1260/(1200*1.785714)=0.588
    # 1/r=0.005/(0.30*1.088)=0.0153186  (cap 0.005/0.30=0.016667, não governa)
    # M2d=1260*16/10*0.0153186=30.882
    # M1d,min=1260*(0.015+0.03*0.30)=1260*0.024=30.24
    # Md,tot=1.0*37.8+30.882=68.682
    r = _medium_column()
    assert r.nu == pytest.approx(0.588, abs=0.002)
    assert r.one_over_r == pytest.approx(0.0153186, abs=1e-4)
    assert r.m2d_knm == pytest.approx(30.882, abs=0.1)
    assert r.m1d_min_knm == pytest.approx(30.24, abs=0.05)
    assert r.md_tot_knm == pytest.approx(68.682, abs=0.2)


def test_column_reinforcement_sanity_medium():
    r = _medium_column()
    assert r.as_calc_cm2 > 0
    assert r.as_adopted_cm2 >= r.as_min_cm2 - 1e-9
    assert r.as_adopted_cm2 <= r.as_max_cm2 + 1e-9
    # capacidade da seção >= solicitação (Nd, Md,tot)
    mrd = column_moment_capacity(
        r.nd_kn, r.as_adopted_cm2, r.b_cm, r.h_cm, r.d_linha_cm,
        r.fck_mpa, r.fyk_mpa,
    )
    assert mrd >= r.md_tot_knm - 1e-2
    if r.bitolas is not None:
        assert r.bitolas.as_ef_cm2 >= r.as_adopted_cm2 - 1e-9


# ------------------------------------------------------------ caso curto (curto)

def test_column_short_no_second_order():
    # h=40, b=40, le=200; i=40/sqrt(12)=11.547; lambda=200/11.547=17.32
    # Nd=1.4*1500=2100; M1d,A=1.4*50=70; e1=70/2100=0.03333 m; e1/h=0.0833
    # lambda1_raw=26.04 -> 35; lambda=17.32<=35 -> "curto", M2d=0
    # M1d,min=2100*(0.015+0.03*0.40)=2100*0.027=56.7; Md,tot=max(70,56.7)=70
    r = design_rectangular_column(
        nk_kn=1500.0, mk_topo_knm=50.0,
        b_cm=40.0, h_cm=40.0, le_cm=200.0,
        fck_mpa=25.0, fyk_mpa=500.0,
    )
    assert r.classe == "curto"
    assert r.esbeltez == pytest.approx(17.32, abs=0.05)
    assert r.m2d_knm == pytest.approx(0.0, abs=1e-9)
    assert r.m1d_min_knm == pytest.approx(56.7, abs=0.05)
    assert r.md_tot_knm == pytest.approx(70.0, abs=0.05)


# --------------------------------------- lambda1 pela fórmula (acima do limite 35)

def test_column_lambda1_formula_above_floor():
    # e1/h=1.0 -> lambda1_raw=25+12.5*1.0=37.5 (dentro de [35,90])
    # b=h=40, le=400: i=11.547; lambda=400/11.547=34.64 <= 37.5 -> "curto"
    # Nk=500 -> Nd=700; M1d,A=e1*Nd=0.40*700=280 -> Mk_topo=280/1.4=200
    r = design_rectangular_column(
        nk_kn=500.0, mk_topo_knm=200.0,
        b_cm=40.0, h_cm=40.0, le_cm=400.0,
        fck_mpa=25.0, fyk_mpa=500.0,
    )
    assert r.lambda1 == pytest.approx(37.5, abs=1e-6)
    assert r.classe == "curto"


# ------------------------------------------------------------------- abstenção

def test_column_rejects_excessive_slenderness():
    # le=600, h=20: i=5.7735; lambda=103.9 > 90 -> fora de escopo
    with pytest.raises(ValueError):
        design_rectangular_column(
            nk_kn=500.0, mk_topo_knm=20.0,
            b_cm=20.0, h_cm=20.0, le_cm=600.0,
            fck_mpa=25.0, fyk_mpa=500.0,
        )


def test_column_rejects_invalid_inputs():
    with pytest.raises(ValueError):
        design_rectangular_column(nk_kn=-1.0, mk_topo_knm=10.0, b_cm=30.0,
                                  h_cm=30.0, le_cm=300.0, fck_mpa=25.0, fyk_mpa=500.0)
    with pytest.raises(ValueError):
        design_rectangular_column(nk_kn=500.0, mk_topo_knm=10.0, b_cm=30.0,
                                  h_cm=30.0, le_cm=300.0, fck_mpa=60.0, fyk_mpa=500.0)
    with pytest.raises(ValueError):
        design_rectangular_column(nk_kn=500.0, mk_topo_knm=10.0, b_cm=-30.0,
                                  h_cm=30.0, le_cm=300.0, fck_mpa=25.0, fyk_mpa=500.0)


def test_column_min_steel_governs_for_light_load():
    # carga leve em seção grande -> As,mín governa (0.4% Ac ou 0.15 Nd/fyd)
    r = design_rectangular_column(
        nk_kn=300.0, mk_topo_knm=5.0,
        b_cm=40.0, h_cm=40.0, le_cm=250.0,
        fck_mpa=30.0, fyk_mpa=500.0,
    )
    assert r.as_adopted_cm2 == pytest.approx(r.as_min_cm2, abs=1e-6)
    assert r.governed_by == "As_min"
