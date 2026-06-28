"""Testes do sistema de memória por projeto (Fase 4).

TDD: usar ``tmp_path`` como base_dir para não tocar em ``memory/projects/`` real.
Timestamps são sempre fornecidos pelo chamador (valores fixos), nunca lidos do relógio.
"""

import json

import pytest

from lib.projects.store import (
    ProjectRecord,
    add_calculo,
    list_projects,
    load_project,
    save_project,
)

FIXED_TS = "2026-01-01T00:00:00"


def _record(project_id: str = "edificio-alfa", **kwargs) -> ProjectRecord:
    base = dict(
        project_id=project_id,
        nome="Edifício Alfa",
        responsavel="Eng. Fulano",
        criado_em=FIXED_TS,
        calculos=[],
        metadados={"cidade": "Curitiba"},
    )
    base.update(kwargs)
    return ProjectRecord(**base)


# --- modelo ----------------------------------------------------------------
def test_record_defaults():
    rec = ProjectRecord(project_id="p1", nome="P1", responsavel=None, criado_em=None)
    assert rec.calculos == []
    assert rec.metadados == {}


# --- save / load roundtrip -------------------------------------------------
def test_save_returns_expected_path(tmp_path):
    rec = _record()
    path = save_project(rec, base_dir=str(tmp_path))
    assert path == str(tmp_path / "edificio-alfa.json")
    assert (tmp_path / "edificio-alfa.json").is_file()


def test_save_creates_missing_dir(tmp_path):
    target = tmp_path / "nao" / "existe"
    rec = _record()
    path = save_project(rec, base_dir=str(target))
    assert (target / "edificio-alfa.json").is_file()
    assert path == str(target / "edificio-alfa.json")


def test_save_load_roundtrip(tmp_path):
    rec = _record(calculos=[{"tipo": "viga", "as_cm2": 5.3}])
    save_project(rec, base_dir=str(tmp_path))
    loaded = load_project("edificio-alfa", base_dir=str(tmp_path))
    assert loaded == rec
    assert loaded.metadados == {"cidade": "Curitiba"}
    assert loaded.calculos[0]["as_cm2"] == 5.3


def test_saved_file_is_valid_json(tmp_path):
    save_project(_record(), base_dir=str(tmp_path))
    data = json.loads((tmp_path / "edificio-alfa.json").read_text(encoding="utf-8"))
    assert data["project_id"] == "edificio-alfa"
    assert data["nome"] == "Edifício Alfa"


# --- list_projects ---------------------------------------------------------
def test_list_projects_empty_when_no_dir(tmp_path):
    assert list_projects(base_dir=str(tmp_path / "vazio")) == []


def test_list_projects_returns_ids_sorted(tmp_path):
    save_project(_record("beta"), base_dir=str(tmp_path))
    save_project(_record("alfa"), base_dir=str(tmp_path))
    save_project(_record("gama"), base_dir=str(tmp_path))
    assert list_projects(base_dir=str(tmp_path)) == ["alfa", "beta", "gama"]


def test_list_projects_ignores_non_json(tmp_path):
    save_project(_record("alfa"), base_dir=str(tmp_path))
    (tmp_path / "leiame.txt").write_text("ignore", encoding="utf-8")
    assert list_projects(base_dir=str(tmp_path)) == ["alfa"]


# --- add_calculo -----------------------------------------------------------
def test_add_calculo_accumulates(tmp_path):
    save_project(_record(), base_dir=str(tmp_path))
    r1 = add_calculo("edificio-alfa", {"tipo": "viga", "id": 1}, base_dir=str(tmp_path))
    assert len(r1.calculos) == 1
    r2 = add_calculo("edificio-alfa", {"tipo": "pilar", "id": 2}, base_dir=str(tmp_path))
    assert len(r2.calculos) == 2
    # persistido em disco
    reloaded = load_project("edificio-alfa", base_dir=str(tmp_path))
    assert len(reloaded.calculos) == 2
    assert reloaded.calculos[0]["tipo"] == "viga"
    assert reloaded.calculos[1]["tipo"] == "pilar"


def test_add_calculo_is_idempotent_for_same_bundle(tmp_path):
    save_project(_record(), base_dir=str(tmp_path))
    bundle = {"tipo": "viga", "id": 7}
    add_calculo("edificio-alfa", bundle, base_dir=str(tmp_path))
    r2 = add_calculo("edificio-alfa", bundle, base_dir=str(tmp_path))
    assert len(r2.calculos) == 1


def test_add_calculo_accepts_optional_timestamp(tmp_path):
    save_project(_record(), base_dir=str(tmp_path))
    rec = add_calculo(
        "edificio-alfa", {"tipo": "viga"}, base_dir=str(tmp_path), timestamp=FIXED_TS
    )
    assert rec.calculos[0]["registrado_em"] == FIXED_TS


def test_add_calculo_missing_project_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        add_calculo("inexistente", {"tipo": "viga"}, base_dir=str(tmp_path))


# --- erros / abstenção -----------------------------------------------------
def test_load_missing_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_project("nao-existe", base_dir=str(tmp_path))


@pytest.mark.parametrize(
    "bad_id",
    ["../escape", "a/b", "..", "", "   ", "with\\slash", "tem/barra.json"],
)
def test_unsafe_project_id_rejected_on_save(tmp_path, bad_id):
    rec = _record(bad_id)
    with pytest.raises(ValueError):
        save_project(rec, base_dir=str(tmp_path))


@pytest.mark.parametrize("bad_id", ["../escape", "a/b", "..", ""])
def test_unsafe_project_id_rejected_on_load(tmp_path, bad_id):
    with pytest.raises(ValueError):
        load_project(bad_id, base_dir=str(tmp_path))


def test_safe_project_id_with_dots_and_dashes_ok(tmp_path):
    rec = _record("proj_2026.v1-final")
    path = save_project(rec, base_dir=str(tmp_path))
    assert path == str(tmp_path / "proj_2026.v1-final.json")
    assert load_project("proj_2026.v1-final", base_dir=str(tmp_path)) == rec
