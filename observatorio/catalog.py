"""Catálogo de series: TODO lo que define una serie está aquí (unidad, país, fuente, licencia, reglas de validación).

Convenciones:
  - `country`: ES, FR, IT, DE, PT, AT, EU.
  - `group`: 'hogar' (combustibles de calefacción) | 'industria' (índices para profesionales).
  - `unit`: unidad tal como la publica la fuente. `kwh_per_unit`: cuántos kWh de energía contiene una unidad
    (para pasar a €/kWh: precio / kwh_per_unit). None si no aplica (índices).
  - `native_freq`: D diario, W semanal, M mensual, Q trimestral, S semestral, A anual.
  - `expected_every_days`: cada cuántos días debería llegar un dato nuevo; `stale_after_days`: a partir de
    cuántos días sin dato nuevo se avisa.
  - `max_change_pct`: variación máxima aceptada entre un punto y el anterior; más → cuarentena.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Source:
    name: str
    url: str            # página de la fuente (para el enlace visible)
    license: str        # nombre de la licencia / condición de reutilización
    license_url: str
    attribution: str    # texto de cita que exige la fuente


@dataclass(frozen=True)
class Serie:
    id: str
    name: dict          # {'es': ..., 'fr': ..., 'it': ..., 'de': ..., 'pt': ...}
    country: str
    group: str
    fuel: str           # gasoleo | pellet | lena | electricidad | gas | butano | propano | astilla | hueso | indice
    unit: str
    source: Source
    collector: str
    native_freq: str
    expected_every_days: int
    stale_after_days: int
    min_value: float
    max_value: float
    max_change_pct: float
    kwh_per_unit: float | None = None
    decimals: int = 4
    future_days: int = 1
    taxes_included: bool | None = None
    notes: str = ""
    redistributable: bool = True   # si la licencia permite ofrecer el CSV descargable
    publishable: bool = True       # False = recolectada pero NO se publica (p. ej. falta autorización escrita)
    hidden: bool = False           # True = solo para contraste interno; no aparece en la web


_REGISTRY: dict[str, Serie] = {}


def register(serie: Serie) -> Serie:
    if serie.id in _REGISTRY:
        raise ValueError(f"serie duplicada: {serie.id}")
    _REGISTRY[serie.id] = serie
    return serie


def get(serie_id: str) -> Serie:
    return _REGISTRY[serie_id]


def all_series() -> list[Serie]:
    return list(_REGISTRY.values())


def by_collector(collector: str) -> list[Serie]:
    return [s for s in _REGISTRY.values() if s.collector == collector]


# Las definiciones concretas viven en catalog_series.py (se importa al final para poblar el registro).
from . import catalog_series  # noqa: E402,F401
