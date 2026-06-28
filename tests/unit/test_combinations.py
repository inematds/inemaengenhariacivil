"""Testes de combinações de ações (NBR 8681:2003 / NBR 6118:2014).

Valores de referência calculados à mão (a conta está em cada comentário).
ELU normal:  Fd = γg·Gk + γq·(Qk_princ + Σ ψ0·Qk_sec)
ELS q.perm.: Fd,serv = Gk + Σ ψ2·Qk
"""

import pytest

from lib.structural.combinations import (
    CombinationResult,
    combinar_els_quase_permanente,
    combinar_elu_normal,
)


# ---------------------------------------------------------- combinar_elu_normal

def test_elu_normal_sem_secundarias():
    # Fd = 1.4*20 + 1.4*(15) = 28 + 21 = 49.0
    r = combinar_elu_normal(gk=20.0, qk_principal=15.0)
    assert isinstance(r, CombinationResult)
    assert r.fd == pytest.approx(49.0, abs=1e-9)
    assert r.parcela_permanente == pytest.approx(28.0, abs=1e-9)
    assert r.parcela_variavel == pytest.approx(21.0, abs=1e-9)
    assert r.tipo == "ELU-normal"


def test_elu_normal_com_secundarias():
    # Fd = 1.4*20 + 1.4*(15 + 0.5*10 + 0.5*8)
    #    = 28 + 1.4*(15 + 5 + 4) = 28 + 1.4*24 = 28 + 33.6 = 61.6
    r = combinar_elu_normal(
        gk=20.0, qk_principal=15.0, qk_secundarias=[10.0, 8.0], psi0=0.5
    )
    assert r.fd == pytest.approx(61.6, abs=1e-9)
    assert r.parcela_permanente == pytest.approx(28.0, abs=1e-9)
    assert r.parcela_variavel == pytest.approx(33.6, abs=1e-9)


def test_elu_normal_coeficientes_customizados():
    # Fd = 1.35*10 + 1.5*(20) = 13.5 + 30 = 43.5
    r = combinar_elu_normal(gk=10.0, qk_principal=20.0, gamma_g=1.35, gamma_q=1.5)
    assert r.fd == pytest.approx(43.5, abs=1e-9)


# ----------------------------------------------- combinar_els_quase_permanente

def test_els_quase_permanente():
    # Fd,serv = 20 + 0.3*15 + 0.3*10 = 20 + 4.5 + 3 = 27.5
    r = combinar_els_quase_permanente(gk=20.0, qks=[15.0, 10.0], psi2=0.3)
    assert isinstance(r, CombinationResult)
    assert r.fd == pytest.approx(27.5, abs=1e-9)
    assert r.parcela_permanente == pytest.approx(20.0, abs=1e-9)
    assert r.parcela_variavel == pytest.approx(7.5, abs=1e-9)
    assert r.tipo == "ELS-quase-permanente"


def test_els_quase_permanente_sem_variaveis():
    # Fd,serv = 12 + 0 = 12.0
    r = combinar_els_quase_permanente(gk=12.0, qks=[])
    assert r.fd == pytest.approx(12.0, abs=1e-9)
    assert r.parcela_variavel == pytest.approx(0.0, abs=1e-9)


# ----------------------------------------------------------------- abstenção

def test_combinacao_rejeita_negativos():
    with pytest.raises(ValueError):
        combinar_elu_normal(gk=-1.0, qk_principal=10.0)
    with pytest.raises(ValueError):
        combinar_elu_normal(gk=10.0, qk_principal=-5.0)
    with pytest.raises(ValueError):
        combinar_elu_normal(gk=10.0, qk_principal=5.0, qk_secundarias=[-2.0])
    with pytest.raises(ValueError):
        combinar_els_quase_permanente(gk=-1.0, qks=[5.0])
    with pytest.raises(ValueError):
        combinar_els_quase_permanente(gk=10.0, qks=[5.0, -2.0])
