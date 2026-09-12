"""INE (API Tempus3, JSON): IPC por subclases (energía del hogar) e IPRI por ramas (industria).

Gotcha comprobado: el servidor corta la conexión si el User-Agent no parece un navegador. Cada serie se pide
completa (`?date=20000101:20991231`), así que la misma llamada sirve para la carga inicial y la actualización.
Si el INE cambia el código de una serie (pasó en 2026 al cambiar la clasificación), la descarga vuelve vacía y
el recolector avisa: hay que actualizar el código en catalog_series.py.
"""
from __future__ import annotations

import re
import time

from .. import catalog
from ..util import http_get, save_raw
from .base import Collector as _Base

API = "https://servicios.ine.es/wstempus/js/ES/DATOS_SERIE/"
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) CPC-Observatorio/0.1 (+https://cristalesparachimeneas.es/contacto/)"}


def fetch_serie(code: str) -> list[tuple]:
    r = http_get(API + code, params={"date": "20000101:20991231"}, headers=UA)
    save_raw(f"ine_{code}.json", r.text)
    d = r.json()
    if isinstance(d, list):
        d = d[0] if d else {}
    data = d.get("Data") or []
    pts = []
    for item in data:
        if item.get("Secreto") or item.get("Valor") is None:
            continue
        y, m = item.get("Anyo"), item.get("FK_Periodo")
        if not y or not m or m > 12:
            continue
        pts.append((f"{y}-{int(m):02d}-01", float(item["Valor"])))
    if not pts:
        raise RuntimeError(f"INE: la serie {code} no devuelve datos (¿ha cambiado el código?)")
    return pts


class _Ine(_Base):
    prefix = ""

    def codes(self) -> dict[str, str]:
        out = {}
        for s in catalog.by_collector(self.name):
            m = re.search(r"\(serie (IP[RC]\d+)\)", s.notes)
            if m:
                out[s.id] = m.group(1)
        return out

    def fetch(self, *, backfill: bool = False) -> dict[str, list[tuple]]:
        out = {}
        for sid, code in self.codes().items():
            out[sid] = fetch_serie(code)
            time.sleep(0.5)
        return out


class Ipc(_Ine):
    name = "ine_ipc"
    min_records = 3 * 200


class Ipri(_Ine):
    name = "ine_ipri"
    min_records = 7 * 200


COLLECTORS = {"ine_ipc": Ipc, "ine_ipri": Ipri}
Collector = Ipc
