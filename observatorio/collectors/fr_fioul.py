"""Francia, Ministère de la Transition écologique: precio semanal del fioul domestique (2.000-4.999 l) TTC.

Solo sirve para CONTRASTAR el Weekly Oil Bulletin (serie oculta). XLSX "Prix HTT et TTC depuis janvier 2020"
(licencia etalab-2.0); el enlace se localiza en la página porque el nombre del fichero lleva sufijos variables.
"""
from __future__ import annotations

import io
import re
from urllib.parse import urljoin

import openpyxl

from ..util import http_get, save_raw
from .base import Collector as _Base

PAGE = "https://www.ecologie.gouv.fr/prix-des-produits-petroliers"
UA = {"User-Agent": "Mozilla/5.0 (compatible; CPC-Observatorio/0.1; +https://cristalesparachimeneas.es/contacto/)"}


class Collector(_Base):
    name = "fr_fioul"
    min_records = 100

    def fetch(self, *, backfill: bool = False) -> dict[str, list[tuple]]:
        html = http_get(PAGE, headers=UA).text
        m = re.search(r'href="([^"]*Prix[^"]*HTT[^"]*TTC[^"]*\.xlsx)"', html, re.I)
        if not m:
            raise RuntimeError("fioul FR: no encuentro el enlace al XLSX de precios")
        url = urljoin(PAGE, m.group(1).replace("&amp;", "&"))
        content = http_get(url, headers=UA).content
        save_raw("fr_fioul.xlsx", content)
        return {"fioul_fr_ministere": parse(content)}


def parse(content: bytes) -> list[tuple]:
    wb = openpyxl.load_workbook(io.BytesIO(content), read_only=True, data_only=True)
    ws = wb["Combustibles"]
    rows = ws.iter_rows(values_only=True)
    col = None
    for r in rows:
        if r and r[0] == "Date":
            # primera columna TTC de fioul domestique 2.000-4.999 l (la HTT va antes)
            idx = [i for i, h in enumerate(r) if h and "2 000" in str(h)]
            if len(idx) >= 2:
                col = idx[1]
            break
    if col is None:
        raise RuntimeError("fioul FR: cabecera no reconocida")
    # La hoja lleva TRES tablas apiladas: las lecturas semanales, debajo "MOYENNES MENSUELLES" y al final las
    # anuales. Leyendolas todas se mezclaban lecturas semanales con medias mensuales en la misma serie, y en las
    # once semanas que cayeron en dia 1 salian dos valores distintos para la misma fecha. Se corta en el rotulo.
    pts = []
    for r in rows:
        if r and isinstance(r[0], str) and "MOYENNE" in r[0].upper():
            break
        d = r[0]
        if hasattr(d, "date") and isinstance(r[col], (int, float)):
            pts.append((d.date().isoformat(), float(r[col])))
    return pts
