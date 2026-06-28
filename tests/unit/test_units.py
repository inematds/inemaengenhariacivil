"""Testes da camada de unidades (pint)."""

import pytest

from lib.units.registry import Q_, ensure, ureg


def test_ensure_converts_to_requested_unit():
    # 5 metros pedidos em centímetros -> 500
    assert ensure(Q_(5, "meter"), "centimeter") == pytest.approx(500.0)


def test_ensure_accepts_plain_float_as_already_in_unit():
    # valor sem unidade é interpretado como já estando na unidade-alvo
    assert ensure(25.0, "centimeter") == pytest.approx(25.0)


def test_ensure_raises_on_dimensional_mismatch():
    # passar uma força onde se espera comprimento deve falhar
    with pytest.raises(Exception):
        ensure(Q_(10, "kilonewton"), "centimeter")


def test_registry_is_shared_singleton():
    # Q_ deve pertencer ao mesmo registry exportado (pint exige isso p/ operar juntos)
    assert Q_(1, "meter").to("centimeter").magnitude == pytest.approx(100.0)
    assert ureg is Q_(1, "meter")._REGISTRY
