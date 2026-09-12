"""Tests de la validación y la cuarentena (no tocan la red)."""
import datetime as dt

import pytest

from observatorio import catalog, config, quarantine, storage
from observatorio.catalog import Serie, Source
from observatorio.validate import validate_points

SRC = Source(name="Fuente de prueba", url="https://example.org", license="CC BY 4.0",
             license_url="https://creativecommons.org/licenses/by/4.0/", attribution="Fuente de prueba")


def serie(**kw) -> Serie:
    base = dict(id="test_serie", name={"es": "Prueba"}, country="ES", group="hogar", fuel="gasoleo",
                unit="EUR/l", source=SRC, collector="test", native_freq="W", expected_every_days=7,
                stale_after_days=21, min_value=0.3, max_value=3.0, max_change_pct=15, kwh_per_unit=10)
    base.update(kw)
    return Serie(**base)


REF = dt.date(2026, 9, 15)
EXISTING = [("2026-08-24", 1.00), ("2026-08-31", 1.02), ("2026-09-07", 1.05)]


def test_acepta_dato_normal():
    r = validate_points(serie(), [("2026-09-14", 1.07)], EXISTING, reference=REF)
    assert r.accepted == [("2026-09-14", 1.07)] and not r.rejected


def test_formato_invalido():
    r = validate_points(serie(), [("no-es-fecha", 1.0), ("2026-09-14", "abc"), ("2026-09-15", float("nan"))],
                        EXISTING, reference=REF)
    assert not r.accepted
    assert {x.reason for x in r.rejected} == {"fecha_invalida", "valor_no_numerico"}


def test_fuera_de_rango():
    r = validate_points(serie(), [("2026-09-14", 15.0), ("2026-09-15", 0.05)], EXISTING, reference=REF)
    assert not r.accepted and all("fuera_de_rango" in x.reason for x in r.rejected)


def test_salto_grande_va_a_cuarentena():
    r = validate_points(serie(), [("2026-09-14", 1.40)], EXISTING, reference=REF)  # +33 % > 15 %
    assert not r.accepted and r.rejected[0].reason.startswith("salto_")


def test_fecha_futura():
    r = validate_points(serie(), [("2026-09-25", 1.05)], EXISTING, reference=REF)
    assert r.rejected[0].reason == "fecha_futura"


def test_duplicado_se_ignora_y_revision_pequena_se_acepta():
    r = validate_points(serie(), [("2026-09-07", 1.05), ("2026-08-31", 1.03)], EXISTING, reference=REF)
    assert r.duplicates == 1 and r.revisions == 1 and r.accepted == [("2026-08-31", 1.03)]


def test_revision_grande_se_rechaza():
    r = validate_points(serie(), [("2026-09-07", 1.50)], EXISTING, reference=REF)
    assert r.rejected[0].reason.startswith("revision_grande")


def test_anterior_a_ultima_solo_con_backfill():
    r = validate_points(serie(), [("2026-08-17", 0.99)], EXISTING, reference=REF)
    assert r.rejected[0].reason.startswith("anterior_a_ultima")
    r2 = validate_points(serie(), [("2026-08-17", 0.99)], EXISTING, reference=REF, backfill=True)
    assert r2.accepted == [("2026-08-17", 0.99)] and r2.backfilled == 1


def test_carga_historica_acepta_saltos_pero_no_rangos():
    pts = [("2026-01-05", 1.0), ("2026-01-12", 1.05), ("2026-01-19", 2.0), ("2026-01-26", 9.0)]
    r = validate_points(serie(), pts, [], reference=REF, backfill=True)
    # en backfill el salto del 19 (+90 %) se acepta (histórico oficial); el 26 está fuera de rango y no
    assert [d for d, _ in r.accepted] == ["2026-01-05", "2026-01-12", "2026-01-19"]
    assert r.rejected[0].date == "2026-01-26" and "fuera_de_rango" in r.rejected[0].reason


def test_sin_backfill_detecta_salto_intermedio():
    pts = [("2026-01-05", 1.0), ("2026-01-12", 1.05), ("2026-01-19", 2.0), ("2026-01-26", 1.06)]
    r = validate_points(serie(), pts, [], reference=REF)
    assert [d for d, _ in r.accepted] == ["2026-01-05", "2026-01-12", "2026-01-26"]
    assert r.rejected[0].date == "2026-01-19"


@pytest.fixture
def sandbox(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DATA", tmp_path)
    monkeypatch.setattr(config, "SERIES_DIR", tmp_path / "series")
    monkeypatch.setattr(config, "QUARANTINE_DIR", tmp_path / "quarantine")
    monkeypatch.setattr(config, "PUBLISHED_DIR", tmp_path / "published")
    monkeypatch.setattr(config, "RAW_DIR", tmp_path / "raw")
    monkeypatch.setattr(config, "STATE_FILE", tmp_path / "state.json")
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.delenv("TELEGRAM_CHAT_ID", raising=False)
    monkeypatch.setattr(config, "ENV_FILES", [])
    s = serie()
    catalog._REGISTRY[s.id] = s
    yield tmp_path
    catalog._REGISTRY.pop(s.id, None)


def test_cuarentena_no_publica_y_aprobar_guarda(sandbox):
    storage.write_series("test_serie", EXISTING)
    r = validate_points(serie(), [("2026-09-14", 1.40)], EXISTING, reference=REF)
    quarantine.add("test_serie", r.rejected)
    assert storage.last_point("test_serie") == ("2026-09-07", 1.05)   # la web sigue con el último bueno
    assert len(quarantine.pending()) == 1
    assert quarantine.approve("test_serie") == 1
    assert storage.last_point("test_serie") == ("2026-09-14", 1.4)
    assert quarantine.pending() == []


def test_descartar_vacia_la_cuarentena(sandbox):
    r = validate_points(serie(), [("2026-09-14", 1.40)], EXISTING, reference=REF)
    quarantine.add("test_serie", r.rejected)
    assert quarantine.discard("test_serie") == 1 and quarantine.pending() == []


def test_csv_ida_y_vuelta(sandbox):
    storage.write_series("test_serie", [("2026-01-01", 1.23456), ("2025-12-01", 0.5)])
    assert storage.read_series("test_serie") == [("2025-12-01", 0.5), ("2026-01-01", 1.2346)]
