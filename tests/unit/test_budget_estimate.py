"""Testes da montagem de orçamento e da validação aritmética.

Valores de referência calculados à mão (a conta está nos comentários). Preços vêm
do CSV de amostra ILUSTRATIVO ``data/sinapi_amostra.csv``.
"""

from pathlib import Path

import pytest

from lib.budget.estimate import ItemOrcamento, OrcamentoResult, montar_orcamento
from lib.budget.sinapi import load_sinapi
from lib.validators.budget_check import validate_orcamento
from lib.validators.report import ValidationReport

CSV = Path(__file__).resolve().parents[2] / "data" / "sinapi_amostra.csv"


def _base():
    return load_sinapi(CSV)


def test_montar_orcamento_known_case():
    # 2 m³ concreto C25 (92873) a R$ 520,00 -> 1040,00
    # 100 kg aço CA-50 (92915) a R$ 12,50 -> 1250,00
    # subtotal = 1040 + 1250 = 2290,00
    # BDI 25% -> valor_bdi = 2290·0,25 = 572,50; total = 2290·1,25 = 2862,50
    r = montar_orcamento(
        [{"codigo": "92873", "quantidade": 2.0},
         {"codigo": "92915", "quantidade": 100.0}],
        _base(),
        bdi_pct=25.0,
    )
    assert isinstance(r, OrcamentoResult)
    assert len(r.itens) == 2
    assert r.itens[0].custo == pytest.approx(1040.00, abs=1e-6)
    assert r.itens[1].custo == pytest.approx(1250.00, abs=1e-6)
    assert r.itens[0].unidade == "m3"
    assert r.subtotal == pytest.approx(2290.00, abs=1e-6)
    assert r.bdi_pct == pytest.approx(25.0, abs=1e-9)
    assert r.valor_bdi == pytest.approx(572.50, abs=1e-6)
    assert r.total == pytest.approx(2862.50, abs=1e-6)


def test_montar_orcamento_sem_bdi():
    # BDI padrão = 0 -> total == subtotal
    # 3 m² forma (92438) a R$ 85,00 -> 255,00
    r = montar_orcamento([{"codigo": "92438", "quantidade": 3.0}], _base())
    assert r.bdi_pct == 0.0
    assert r.subtotal == pytest.approx(255.00, abs=1e-6)
    assert r.valor_bdi == pytest.approx(0.0, abs=1e-9)
    assert r.total == pytest.approx(255.00, abs=1e-6)


def test_montar_orcamento_item_detalhado():
    r = montar_orcamento([{"codigo": "92915", "quantidade": 10.0}], _base())
    item = r.itens[0]
    assert isinstance(item, ItemOrcamento)
    assert item.codigo == "92915"
    assert item.quantidade == pytest.approx(10.0)
    assert item.preco_unitario == pytest.approx(12.50, abs=1e-6)
    assert item.custo == pytest.approx(125.00, abs=1e-6)
    assert item.descricao  # descrição preenchida a partir da base


def test_montar_orcamento_quantidade_negativa_raises():
    with pytest.raises(ValueError):
        montar_orcamento([{"codigo": "92873", "quantidade": -1.0}], _base())


def test_montar_orcamento_bdi_fora_faixa_raises():
    with pytest.raises(ValueError):
        montar_orcamento([{"codigo": "92873", "quantidade": 1.0}], _base(), bdi_pct=41.0)
    with pytest.raises(ValueError):
        montar_orcamento([{"codigo": "92873", "quantidade": 1.0}], _base(), bdi_pct=-5.0)


def test_montar_orcamento_codigo_inexistente_raises():
    with pytest.raises(KeyError):
        montar_orcamento([{"codigo": "00000-x", "quantidade": 1.0}], _base())


def test_validate_orcamento_passes():
    r = montar_orcamento(
        [{"codigo": "92873", "quantidade": 2.0},
         {"codigo": "92915", "quantidade": 100.0}],
        _base(),
        bdi_pct=25.0,
    )
    rep = validate_orcamento(r)
    assert isinstance(rep, ValidationReport)
    assert rep.passed is True
    assert all(c.status != "fail" for c in rep.checks)


def test_validate_orcamento_detects_inconsistent_total():
    # total adulterado (não bate com subtotal·(1+bdi)) -> reprova
    bad = OrcamentoResult(
        itens=[ItemOrcamento(codigo="X", descricao="d", unidade="un",
                             quantidade=2.0, preco_unitario=10.0, custo=20.0)],
        subtotal=20.0, bdi_pct=10.0, valor_bdi=2.0, total=999.0,
    )
    rep = validate_orcamento(bad)
    assert rep.passed is False
    assert any(c.status == "fail" for c in rep.checks)


def test_validate_orcamento_detects_negative_price():
    bad = OrcamentoResult(
        itens=[ItemOrcamento(codigo="X", descricao="d", unidade="un",
                             quantidade=1.0, preco_unitario=-5.0, custo=-5.0)],
        subtotal=-5.0, bdi_pct=0.0, valor_bdi=0.0, total=-5.0,
    )
    rep = validate_orcamento(bad)
    assert rep.passed is False


def test_validate_orcamento_detects_bad_subtotal():
    # custos certos por item, mas subtotal não é a soma -> reprova
    bad = OrcamentoResult(
        itens=[ItemOrcamento(codigo="X", descricao="d", unidade="un",
                             quantidade=2.0, preco_unitario=10.0, custo=20.0)],
        subtotal=50.0, bdi_pct=0.0, valor_bdi=0.0, total=50.0,
    )
    rep = validate_orcamento(bad)
    assert rep.passed is False
