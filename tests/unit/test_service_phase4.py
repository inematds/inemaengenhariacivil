"""Testes do orquestrador de orçamento da Fase 4 (``solve_orcamento``).

Devolve o pacote serializável padrão: resultado, validação, memorial (com aviso
embutido), aviso (Lei 6.496/77) e o flag ``aprovado`` coerente. Propaga as abstenções
dos núcleos (código inexistente, BDI fora de faixa, quantidade negativa, lista vazia).
"""

import pathlib

import pytest

from lib.service import solve_orcamento

_KEYS = {"resultado", "validacao", "memorial_markdown", "aviso", "aprovado"}
_CSV = str(pathlib.Path(__file__).resolve().parents[2] / "data" / "sinapi_amostra.csv")


def _assert_bundle(bundle: dict) -> None:
    assert set(bundle) >= _KEYS
    assert "6.496/77" in bundle["aviso"]
    assert "RESPONSABILIDADE TÉCNICA" in bundle["memorial_markdown"]
    assert bundle["aprovado"] == bundle["validacao"]["passed"]


def test_solve_orcamento_bundle_approved():
    bundle = solve_orcamento(
        itens=[
            {"codigo": "92873", "quantidade": 1.5},
            {"codigo": "92915", "quantidade": 180.0},
            {"codigo": "92438", "quantidade": 18.0},
        ],
        bdi_pct=25.0,
        csv_path=_CSV,
    )
    _assert_bundle(bundle)
    assert bundle["aprovado"] is True
    # subtotal = 780 + 2250 + 1530 = 4560; total = 4560 * 1.25 = 5700
    assert bundle["resultado"]["subtotal"] == pytest.approx(4560.0)
    assert bundle["resultado"]["valor_bdi"] == pytest.approx(1140.0)
    assert bundle["resultado"]["total"] == pytest.approx(5700.0)
    assert len(bundle["resultado"]["itens"]) == 3


def test_solve_orcamento_zero_bdi():
    bundle = solve_orcamento(
        itens=[{"codigo": "87490", "quantidade": 100.0}],
        csv_path=_CSV,
    )
    _assert_bundle(bundle)
    assert bundle["resultado"]["bdi_pct"] == 0.0
    assert bundle["resultado"]["total"] == pytest.approx(bundle["resultado"]["subtotal"])


def test_solve_orcamento_unknown_code_aborts():
    with pytest.raises(KeyError):
        solve_orcamento(itens=[{"codigo": "00000", "quantidade": 1.0}], csv_path=_CSV)


def test_solve_orcamento_bdi_out_of_range_aborts():
    with pytest.raises(ValueError):
        solve_orcamento(
            itens=[{"codigo": "92873", "quantidade": 1.0}], bdi_pct=50.0, csv_path=_CSV,
        )


def test_solve_orcamento_empty_items_aborts():
    with pytest.raises(ValueError):
        solve_orcamento(itens=[], csv_path=_CSV)
