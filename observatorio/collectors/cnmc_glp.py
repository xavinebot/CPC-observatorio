"""CNMC Data: precio regulado del butano envasado (desde 1994) y del GLP canalizado (desde 2006).

Los ficheros CSV (separador ';', decimales con coma, BOM UTF-8) traen todo el histórico en cada descarga. La URL
del recurso se resuelve con la API CKAN (`package_search`) para no depender de un UUID fijo; si falla, se usa la
URL conocida.
"""
from __future__ import annotations

import csv
import io

from ..util import http_get, save_raw
from .base import Collector as _Base

CKAN = "https://catalogodatos.cnmc.es/api/3/action/package_search"
DATASETS = {
    # nombre CKAN → (serie, columna que contiene, factor)
    "ds_24367_1": ("butano_es", "Venta al P", 0.01),            # c€/kg → €/kg
    "ds_24350_1": ("propano_canalizado_es", "rmino variable", 0.01),
}
FALLBACK = {
    "ds_24367_1": "https://catalogodatos.cnmc.es/dataset/4ba7704a-32fa-409b-b69b-cc0a9003b33a/resource/8aa5fbac-2375-49c5-bcbc-6a6675bead20/download/ds_24367_1.csv",
    "ds_24350_1": "https://catalogodatos.cnmc.es/dataset/f783d30e-e7bc-4040-9981-a96208ee11fd/resource/f789ec67-8c1b-4163-bf1b-1dad1bfe1868/download/ds_24350_1.csv",
}
UA = {"User-Agent": "Mozilla/5.0 (compatible; CPC-Observatorio/0.1; +https://cristalesparachimeneas.es/contacto/)"}


class Collector(_Base):
    name = "cnmc_glp"
    min_records = 380 + 240

    def resolve_csv(self, ds: str) -> str:
        try:
            r = http_get(CKAN, params={"q": f"name:{ds}", "rows": 3}, headers=UA)
            for pkg in r.json()["result"]["results"]:
                if pkg.get("name") == ds:
                    for res in pkg.get("resources", []):
                        if str(res.get("format", "")).upper() == "CSV" and res.get("url", "").endswith(".csv"):
                            return res["url"]
        except Exception:  # noqa: BLE001 — cualquier fallo → URL conocida
            pass
        return FALLBACK[ds]

    def fetch(self, *, backfill: bool = False) -> dict[str, list[tuple]]:
        out = {}
        for ds, (sid, col_part, factor) in DATASETS.items():
            url = self.resolve_csv(ds)
            text = http_get(url, headers=UA).content.decode("utf-8-sig")
            save_raw(f"cnmc_{ds}.csv", text)
            out[sid] = parse_csv(text, col_part, factor)
        return out


def parse_csv(text: str, col_part: str, factor: float) -> list[tuple]:
    reader = csv.reader(io.StringIO(text), delimiter=";")
    header = next(reader)
    col = next((i for i, h in enumerate(header) if col_part in h), None)
    if col is None:
        raise RuntimeError(f"CNMC: no encuentro la columna '{col_part}' en {header}")
    pts = []
    for row in reader:
        if len(row) <= col or not row[0].strip():
            continue
        v = row[col].strip().replace(".", "").replace(",", ".")
        if not v:
            continue
        pts.append((row[0].strip()[:7], float(v) * factor))
    return pts
