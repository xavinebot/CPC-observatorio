"""Weekly Oil Bulletin (Comisión Europea): gasóleo de calefacción semanal por país, con y sin impuestos.

Descarga el XLSX "Prices History" completo (≈4 MB) cada vez: trae toda la serie desde 2005, así que la misma
descarga sirve para la carga inicial y para la actualización semanal. La URL del fichero cambia de vez en
cuando: se localiza en la página del boletín buscando el enlace cuyo nombre contiene "Prices_History".
"""
from __future__ import annotations

import io
import re
from urllib.parse import urljoin

import openpyxl

from .. import catalog
from ..util import http_get, save_raw
from .base import Collector as _Base

PAGE = "https://energy.ec.europa.eu/data-and-analysis/weekly-oil-bulletin_en"
FALLBACK = ("https://energy.ec.europa.eu/document/download/906e60ca-8b6a-44e7-8589-652854d2fd3f_en"
            "?filename=Weekly_Oil_Bulletin_Prices_History_maticni_4web.xlsx")


class Collector(_Base):
    name = "wob"
    min_records = 6 * 2 * 500  # 6 países × 2 variantes × >500 semanas

    def find_history_url(self) -> str:
        html = http_get(PAGE).text
        m = re.search(r'href="([^"]*document/download/[^"]*Prices_History[^"]*)"', html)
        if m:
            return urljoin(PAGE, m.group(1).replace("&amp;", "&"))
        return FALLBACK

    def fetch(self, *, backfill: bool = False) -> dict[str, list[tuple]]:
        url = self.find_history_url()
        content = http_get(url).content
        save_raw("wob_history.xlsx", content)
        return parse_history(content)


def parse_history(content: bytes) -> dict[str, list[tuple]]:
    wb = openpyxl.load_workbook(io.BytesIO(content), read_only=True, data_only=True)
    out: dict[str, list[tuple]] = {}
    for sheet, suffix, key in (("Prices with taxes", "", "with_tax"), ("Prices wo taxes", "sin_imp_", "wo_tax")):
        ws = wb[sheet]
        rows = ws.iter_rows(values_only=True)
        header = next(rows)
        cols = {}
        for i, h in enumerate(header):
            h = str(h or "")
            m = re.match(rf"([A-Z]{{2}})_price_{key}_heating_oil$", h)
            if m:
                cols[m.group(1)] = i
        next(rows); next(rows)  # nombre del producto y unidad
        for r in rows:
            d = r[0]
            if not hasattr(d, "isoformat"):
                continue  # filas de notas al final
            date = d.date().isoformat() if hasattr(d, "date") else d.isoformat()
            for cc, i in cols.items():
                sid = f"gasoleo_{suffix}{cc.lower()}"
                try:
                    catalog.get(sid)
                except KeyError:
                    continue
                v = r[i]
                if v is None or v == "":
                    continue
                try:
                    out.setdefault(sid, []).append((date, float(v) / 1000.0))  # €/1000 l → €/l
                except (TypeError, ValueError):
                    continue
    return out
