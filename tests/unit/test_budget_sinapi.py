"""Testes da base local de preços tipo SINAPI (amostra ILUSTRATIVA).

Valores de referência vêm do CSV de amostra ``data/sinapi_amostra.csv`` — são
ilustrativos e devem ser substituídos pela SINAPI vigente/regional. A base é uma
tabela consultável: código inexistente -> KeyError (princípio da abstenção).
"""

from pathlib import Path

import pytest

from lib.budget.sinapi import SinapiItem, load_sinapi, lookup

CSV = Path(__file__).resolve().parents[2] / "data" / "sinapi_amostra.csv"


def _base():
    return load_sinapi(CSV)


def test_load_sinapi_returns_dict_of_items():
    base = _base()
    assert isinstance(base, dict)
    assert len(base) >= 15
    item = base["92873"]
    assert isinstance(item, SinapiItem)


def test_load_sinapi_known_values():
    base = _base()
    # concreto C25: m3 a R$ 520,00 (valor do CSV de amostra)
    c25 = base["92873"]
    assert c25.codigo == "92873"
    assert c25.unidade == "m3"
    assert c25.preco_unitario == pytest.approx(520.00, abs=1e-6)
    assert "C25" in c25.descricao or "25" in c25.descricao
    # aço CA-50: kg a R$ 12,50
    aco = base["92915"]
    assert aco.unidade == "kg"
    assert aco.preco_unitario == pytest.approx(12.50, abs=1e-6)


def test_codigo_e_string():
    base = _base()
    # códigos numéricos do CSV devem virar string (chave estável)
    assert all(isinstance(k, str) for k in base)
    assert "92915" in base


def test_lookup_known_code():
    base = _base()
    item = lookup("92438", base)
    assert item.unidade == "m2"
    assert item.preco_unitario == pytest.approx(85.00, abs=1e-6)


def test_lookup_unknown_code_raises_keyerror():
    base = _base()
    with pytest.raises(KeyError):
        lookup("00000-inexistente", base)


def test_sinapi_item_fields():
    item = SinapiItem(codigo="X1", descricao="teste", unidade="un", preco_unitario=10.0)
    assert item.codigo == "X1"
    assert item.descricao == "teste"
    assert item.unidade == "un"
    assert item.preco_unitario == 10.0
