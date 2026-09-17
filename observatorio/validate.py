"""Validación de datos ANTES de guardarlos.

Reglas (todas configurables por serie en catalog.py):
  1. formato: fecha ISO válida y valor numérico finito;
  2. rango lógico: min_value <= valor <= max_value;
  3. fecha no futura (más de `future_days` días por delante de hoy);
  4. fecha más reciente que la última guardada (salvo en modo backfill, para cargar histórico);
     - si la fecha ya existe con el mismo valor → se ignora (duplicado);
     - si existe con valor distinto → es una revisión de la fuente: se acepta solo si el cambio es pequeño;
  5. variación máxima respecto al punto anterior (en %). En modo backfill (carga inicial del histórico oficial)
     esta regla NO se aplica: los picos históricos (2022, etc.) son reales y no hay "último valor bueno" que
     proteger; el resto de reglas sí se aplican.
Lo que no pasa va a cuarentena con su motivo; nunca se guarda ni se publica.
"""
from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field

from .catalog import Serie
from .storage import Point
from .util import is_number, parse_date, pct_change, today


@dataclass
class Rejected:
    date: str
    value: float | None
    reason: str


@dataclass
class ValidationResult:
    accepted: list[Point] = field(default_factory=list)
    rejected: list[Rejected] = field(default_factory=list)
    duplicates: int = 0
    revisions: int = 0
    backfilled: int = 0

    @property
    def ok(self) -> bool:
        return not self.rejected


def validate_points(serie: Serie, new_points: list[tuple], existing: list[Point], *,
                    backfill: bool = False, reference: dt.date | None = None) -> ValidationResult:
    """Aplica las reglas a `new_points` frente a la serie ya guardada `existing`."""
    res = ValidationResult()
    ref_today = reference or today()
    existing_map = {d: v for d, v in existing}
    last_date = max(existing_map) if existing_map else None

    # 1. formato
    clean: list[Point] = []
    for raw_d, raw_v in new_points:
        try:
            d = parse_date(str(raw_d)).isoformat()
        except (ValueError, TypeError):
            res.rejected.append(Rejected(str(raw_d), None, "fecha_invalida"))
            continue
        if not is_number(raw_v):
            res.rejected.append(Rejected(d, None, "valor_no_numerico"))
            continue
        clean.append((d, float(raw_v)))
    clean.sort()

    # 1 bis. La misma fecha dos veces con valores distintos DENTRO del mismo lote.
    #
    # Significa que la fuente es ambigua y el recolector no ha decidido: puede ser un mes con dos revisiones de
    # precio, o dos tablas distintas mezcladas en el mismo fichero. Antes se guardaba una u otra según el orden
    # en que vinieran, y eso publicó durante días un precio del butano que ya no estaba en vigor (DECISIONES §19).
    #
    # La regla es la misma que para todo lo demás: **ante la duda, no se publica**. Las dos van a cuarentena, con
    # su aviso, y se arregla el recolector para que diga cuál vale. Elegir al azar es inventarse el dato.
    vistos: dict[str, float] = {}
    conflictivas: set[str] = set()
    for d, v in clean:
        if d in vistos and abs(vistos[d] - v) > 1e-9:
            conflictivas.add(d)
        vistos.setdefault(d, v)
    if conflictivas:
        for d, v in clean:
            if d in conflictivas:
                res.rejected.append(Rejected(d, v, "fecha_duplicada_en_el_lote"))
        clean = [(d, v) for d, v in clean if d not in conflictivas]

    # el "punto anterior" para medir la variación: empieza en el último guardado antes de cada fecha
    prev_by_order = sorted(existing_map.items())

    for d, v in clean:
        # 2. rango
        if v < serie.min_value or v > serie.max_value:
            res.rejected.append(Rejected(d, v, f"fuera_de_rango[{serie.min_value}-{serie.max_value}]"))
            continue
        # 3. futuro
        if parse_date(d) > ref_today + dt.timedelta(days=serie.future_days):
            res.rejected.append(Rejected(d, v, "fecha_futura"))
            continue
        # 4. relación con lo guardado
        if d in existing_map:
            old = existing_map[d]
            if abs(old - v) < 1e-9:
                res.duplicates += 1
                continue
            if pct_change(old, v) <= serie.max_change_pct:
                res.revisions += 1
                res.accepted.append((d, v))
                existing_map[d] = v
                continue
            res.rejected.append(Rejected(d, v, f"revision_grande(antes={old})"))
            continue
        if last_date and d < last_date:
            if not backfill:
                res.rejected.append(Rejected(d, v, f"anterior_a_ultima({last_date})"))
                continue
            res.backfilled += 1
        # 5. variación vs punto anterior (el último aceptado o guardado con fecha < d)
        prev = None
        for pd_, pv in reversed(prev_by_order):
            if pd_ < d:
                prev = (pd_, pv)
                break
        if not backfill and prev is not None and pct_change(prev[1], v) > serie.max_change_pct:
            res.rejected.append(Rejected(d, v, f"salto_{pct_change(prev[1], v):.0f}%_vs_{prev[0]}"))
            continue
        res.accepted.append((d, v))
        existing_map[d] = v
        prev_by_order = sorted(existing_map.items())
    return res
