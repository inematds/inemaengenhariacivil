"""Testes da camada de documentação da Fase 5 — memoriais de estruturas metálicas.

- ``render_compression_memorial``: barra comprimida (NBR 8800 §5.3) — Nc,Rd, χ, λ0.
- ``render_bolted_memorial``: ligação parafusada (§6.3) — nº de parafusos, governante.
- ``render_weld_memorial``: solda de filete (§6.2.6) — comprimento necessário.

Cada memorial deve conter o aviso de responsabilidade técnica (RESPONSABILIDADE
TÉCNICA + Lei 6.496/77), citar a NBR 8800 e exibir os valores-chave.
"""

from lib.reporting.memorial import (
    render_bolted_memorial,
    render_compression_memorial,
    render_weld_memorial,
)
from lib.steel.connections import design_bolted_connection, design_fillet_weld
from lib.steel.profiles import DEFAULT_TABLE, load_profiles
from lib.steel.stability import design_compression
from lib.validators.steel_check import validate_compression
from lib.validators.steel_connections_check import validate_bolted, validate_weld


def _disclaimer_ok(md: str) -> None:
    assert "RESPONSABILIDADE TÉCNICA" in md
    assert "6.496/77" in md
    assert "NBR 8800" in md


# --- compressão ------------------------------------------------------------
def test_compression_memorial_has_disclaimer_norm_and_ncrd():
    base = load_profiles(DEFAULT_TABLE)
    r = design_compression("W250x22,3", base, kl_cm=300.0, fy_mpa=250.0)
    rep = validate_compression(r)
    md = render_compression_memorial(r, rep)

    _disclaimer_ok(md)
    assert "Barra Comprimida" in md
    assert "W250x22,3" in md
    # valor-chave: Nc,Rd (213,33 kN)
    assert "Nc,Rd" in md
    assert f"{r.nc_rd_kn:.2f}" in md
    assert f"{r.chi:.4f}" in md
    assert f"{r.lambda_0:.4f}" in md
    assert "## 4. Validação automática" in md


# --- ligação parafusada ----------------------------------------------------
def test_bolted_memorial_has_disclaimer_norm_and_n_bolts():
    r = design_bolted_connection(
        forca_kn=200.0, db_mm=20.0, fub_mpa=800.0, t_mm=9.5, fu_mpa=400.0,
    )
    rep = validate_bolted(r)
    md = render_bolted_memorial(r, rep)

    _disclaimer_ok(md)
    assert "Ligação Parafusada" in md
    # valor-chave: nº de parafusos (3)
    assert f"**{r.n_parafusos}**" in md
    assert r.governante in md
    assert f"{r.capacidade_total_kn:.2f}" in md


# --- solda de filete -------------------------------------------------------
def test_weld_memorial_has_disclaimer_norm_and_length():
    r = design_fillet_weld(forca_kn=200.0, perna_mm=6.0)
    rep = validate_weld(r)
    md = render_weld_memorial(r, rep)

    _disclaimer_ok(md)
    assert "Solda de Filete" in md
    # valor-chave: comprimento necessário de solda
    assert "Comprimento de solda" in md
    assert f"{r.comprimento_nec_cm:.2f}" in md
    assert f"{r.rd_kn_cm:.4f}" in md
