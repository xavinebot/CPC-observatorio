"""Contraste entre fuentes: cuando el mismo dato sale en dos sitios, deben parecerse.

Cada regla compara dos series y avisa si difieren más de `tolerance`:
  - mode='level': compara el último valor de cada una (convertido a la unidad común con los factores).
  - mode='yoy':   compara la variación interanual (%) del último mes que está en LAS DOS series (sirve
                  para índices con bases distintas, p. ej. INE 2021=100 frente a Eurostat 2015=100). Tiene que
                  ser el mismo mes: el INE publica antes que Eurostat y comparar agosto con julio da falsas
                  alarmas.
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


def yoy_de(points: list[storage.Point], mes: str) -> float | None:
    """Variación interanual (%) de un mes concreto ('AAAA-MM'), contra el mismo mes del año anterior."""
    d = {p[0][:7]: p[1] for p in points}
    previo = f"{int(mes[:4]) - 1}{mes[4:7]}"
    if mes in d and d.get(previo):
        return (d[mes] - d[previo]) / d[previo] * 100.0
    return None


def ultimo_mes_comun(pa: list[storage.Point], pb: list[storage.Point]) -> str | None:
    """El mes más reciente que está en las dos series."""
    comunes = {p[0][:7] for p in pa} & {p[0][:7] for p in pb}
    return max(comunes) if comunes else None


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
        if r.mode == "yoy":
            # Se comparan SIEMPRE el mismo mes en las dos series. Comparando el último punto de cada una salían
            # falsas alarmas: el INE publica antes que Eurostat, así que se estaba comparando la variación de
            # agosto con la de julio. En una serie movida como los combustibles líquidos, dos meses seguidos se
            # llevan quince puntos sin que pase nada, y el aviso enseña a no hacer caso de los avisos.
            mes = ultimo_mes_comun(pa, pb)
            if not mes:
                continue
            ya, yb = yoy_de(pa, mes), yoy_de(pb, mes)
            if ya is None or yb is None:
                continue
            diff = abs(ya - yb)
            if diff > r.tolerance:
                alerts.append(f"{r.label or r.a + ' vs ' + r.b} en {mes}: {ya:+.1f}% frente a {yb:+.1f}%, "
                              f"{diff:.1f} puntos de diferencia (tolerancia {r.tolerance})")
        else:
            if abs((parse_date(pa[-1][0]) - parse_date(pb[-1][0])).days) > r.max_days_apart:
                continue
            va, vb = pa[-1][1] * r.to_common_a, pb[-1][1] * r.to_common_b
            diff = pct_change(va, vb)
            if diff > r.tolerance:
                alerts.append(f"{r.label or r.a + ' vs ' + r.b}: {va:.4g} ({pa[-1][0]}) frente a {vb:.4g} "
                              f"({pb[-1][0]}), diferencia {diff:.1f}% (tolerancia {r.tolerance}%)")
    return alerts
