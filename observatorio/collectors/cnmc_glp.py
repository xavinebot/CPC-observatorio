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
# La CNMC renumeró sus conjuntos en septiembre de 2026 y los antiguos (ds_24367_1 y ds_24350_1) devuelven 404.
# Los nuevos se comprobaron uno a uno contra lo que ya teníamos guardado antes de cambiarlos: el butano coincide
# en 391 de 393 meses (las dos diferencias son meses con dos revisiones de precio, ver parse_csv) y el propano
# canalizado en los 248, sin una sola discrepancia.
DATASETS = {
    # nombre CKAN → (serie, columna que contiene, factor)
    "ds_24382_1": ("butano_es", "Venta al P", 0.01),            # c€/kg → €/kg
    "ds_24386_1": ("propano_canalizado_es", "rmino variable", 0.01),
}
FALLBACK = {
    "ds_24382_1": "https://catalogodatos.cnmc.es/dataset/7c1f4112-86b6-4cc7-9f67-469d9cd84ba2/resource/4a468073-1fec-4b73-baa9-579a73081e8a/download/ds_24382_1.csv",
    "ds_24386_1": "https://catalogodatos.cnmc.es/dataset/263f5ceb-9352-4012-b994-9fbc6027c136/resource/f333de3e-2ed6-4a5f-a2a6-1669b3c345e8/download/ds_24386_1.csv",
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
    """Un valor por mes, el que estaba vigente al final del mes.

    El butano se revisa cada dos meses, pero a veces cambia dos veces dentro del mismo mes: el fichero trae
    entonces **dos filas con la misma fecha** y distinta "Entrada en vigor". Antes se guardaban las dos y se
    quedaba una al azar según el orden del fichero, así que unos meses llevaban el precio de principios de mes y
    otros el de mediados. En septiembre de 2026 eso hacía que la web enseñara 1,4362 €/kg cuando el precio en
    vigor desde el día 15 era 1,5073.

    La regla es la que responde a la pregunta que trae al lector: **cuánto cuesta ahora**. De cada mes se guarda
    la última revisión que entró en vigor. Si el fichero no trae la columna de entrada en vigor, se queda la
    primera fila del mes, que en estos ficheros es la más reciente porque vienen ordenados del revés.
    """
    reader = csv.reader(io.StringIO(text), delimiter=";")
    header = next(reader)
    col = next((i for i, h in enumerate(header) if col_part in h), None)
    if col is None:
        raise RuntimeError(f"CNMC: no encuentro la columna '{col_part}' en {header}")
    vig = next((i for i, h in enumerate(header) if "vigor" in h.lower()), None)
    mejor: dict[str, tuple[str, float]] = {}
    for row in reader:
        if len(row) <= col or not row[0].strip():
            continue
        v = row[col].strip().replace(".", "").replace(",", ".")
        if not v:
            continue
        mes = row[0].strip()[:7]
        desde = row[vig].strip() if vig is not None and len(row) > vig else ""
        if mes in mejor and not (desde > mejor[mes][0]):
            continue
        mejor[mes] = (desde, float(v) * factor)
    return [(mes, val) for mes, (_, val) in sorted(mejor.items())]
