"""Registro público de correcciones: solo cambios que se ven, y solo series publicadas (no toca la red)."""
import json

from observatorio import catalog, config, correcciones
from observatorio.validate import validate_points

from test_validate import EXISTING, REF, serie


def _aislar(tmp_path, monkeypatch):
    monkeypatch.setattr(correcciones, "FICHERO", tmp_path / "correcciones.json")
    (tmp_path / "pub").mkdir()
    monkeypatch.setattr(config, "PUBLISHED_DIR", tmp_path / "pub")


def test_la_validacion_anota_la_revision_con_antes_y_despues():
    r = validate_points(serie(), [("2026-09-07", 1.06)], EXISTING, reference=REF)
    assert r.revised == [("2026-09-07", 1.05, 1.06)]


def test_un_cambio_que_no_se_ve_no_es_una_correccion(tmp_path, monkeypatch):
    _aislar(tmp_path, monkeypatch)
    sid = catalog.all_series()[0].id
    dec = catalog.get(sid).decimals
    assert correcciones.registrar(sid, [("2026-07-01", 0.35266, 0.35266 + 10 ** -(dec + 2))], "revision_fuente") == 0
    assert not (tmp_path / "correcciones.json").exists()


def test_se_registra_y_se_publica_solo_lo_publicable(tmp_path, monkeypatch):
    _aislar(tmp_path, monkeypatch)
    visible = next(s for s in catalog.all_series() if s.publishable and not s.hidden)
    oculta = next((s for s in catalog.all_series() if s.hidden or not s.publishable), None)
    assert correcciones.registrar(visible.id, [("2026-09-07", 1.05, 1.10)], "revision_fuente") == 1
    if oculta:
        correcciones.registrar(oculta.id, [("2026-09-07", 1.05, 1.10)], "revision_fuente")
    reg = json.loads((tmp_path / "correcciones.json").read_text(encoding="utf-8"))
    assert reg["desde"] == "2026-11-21"
    assert reg["correcciones"][0]["serie"] == visible.id
    assert reg["correcciones"][0]["antes"] == round(1.05, visible.decimals)
    correcciones.publicar()
    pub = json.loads((tmp_path / "pub" / "correcciones.json").read_text(encoding="utf-8"))
    assert [c["serie"] for c in pub["correcciones"]] == [visible.id]


def test_sin_registro_se_publica_vacio_con_su_fecha_de_inicio(tmp_path, monkeypatch):
    _aislar(tmp_path, monkeypatch)
    correcciones.publicar()
    pub = json.loads((tmp_path / "pub" / "correcciones.json").read_text(encoding="utf-8"))
    assert pub == {"desde": "2026-11-21", "correcciones": []}
