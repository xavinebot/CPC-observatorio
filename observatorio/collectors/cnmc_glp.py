"""CNMC Data: precio regulado del butano envasado (desde 1994) y del GLP canalizado (desde 2006).

Los ficheros CSV (separador ';', decimales con coma, BOM UTF-8) traen todo el histórico en cada descarga.

**Los conjuntos se buscan por su TÍTULO, no por su identificador.** La CNMC renumera: `ds_24367_1` murió el 16 de
septiembre de 2026, y `ds_24382_1`, que lo sustituyó, murió el 6 de octubre —tres semanas— mientras que los del
GLP canalizado conservaron el suyo. El identificador no es estable y el título sí, así que fijarse en el número
es fijarse justo en lo que cambia. La última dirección que funcionó se guarda en `data/cnmc_urls.json` y solo se
usa si el catálogo no responde: así el apaño se cura solo en vez de pudrirse dentro del código.
"""
from __future__ import annotations

import csv
import io
import json

from .. import config
from ..util import http_get, save_raw
from .base import Collector as _Base

CKAN = "https://catalogodatos.cnmc.es/api/3/action/package_search"
CACHE_URLS = config.DATA / "cnmc_urls.json"

# título exacto en el catálogo → (serie, columna que contiene, factor)
DATASETS = {
    "Estadística GLP - Precio GLP envasado regulado": ("butano_es", "Venta al P", 0.01),   # c€/kg → €/kg
    "Precio GLP Canalizado (antes de impuestos)": ("propano_canalizado_es", "rmino variable", 0.01),
}
UA = {"User-Agent": "Mozilla/5.0 (compatible; CPC-Observatorio/0.1; +https://cristalesparachimeneas.es/contacto/)"}


def _norm(s: str) -> str:
    return " ".join(str(s).split()).casefold()


def _urls_recordadas() -> dict:
    try:
        return json.loads(CACHE_URLS.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001 — sin fichero todavía o ilegible: se resuelve por el catálogo
        return {}


class Collector(_Base):
    name = "cnmc_glp"
    min_records = 380 + 240

    def resolve_csv(self, titulo: str) -> tuple[str, bool]:
        """Dirección del CSV de ese conjunto. Devuelve (url, la_dio_el_catálogo)."""
        try:
            r = http_get(CKAN, params={"q": f'title:"{titulo}"', "rows": 10}, headers=UA)
            for pkg in r.json()["result"]["results"]:
                # Comparación exacta: «Estadística GLP - Precio GLP envasado regulado» NO es «Precio GLP envasado
                # regulado de Venta al Público». Se parecen, coexisten y son conjuntos distintos.
                if _norm(pkg.get("title", "")) != _norm(titulo):
                    continue
                for res in pkg.get("resources", []):
                    if str(res.get("format", "")).upper() == "CSV" and str(res.get("url", "")).endswith(".csv"):
                        return res["url"], True
        except Exception:  # noqa: BLE001 — el catálogo caído no es motivo para no intentar lo de ayer
            pass
        recordada = _urls_recordadas().get(titulo)
        if recordada:
            return recordada, False
        raise RuntimeError(f"CNMC: el catálogo no responde y no hay dirección guardada para «{titulo}»")

    def fetch(self, *, backfill: bool = False) -> dict[str, list[tuple]]:
        out = {}
        recordar = _urls_recordadas()
        for titulo, (sid, col_part, factor) in DATASETS.items():
            url, del_catalogo = self.resolve_csv(titulo)
            text = http_get(url, headers=UA).content.decode("utf-8-sig")
            save_raw(f"cnmc_{sid}.csv", text)
            # Si el título llevara a otro conjunto, aquí revienta por falta de columna en vez de publicar otra cosa.
            out[sid] = parse_csv(text, col_part, factor)
            if del_catalogo:
                recordar[titulo] = url
        CACHE_URLS.parent.mkdir(parents=True, exist_ok=True)
        CACHE_URLS.write_text(json.dumps(recordar, ensure_ascii=False, indent=1), encoding="utf-8")
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
