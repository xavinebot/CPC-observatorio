"""AIEL (Associazione Italiana Energie Agroforestali): precio del pellet y de la leña en Italia, en euros.

AIEL mide tres veces al año (enero, abril y septiembre) y lo publica unas semanas después en un artículo por
combustible en https://energiadallegno.it/tag/prezzibiocombustibili/. Las tablas de esos artículos son IMÁGENES y el
texto da las cifras con frases distintas cada vez (y no siempre): no se pueden leer de forma fiable con un programa.
Por eso las cifras se cargan A MANO en `data/manual/aiel.csv`, una fila por medición, copiadas de la tabla y
comprobadas con el texto del artículo, y este recolector solo las lee. Además mira la página de AIEL: si hay una
medición más nueva que la última cargada, falla con un aviso para que se cargue (es `optional`: sale en el resumen
semanal, no como incidencia). Y hay recordatorios en `recordatorios.py` en las fechas en que suele publicar.

AUTORIZACIÓN: AIEL autorizó el uso de sus datos por correo a Xavier el 24 de noviembre de 2026 (el correo, en PDF, en
`observatorio-docs/`). Condiciones que impone y que hay que respetar al tocar esto:
  1. Citar AIEL como fuente, con enlace directo a su página de precios
     (https://energiadallegno.it/tag/prezzibiocombustibili/), no a la portada ni a un artículo suelto.
  2. Sus precios llevan IVA; si una medición no lo lleva, lo dice el artículo, y hay que respetarlo dato a dato. Hasta
     enero de 2024 las tablas de pellet en saco y de leña dicen «IVA esclusa» (y el IVA del pellet pasó del 22 % al
     10 % en 2023): esas mediciones NO entran en estas series, que son todas «IVA inclusa». No se convierte nada.
  3. Indicar la fecha concreta de cada medición: cada punto lleva el mes de la medición que da AIEL («settembre
     2026»), no la fecha en que lo cargamos.
  4. Que sus datos no se puedan descargar de nuestra web: `redistributable=False` (sin CSV, sin descarga en el
     marcado Dataset, sin gráfico incrustable ni PNG) y `sin_descarga=True` (fuera de la imagen de la comparativa
     que se descarga o se incrusta). Fijado en tests/test_colectores.py.

CAMBIO DE MÉTODO: en enero de 2025 AIEL cambió cómo mide el pellet a granel («in autobotte»: 6 t a 50 km). La serie
del granel empieza ahí; lo de antes (además con IVA unas veces sí y otras no) no se publica, así que ninguna variación
cruza el cambio. La leña A1 empieza en enero de 2025: la tabla de abril de 2024 es un panel de Looker Studio que no se
puede leer, y desde 2025 las tres clases (A1, A2, B) salen en todas las tablas.
"""
from __future__ import annotations

import csv
import io
import re

from ..util import http_get
from .base import Collector as _Base

PAGINA = "https://energiadallegno.it/tag/prezzibiocombustibili/"
UA = {"User-Agent": "Mozilla/5.0 (compatible; CPC-Observatorio/0.1; +https://cristalesparachimeneas.es/contacto/)"}
# Unidad de AIEL -> factor para pasar a €/kg (como el pellet de España y Austria; la web vuelve a enseñar el saco).
FACTOR = {"EUR/sacco15kg": 1 / 15, "EUR/t": 1 / 1000}
SERIES = ("pellet_saco_it", "pellet_granel_it", "lena_a1_it")
MESES = {"gennaio": 1, "febbraio": 2, "marzo": 3, "aprile": 4, "maggio": 5, "giugno": 6, "luglio": 7, "agosto": 8,
         "settembre": 9, "ottobre": 10, "novembre": 11, "dicembre": 12}


def fichero():
    from pathlib import Path
    return Path(__file__).resolve().parents[2] / "data" / "manual" / "aiel.csv"


def leer(texto: str) -> dict[str, list[tuple]]:
    """Las filas del CSV manual -> {serie: [(AAAA-MM-01, €/kg)]}. Falla si una fila no es de fiar."""
    lineas = [l for l in texto.splitlines() if l.strip() and not l.lstrip().startswith("#")]
    out: dict[str, list[tuple]] = {s: [] for s in SERIES}
    for r in csv.DictReader(io.StringIO("\n".join(lineas))):
        sid = r["serie"].strip()
        if sid not in out:
            raise RuntimeError(f"aiel.csv: serie desconocida «{sid}»")
        if r["iva"].strip() != "inclusa":
            raise RuntimeError(f"aiel.csv: {sid} {r['medicion']} no es «IVA inclusa»: no entra (condición 2 de AIEL)")
        if r["unidad"].strip() not in FACTOR:
            raise RuntimeError(f"aiel.csv: unidad desconocida «{r['unidad']}»")
        if not re.fullmatch(r"20\d\d-(0[1-9]|1[0-2])", r["medicion"].strip()):
            raise RuntimeError(f"aiel.csv: mes de medición raro «{r['medicion']}»")
        if not r["articulo"].strip().startswith("https://energiadallegno.it/"):
            raise RuntimeError(f"aiel.csv: {sid} {r['medicion']} sin el artículo de AIEL del que sale")
        valor = float(r["valor"]) * FACTOR[r["unidad"].strip()]
        out[sid].append((r["medicion"].strip() + "-01", round(valor, 6)))
    for sid in out:
        fechas = [d for d, _ in out[sid]]
        if len(fechas) != len(set(fechas)):
            raise RuntimeError(f"aiel.csv: {sid} tiene una medición repetida")
        out[sid].sort()
    return out


def ultima_publicada(html: str) -> str | None:
    """El mes más reciente con artículo de pellet o de leña en la página de AIEL («2026-09»)."""
    meses = []
    for m in re.finditer(r"prezzo-(?:del-pellet|della-legna-da-ardere)-(?:a|ad|in-[a-z]+-a)?-?([a-z]+)-(20\d\d)", html):
        if m.group(1) in MESES:
            meses.append(f"{m.group(2)}-{MESES[m.group(1)]:02d}")
    return max(meses) if meses else None


class Collector(_Base):
    name = "aiel"
    min_records = 15
    # Sale en el resumen semanal si falla (p. ej. hay una medición nueva sin cargar), no como incidencia: las series
    # siguen publicadas con lo cargado.
    optional = True

    def fetch(self, *, backfill: bool = False) -> dict[str, list[tuple]]:
        out = leer(fichero().read_text(encoding="utf-8"))
        ultima_cargada = max(d[:7] for pts in out.values() for d, _ in pts)
        try:
            html = http_get(PAGINA, headers=UA).text
        except Exception:  # noqa: BLE001 — si la web de AIEL no responde, no pasa nada: lo cargado sigue valiendo
            return out
        nueva = ultima_publicada(html)
        if nueva and nueva > ultima_cargada:
            raise RuntimeError(f"AIEL ha publicado la medición de {nueva} y la última cargada es {ultima_cargada}: "
                               f"cópiala de las tablas de sus artículos en data/manual/aiel.csv")
        return out
