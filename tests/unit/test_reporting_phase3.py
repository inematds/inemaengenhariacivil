"""Testes dos memoriais da Fase 3 (geotecnia + hidráulica).

Cada memorial deve conter o aviso de responsabilidade técnica ("RESPONSABILIDADE
TÉCNICA" + Lei 6.496/77) e os valores-chave do cálculo.
"""

from lib.geotechnical.bearing_capacity import design_bearing_capacity
from lib.geotechnical.earth_pressure import (
    coulomb_earth_pressure,
    rankine_earth_pressure,
)
from lib.geotechnical.piles import SoilLayer, comparar_metodos_estaca
from lib.geotechnical.settlement import (
    consolidation_settlement,
    elastic_settlement,
)
from lib.hydraulic.head_loss import total_head_loss
from lib.hydraulic.open_channel import manning_rectangular
from lib.hydraulic.pipe_flow import (
    pipe_flow_darcy_weisbach,
    pipe_flow_hazen_williams,
)
from lib.reporting.memorial import (
    render_bearing_capacity_memorial,
    render_consolidation_settlement_memorial,
    render_earth_pressure_memorial,
    render_elastic_settlement_memorial,
    render_head_loss_memorial,
    render_open_channel_memorial,
    render_pile_comparison_memorial,
    render_pipe_flow_memorial,
)
from lib.service import _combine_pile_reports
from lib.validators.geotech_check import (
    validate_bearing,
    validate_earth_pressure,
    validate_pile,
    validate_settlement,
)
from lib.validators.hydraulic_check import (
    validate_head_loss,
    validate_open_channel,
    validate_pipe_flow,
)


def _assert_disclaimer(md: str) -> None:
    assert "RESPONSABILIDADE TÉCNICA" in md
    assert "6.496/77" in md


def test_bearing_capacity_memorial():
    r = design_bearing_capacity(
        c_kpa=10.0, phi_deg=30.0, gamma_kn_m3=18.0, b_m=2.0, depth_df_m=1.5,
    )
    md = render_bearing_capacity_memorial(r, validate_bearing(r))
    _assert_disclaimer(md)
    assert "NBR 6122" in md
    assert f"q_ult = {r.q_ult_kpa:.1f} kPa" in md
    assert f"q_adm = q_ult/FS = {r.q_adm_kpa:.1f} kPa" in md


def test_elastic_settlement_memorial():
    r = elastic_settlement(q_kpa=150.0, b_m=2.0, poisson_nu=0.3, iw=0.95, es_kpa=20000.0)
    md = render_elastic_settlement_memorial(r, validate_settlement(r))
    _assert_disclaimer(md)
    assert "Recalque Elástico" in md
    assert f"s = {r.settlement_mm:.2f} mm" in md


def test_consolidation_settlement_memorial():
    r = consolidation_settlement(
        cc=0.3, e0=0.8, h_m=4.0, sigma0_kpa=80.0, delta_sigma_kpa=60.0,
    )
    md = render_consolidation_settlement_memorial(r, validate_settlement(r))
    _assert_disclaimer(md)
    assert "Adensamento" in md
    assert f"s = {r.settlement_mm:.2f} mm" in md


def test_earth_pressure_rankine_memorial():
    r = rankine_earth_pressure(gamma_kn_m3=18.0, h_m=4.0, phi_deg=30.0)
    md = render_earth_pressure_memorial(r, validate_earth_pressure(r))
    _assert_disclaimer(md)
    assert "Rankine" in md
    assert f"Ka = {r.ka:.4f}" in md
    assert f"Ea = {r.ea_active_kn_m:.2f} kN/m" in md


def test_earth_pressure_coulomb_memorial():
    r = coulomb_earth_pressure(
        gamma_kn_m3=18.0, h_m=4.0, phi_deg=30.0, delta_deg=20.0, beta_deg=0.0, alpha_deg=10.0,
    )
    md = render_earth_pressure_memorial(r, validate_earth_pressure(r))
    _assert_disclaimer(md)
    assert "Coulomb" in md
    assert "Atrito solo-muro δ" in md
    assert f"Ka = {r.ka:.4f}" in md


def test_pile_comparison_memorial_shows_divergence():
    layers = [
        SoilLayer(n_spt=8, soil_type="argila siltosa", thickness_m=4.0),
        SoilLayer(n_spt=20, soil_type="areia siltosa", thickness_m=6.0),
    ]
    r = comparar_metodos_estaca(layers, "pre-moldada", 0.30)
    rep = _combine_pile_reports(r, validate_pile(r.aoki), validate_pile(r.decourt))
    md = render_pile_comparison_memorial(r, rep)
    _assert_disclaimer(md)
    assert "Aoki-Velloso" in md and "Décourt-Quaresma" in md
    assert f"Divergência relativa = {r.divergencia_pct:.1f}%" in md


def test_pipe_flow_hazen_williams_memorial():
    r = pipe_flow_hazen_williams(Q_m3s=0.05, D_m=0.30, L_m=1000.0, C=130.0)
    md = render_pipe_flow_memorial(r, validate_pipe_flow(r))
    _assert_disclaimer(md)
    assert "Hazen-Williams" in md
    assert f"hf = {r.hf_m:.3f} m" in md


def test_pipe_flow_darcy_weisbach_memorial():
    r = pipe_flow_darcy_weisbach(Q_m3s=0.05, D_m=0.30, L_m=1000.0, eps_m=1.5e-4)
    md = render_pipe_flow_memorial(r, validate_pipe_flow(r))
    _assert_disclaimer(md)
    assert "Darcy-Weisbach" in md
    assert f"f = {r.f:.4f}" in md
    assert f"hf = {r.hf_m:.3f} m" in md


def test_open_channel_memorial():
    r = manning_rectangular(b_m=1.0, y_m=0.5, n=0.013, S=0.001)
    md = render_open_channel_memorial(r, validate_open_channel(r))
    _assert_disclaimer(md)
    assert "Manning" in md
    assert f"Q = {r.Q_m3s:.4f} m³/s" in md


def test_head_loss_memorial():
    r = total_head_loss(
        hf_distribuida_m=2.0, singularidades={"curva_90": 2, "registro_gaveta_aberto": 1},
        V_ms=1.5,
    )
    md = render_head_loss_memorial(r, validate_head_loss(r))
    _assert_disclaimer(md)
    assert f"hf,total = {r.hf_total_m:.3f} m" in md
    assert "curva_90" in md
