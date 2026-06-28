"""Testes da camada de documentação da Fase 6 — pavimento, terraplenagem, taludes.

- ``render_pavement_memorial``: pavimento flexível DNER/DNIT — espessura total, camadas.
- ``render_earthwork_memorial``: balanço de terraplenagem — balanço, bota-fora/empréstimo.
- ``render_infinite_slope_memorial``: talude infinito — FS, classificação.
- ``render_fellenius_memorial``: Fellenius — FS, número de fatias.

Cada memorial deve conter o aviso de responsabilidade técnica (RESPONSABILIDADE
TÉCNICA + Lei 6.496/77) e exibir os valores-chave.
"""

from lib.earthwork.volumes import balanco_corte_aterro
from lib.geotechnical.slope_stability import Slice, fellenius_fs, infinite_slope_fs
from lib.pavement.flexible import design_flexible_pavement
from lib.reporting.memorial import (
    render_earthwork_memorial,
    render_fellenius_memorial,
    render_infinite_slope_memorial,
    render_pavement_memorial,
)
from lib.validators.earthwork_check import validate_earthwork
from lib.validators.pavement_check import validate_pavement
from lib.validators.slope_check import validate_slope


def _disclaimer_ok(md: str) -> None:
    assert "RESPONSABILIDADE TÉCNICA" in md
    assert "6.496/77" in md


# --- pavimento flexível ----------------------------------------------------
def test_pavement_memorial_has_disclaimer_and_total():
    r = design_flexible_pavement(cbr_subleito=10.0, n_trafego=1.0e6)
    rep = validate_pavement(r)
    md = render_pavement_memorial(r, rep)

    _disclaimer_ok(md)
    assert "Pavimento Flexível" in md
    assert "DNER" in md
    # valor-chave: espessura total
    assert f"{r.espessura_total_cm:.1f}" in md
    assert f"{r.hm_cm:.2f}" in md
    assert "## 5. Validação automática" in md


# --- terraplenagem ---------------------------------------------------------
def test_earthwork_memorial_has_disclaimer_and_balance():
    r = balanco_corte_aterro(5000.0, 3000.0, 1.25)
    rep = validate_earthwork(r)
    md = render_earthwork_memorial(r, rep)

    _disclaimer_ok(md)
    assert "Terraplenagem" in md
    # valor-chave: balanço
    assert f"{r.balanco_m3:.1f}" in md
    assert r.situacao in md
    assert f"{r.volume_corte_solto_m3:.1f}" in md


# --- talude infinito -------------------------------------------------------
def test_infinite_slope_memorial_has_disclaimer_and_fs():
    r = infinite_slope_fs(c_kpa=10.0, phi_deg=25.0, gamma_kn_m3=18.0, z_m=3.0, beta_deg=20.0)
    rep = validate_slope(r)
    md = render_infinite_slope_memorial(r, rep)

    _disclaimer_ok(md)
    assert "Talude Infinito" in md
    assert "NBR 11682" in md
    # valor-chave: FS
    assert f"{r.fs:.3f}" in md
    assert r.classification in md


# --- Fellenius -------------------------------------------------------------
def test_fellenius_memorial_has_disclaimer_and_fs():
    slices = [
        Slice(w_kn=50.0, alpha_deg=-10.0, dl_m=2.0),
        Slice(w_kn=120.0, alpha_deg=10.0, dl_m=2.1),
        Slice(w_kn=150.0, alpha_deg=30.0, dl_m=2.6),
    ]
    r = fellenius_fs(slices, c_kpa=15.0, phi_deg=20.0)
    rep = validate_slope(r)
    md = render_fellenius_memorial(r, rep)

    _disclaimer_ok(md)
    assert "Fellenius" in md
    assert "NBR 11682" in md
    # valor-chave: FS e nº de fatias
    assert f"{r.fs:.3f}" in md
    assert f"| {r.n_slices} |" in md
