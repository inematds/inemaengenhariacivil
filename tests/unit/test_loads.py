"""Testes da tabela consultável de ações — NBR 6120:2019.

Valores de referência conferidos contra a tabela da própria norma reproduzida em
`normas/NBR6120/README.md` (pesos específicos Tab.2 e cargas acidentais por uso).
"""

import pytest

from lib.structural.loads import (
    carga_acidental_uso,
    listar_materiais,
    listar_usos,
    peso_especifico_material,
    peso_proprio_laje_macica,
)


# ------------------------------------------------------ pesos específicos (Tab.2)

def test_peso_especifico_concreto_armado():
    # NBR 6120:2019 Tab.2 — concreto armado = 25,0 kN/m³
    r = peso_especifico_material("concreto armado")
    assert r.valor == pytest.approx(25.0)
    assert r.unidade == "kN/m³"


def test_peso_especifico_aceita_acentos_e_caixa():
    # "Aço" / "AÇO" / "aco" devem resolver para o mesmo material (78,5 kN/m³)
    assert peso_especifico_material("AÇO").valor == pytest.approx(78.5)
    assert peso_especifico_material("aco").valor == pytest.approx(78.5)


def test_peso_especifico_material_desconhecido_abstem():
    # material fora da tabela -> erro claro (nunca inventar valor)
    with pytest.raises(KeyError):
        peso_especifico_material("kriptonita")


# --------------------------------------------------- cargas acidentais por uso

def test_carga_acidental_escritorio():
    # README/NBR 6120 — escritório = 2,0 kN/m²
    r = carga_acidental_uso("escritório")
    assert r.valor == pytest.approx(2.0)
    assert r.unidade == "kN/m²"


def test_carga_acidental_corredor():
    # corredor/escada = 3,0 kN/m²
    assert carga_acidental_uso("corredor").valor == pytest.approx(3.0)


# ----------------------------------------------------------- peso próprio laje

def test_peso_proprio_laje_macica():
    # laje maciça h=10 cm: g_pp = 25 kN/m³ * 0,10 m = 2,5 kN/m²
    assert peso_proprio_laje_macica(h_cm=10.0) == pytest.approx(2.5)


# ----------------------------------------------------------------- listagens

def test_listagens_nao_vazias():
    # listagens devolvem chaves normalizadas (sem acento, minúsculas)
    assert "concreto armado" in listar_materiais()
    assert "escritorio" in listar_usos()
