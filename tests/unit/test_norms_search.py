"""Testes da busca léxica em tabelas normativas (``lib.norms.search``).

Cobre: (1) busca contra os JSON reais em ``normas/`` (W250 acha perfis; aoki acha
coeficientes); (2) isolamento e insensibilidade a acento/caixa via ``tmp_path``;
(3) abstenção (termo sem correspondência => lista vazia) e ausência de efeitos
colaterais (a busca não escreve nada).
"""

import json
import pathlib

from lib.norms.search import buscar_tabela, listar_tabelas

_NORMAS = pathlib.Path(__file__).resolve().parents[2] / "normas"


# --- contra os JSON reais --------------------------------------------------
def test_buscar_w250_acha_perfis():
    hits = buscar_tabela("W250", base_dir=_NORMAS)
    assert hits, "deveria achar perfis W250*"
    assert all(h["chave"].startswith("W250") for h in hits)
    assert all(h["norma"] == "NBR8800" for h in hits)
    # os dados trazem propriedades geométricas reais (área da seção)
    assert all("area_cm2" in h["dados"] for h in hits)


def test_buscar_aoki_acha_coeficientes():
    hits = buscar_tabela("aoki", base_dir=_NORMAS)
    assert hits, "deveria achar coeficientes Aoki-Velloso"
    arquivos = {h["arquivo"] for h in hits}
    assert any("aoki" in a for a in arquivos)
    assert all(h["norma"] == "NBR6122" for h in hits)


def test_buscar_termo_inexistente_retorna_vazio():
    assert buscar_tabela("xyzzy-nao-existe", base_dir=_NORMAS) == []
    assert buscar_tabela("", base_dir=_NORMAS) == []


def test_listar_tabelas_inclui_perfis_w():
    tabelas = listar_tabelas(base_dir=_NORMAS)
    assert "NBR8800/tables/perfis_w.json" in tabelas
    assert tabelas == sorted(tabelas)


# --- isolamento, acento/caixa e ausência de efeitos colaterais -------------
def _fixture_norma(base: pathlib.Path) -> None:
    tdir = base / "NBRXXXX" / "tables"
    tdir.mkdir(parents=True)
    (tdir / "coef.json").write_text(
        json.dumps(
            {
                "meta": {"norma": "NBR XXXX", "fonte": "fonte de teste"},
                "coeficientes": {
                    "coesão alta": {"valor": 1.5},
                    "coesão baixa": {"valor": 0.5},
                },
            }
        ),
        encoding="utf-8",
    )


def test_busca_sem_acento_e_caixa(tmp_path):
    _fixture_norma(tmp_path)
    # "coesao" (sem acento, minúsculo) deve casar com "coesão alta/baixa"
    hits = buscar_tabela("COESAO", base_dir=tmp_path)
    assert len(hits) == 2
    assert {h["chave"] for h in hits} == {"coesão alta", "coesão baixa"}
    assert all(h["norma"] == "NBRXXXX" for h in hits)


def test_busca_sem_efeitos_colaterais(tmp_path):
    _fixture_norma(tmp_path)
    antes = {p: p.read_bytes() for p in tmp_path.rglob("*.json")}
    buscar_tabela("coesao", base_dir=tmp_path)
    listar_tabelas(base_dir=tmp_path)
    depois = {p: p.read_bytes() for p in tmp_path.rglob("*.json")}
    assert antes == depois  # nada foi escrito/alterado
