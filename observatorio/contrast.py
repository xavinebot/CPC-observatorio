"""Contraste entre fuentes: cuando el mismo dato sale en dos sitios, deben parecerse.

Cada regla compara dos series y avisa si difieren más de `tolerance`:
  - mode='level': compara el último valor de cada una (convertido a la unidad común con los factores).
  - mode='yoy':   compara la variación interanual (%) del último punto de cada una (sirve para índices con
                  bases distintas, p. ej. INE 2021=100 frente a Eurostat 2015=100).
Las reglas concretas están en RULES (abajo).
"""
from __future__ import annotations

from dataclasses import dataclass

from . import catalog, storage
from .util import parse_date, pct_change


@dataclass(frozen=True)
class Rule:
    a: str                 # serie A
    b: str                 # serie B
    tolerance: float       # % (level) o puntos porcentuales (yoy)
    mode: str = "level"
    to_common_a: float = 1.0
    to_common_b: float = 1.0
    max_days_apart: int = 45   # solo se comparan si sus últimas fechas están cerca
    label: str = ""


RULES: list[Rule] = [
    # Gasoleo de calefaccion de Francia: el Weekly Oil Bulletin (el dato que Francia envia a la Comision) frente a
    # la serie del propio ministerio frances. Fechas distintas (lunes contra viernes), asi que la tolerancia es holgada.
    Rule("gasoleo_fr", "fioul_fr_ministere", 6.0, "level", max_days_apart=10,
         label="Gasoleo FR: Boletin Petrolero de la UE frente al ministerio frances"),
    # El IPRI del vidrio (23.1) del INE y el que publica Eurostat para España (C231) son el MISMO dato.
    Rule("ipri_vidrio_es", "ipri_vidrio_es_eurostat", 1.0, "level", label="IPRI vidrio ES: INE frente a Eurostat"),
    # IPC electricidad del INE (2021=100) frente al HICP electricidad de Eurostat (2015=100): misma fuente
    # de fondo, bases distintas → se comparan las variaciones interanuales.
    Rule("ipc_electricidad_es", "hicp_electricidad_es", 4.0, "yoy", label="IPC electricidad ES: INE frente a Eurostat (variación 12 m)"),
    Rule("ipc_gas_es", "hicp_gas_es", 4.0, "yoy", label="IPC gas ES: INE frente a Eurostat (variación 12 m)"),
    Rule("ipc_comb_liquidos_es", "hicp_comb_liquidos_es", 4.0, "yoy", label="IPC combustibles líquidos ES: INE frente a Eurostat (variación 12 m)"),
]


def yoy(points: list[storage.Point]) -> tuple[str, float] | None:
    """Variación interanual (%) del último punto: busca el punto 12 meses antes (mismo mes)."""
    if len(points) < 13:
        return None
    d_last, v_last = points[-1]
    target = d_last[:4]
    prev_key = f"{int(target) - 1}{d_last[4:7]}"
    for d, v in reversed(points):
        if d[:7] == prev_key and v:
            return d_last, (v_last - v) / v * 100.0
    return None


def check_all() -> list[str]:
    alerts = []
    for r in RULES:
        try:
            catalog.get(r.a), catalog.get(r.b)
        except KeyError:
            continue
        pa, pb = storage.read_series(r.a), storage.read_series(r.b)
        if not pa or not pb:
            continue
        if abs((parse_date(pa[-1][0]) - parse_date(pb[-1][0])).days) > r.max_days_apart:
            continue
        if r.mode == "yoy":
            ya, yb = yoy(pa), yoy(pb)
            if not ya or not yb:
                continue
            diff = abs(ya[1] - yb[1])
            if diff > r.tolerance:
                alerts.append(f"{r.label or r.a + ' vs ' + r.b}: {ya[1]:+.1f}% ({ya[0]}) frente a {yb[1]:+.1f}% "
                              f"({yb[0]}), {diff:.1f} puntos de diferencia (tolerancia {r.tolerance})")
        else:
            va, vb = pa[-1][1] * r.to_common_a, pb[-1][1] * r.to_common_b
            diff = pct_change(va, vb)
            if diff > r.tolerance:
                alerts.append(f"{r.label or r.a + ' vs ' + r.b}: {va:.4g} ({pa[-1][0]}) frente a {vb:.4g} "
                              f"({pb[-1][0]}), diferencia {diff:.1f}% (tolerancia {r.tolerance}%)")
    return alerts
