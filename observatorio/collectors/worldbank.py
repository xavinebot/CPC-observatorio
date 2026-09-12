"""Banco Mundial, Commodity Price Data (Pink Sheet): precios mensuales de materias primas en USD desde 1960.

El enlace del XLSX cambia cada año (lleva un hash): se localiza en la página de Commodity Markets; si no aparece,
se usa el último conocido.
"""
from __future__ import annotations

import io
import re

import openpyxl

from ..util import http_get, save_raw
from .base import Collector as _Base

PAGE = "https://www.worldbank.org/en/research/commodity-markets"
FALLBACK = "https://thedocs.worldbank.org/en/doc/74e8be41ceb20fa0da750cda2f6b9e4e-0050012026/related/CMO-Historical-Data-Monthly.xlsx"
COLUMNS = {"gas_ttf_eu": "Natural gas, Europe", "mineral_hierro": "Iron ore, cfr spot",
           "brent": "Crude oil, Brent", "cobre": "Copper"}
UA = {"User-Agent": "Mozilla/5.0 (compatible; CPC-Observatorio/0.1; +https://cristalesparachimeneas.es/contacto/)"}


class Collector(_Base):
    name = "worldbank"
    min_records = 4 * 300

    def find_url(self) -> str:
        try:
            html = http_get(PAGE, headers=UA).text
            m = re.search(r'https://thedocs\.worldbank\.org/[^"\']*CMO-Historical-Data-Monthly\.xlsx', html)
            if m:
                return m.group(0)
        except Exception:  # noqa: BLE001
            pass
        return FALLBACK

    def fetch(self, *, backfill: bool = False) -> dict[str, list[tuple]]:
        content = http_get(self.find_url(), headers=UA).content
        save_raw("worldbank_pinksheet.xlsx", content)
        return parse(content)


def parse(content: bytes) -> dict[str, list[tuple]]:
    wb = openpyxl.load_workbook(io.BytesIO(content), read_only=True, data_only=True)
    ws = wb["Monthly Prices"]
    rows = ws.iter_rows(values_only=True)
    names = None
    for r in rows:
        if r and r[1] and str(r[1]).startswith("Crude oil"):
            names = [str(x).strip() if x else "" for x in r]
            break
    if not names:
        raise RuntimeError("Pink Sheet: no encuentro la fila de nombres de series")
    next(rows)  # unidades
    idx = {}
    for sid, col in COLUMNS.items():
        try:
            idx[sid] = names.index(col)
        except ValueError:
            raise RuntimeError(f"Pink Sheet: falta la columna '{col}'")
    out = {sid: [] for sid in COLUMNS}
    for r in rows:
        key = r[0]
        m = re.match(r"^(\d{4})M(\d{2})$", str(key or ""))
        if not m:
            continue
        date = f"{m.group(1)}-{m.group(2)}-01"
        for sid, i in idx.items():
            v = r[i]
            if isinstance(v, (int, float)):
                out[sid].append((date, float(v)))
    return out
