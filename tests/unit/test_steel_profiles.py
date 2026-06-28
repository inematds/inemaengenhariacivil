"""Testes da tabela de perfis laminados W (NBR 8800:2008 / catálogo Gerdau).

Verifica carregamento, busca com abstenção (KeyError) e consistência interna:
rx = sqrt(Ix/A) e ry = sqrt(Iy/A) (geometria do perfil).
"""

import math

import pytest

from lib.steel.profiles import (
    DEFAULT_TABLE,
    ProfileProperties,
    get_profile,
    load_profiles,
)


# ----------------------------------------------------------------- load_profiles

def test_load_profiles_returns_typed_dict():
    base = load_profiles(DEFAULT_TABLE)
    assert isinstance(base, dict)
    assert len(base) >= 12               # tabela mínima pedida (~12 perfis)
    for desig, prof in base.items():
        assert isinstance(prof, ProfileProperties)
        assert prof.designacao == desig


def test_default_table_includes_reference_profiles():
    base = load_profiles(DEFAULT_TABLE)
    for desig in ("W150x13,0", "W200x19,3", "W250x22,3", "W360x32,9", "W410x38,8"):
        assert desig in base


# -------------------------------------------------------------------- get_profile

def test_get_profile_known():
    base = load_profiles(DEFAULT_TABLE)
    # W250x22,3 (Gerdau): A=28,4 cm²; Ix=2939 cm⁴; Iy=122 cm⁴; ry=2,07 cm
    p = get_profile("W250x22,3", base)
    assert p.area_cm2 == pytest.approx(28.4, abs=0.05)
    assert p.ix_cm4 == pytest.approx(2939, abs=1)
    assert p.iy_cm4 == pytest.approx(122, abs=1)
    assert p.ry_cm == pytest.approx(2.07, abs=0.01)


def test_get_profile_missing_raises_keyerror_with_list():
    # abstenção: perfil inexistente -> KeyError listando as designações disponíveis
    base = load_profiles(DEFAULT_TABLE)
    with pytest.raises(KeyError) as exc:
        get_profile("W999x99,9", base)
    msg = str(exc.value)
    assert "W999x99,9" in msg
    assert "W250x22,3" in msg          # a mensagem deve listar perfis válidos


# --------------------------------------------------- consistência interna (rx, ry)

def test_rx_consistency_all_profiles():
    # rx ≈ sqrt(Ix/A) para todo perfil (tolerância de arredondamento de catálogo)
    base = load_profiles(DEFAULT_TABLE)
    for desig, p in base.items():
        rx_calc = math.sqrt(p.ix_cm4 / p.area_cm2)
        assert rx_calc == pytest.approx(p.rx_cm, rel=0.02), desig


def test_ry_consistency_all_profiles():
    # ry ≈ sqrt(Iy/A) para todo perfil
    base = load_profiles(DEFAULT_TABLE)
    for desig, p in base.items():
        ry_calc = math.sqrt(p.iy_cm4 / p.area_cm2)
        assert ry_calc == pytest.approx(p.ry_cm, rel=0.02), desig


def test_weak_axis_is_y():
    # para perfil I, Iy < Ix (eixo de menor inércia governa a flambagem)
    base = load_profiles(DEFAULT_TABLE)
    for desig, p in base.items():
        assert p.iy_cm4 < p.ix_cm4, desig
        assert p.ry_cm < p.rx_cm, desig
