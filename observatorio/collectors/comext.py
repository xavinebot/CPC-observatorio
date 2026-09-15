"""Eurostat Comext: precio medio al que entra en la UE cada materia prima, en euros por kilo.

Comext publica el comercio exterior mes a mes por código de producto. Dividiendo el valor declarado en euros
entre la cantidad en kilos sale un **valor unitario de importación**: lo que de media ha costado meter ese
material en la Unión Europea ese mes.

OJO, y hay que decirlo en la web: **no es una cotización**. Mezcla grados, orígenes y contratos, y en los
productos baratos y de mucho volumen (la arena, la sosa) el flete pesa más que el material, así que el mes suelto
se mueve mucho. Lo que tiene sentido mirar es la tendencia, no el escalón de un mes.

Dos trampas de esta API, que no es la misma que la del resto de Eurostat:
  - vive en /api/comext/dissemination/... y no en /api/dissemination/...
  - el periodo se escribe "2026-01"; con "2026M01" devuelve 400.
"""
from __future__ import annotations

from ..util import http_get, save_raw
from .base import Collector as _Base

API = "https://ec.europa.eu/eurostat/api/comext/dissemination/statistics/1.0/data/DS-045409"

# código de la nomenclatura combinada -> serie
PRODUCTOS = {
    "28369100": "litio_eu",
    "28362000": "sosa_eu",
    "25051000": "silice_eu",
    "28182000": "alumina_eu",
    "28230000": "titanio_eu",
    "28256000": "circonio_eu",
}
DESDE = "2004-01"          # antes de 2004 la UE tenía otra composición y el dato no es comparable


class Collector(_Base):
    name = "comext"
    min_records = 6 * 150

    def fetch(self, *, backfill: bool = False) -> dict[str, list[tuple]]:
        out: dict[str, list[tuple]] = {}
        for codigo, serie in PRODUCTOS.items():
            out[serie] = self._producto(codigo, serie)
        return out

    def _producto(self, codigo: str, serie: str) -> list[tuple]:
        r = http_get(API, params=[
            ("format", "JSON"), ("lang", "EN"), ("product", codigo), ("flow", "1"), ("freq", "M"),
            ("reporter", "EU27_2020"), ("partner", "EXT_EU27_2020"), ("sinceTimePeriod", DESDE),
        ])
        d = r.json()
        if "value" not in d:
            raise RuntimeError(f"Comext {codigo}: respuesta sin datos: {str(d)[:200]}")
        save_raw(f"comext_{codigo}.json", r.text)
        return precios(d)


def precios(d: dict) -> list[tuple]:
    """Del JSON-stat de Comext a [(fecha, €/kg)], saltándose los meses sin valor o sin cantidad."""
    ids, sizes = d["id"], d["size"]
    idx = {k: d["dimension"][k]["category"]["index"] for k in ids}
    inv = {k: {pos: cod for cod, pos in idx[k].items()} for k in ids}
    strides = [1] * len(sizes)
    for i in range(len(sizes) - 2, -1, -1):
        strides[i] = strides[i + 1] * sizes[i + 1]

    por_mes: dict[str, dict[str, float]] = {}
    for plano, valor in d["value"].items():
        resto = int(plano)
        clave = {}
        for i, nombre in enumerate(ids):
            clave[nombre] = inv[nombre][resto // strides[i] % sizes[i]]
        por_mes.setdefault(clave["time"], {})[clave["indicators"]] = float(valor)

    puntos = []
    for mes in sorted(por_mes):
        euros = por_mes[mes].get("VALUE_IN_EUROS")
        cien_kg = por_mes[mes].get("QUANTITY_IN_100KG")
        if not euros or not cien_kg:
            continue                      # un mes sin cantidad declarada no da precio: se salta, no se inventa
        puntos.append((f"{mes}-01", round(euros / (cien_kg * 100.0), 4)))
    return puntos
