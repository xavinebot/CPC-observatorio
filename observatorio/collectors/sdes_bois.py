"""Francia, SDES: precio del pellet para los hogares (en sacos y a granel), en euros por tonelada con impuestos.

Fuente: «Conjoncture mensuelle de l'énergie» del SDES (servicio de estadística del ministerio de la Transición
Ecológica), fichero «1.4. Prix ménages Bois», con datos del CEEB. Se descarga por la API abierta del portal DiDo:
  1. la ficha del conjunto de datos (JSON), que dice cuál es la última entrega del fichero (`millesime`, p. ej.
     "2026-11"); no se fija a mano porque cambia cada mes;
  2. el CSV de esa entrega: separado por «;», con tres filas de cabecera (descripción, unidad, nombre de columna) y
     un mes por fila, de lo más nuevo a lo más viejo. Los meses sin dato (antes de 2007 y los más recientes, que
     aún no han llegado) vienen vacíos.
Licencia Ouverte / Etalab 2.0: se puede publicar y redistribuir citando la fuente.

EL DATO ES TRIMESTRAL. El fichero es mensual, pero repite el mismo valor en los tres meses de cada trimestre
(comprobado el 21 nov 2026 en los 78 trimestres de 2007 a 2026: en todos, los tres meses son idénticos). Se guarda un
punto por trimestre, fechado el primer día (como AVEBIOM): tres puntos iguales harían creer que hay un dato al mes.
Si algún trimestre trajera meses distintos, se mandan los distintos valores con la misma fecha y la validación los
lleva a cuarentena: no se promedia ni se elige uno (DECISIONES §21 y §29).

Se ignoran las columnas «par 100 kWh PCI»: el coste del calor lo calcula la web con el mismo poder calorífico para
el pellet de todos los países.
"""
from __future__ import annotations

import csv
import io

from ..util import http_get, save_raw
from .base import Collector as _Base

API = "https://data.statistiques.developpement-durable.gouv.fr/dido/api/v1"
DATASET = "631b03afb61e5c6479370169"          # Conjoncture mensuelle de l'énergie
DATAFILE = "0bf930dc-bfac-4e6f-a063-ec1774c6d029"  # 1.4. Prix ménages Bois
UA = {"User-Agent": "Mozilla/5.0 (compatible; CPC-Observatorio/0.1; +https://cristalesparachimeneas.es/contacto/)"}
QUARTER_MONTH = {1: "01", 2: "04", 3: "07", 4: "10"}
MIN_POR_SERIE = 60   # trimestres con dato que debe traer cada serie (hay 78 desde 2007): menos, fichero recortado


def columnas() -> dict[str, str]:
    """serie -> columna del CSV (en euros por tonelada). Vienen del catálogo para que no haya dos listas."""
    from ..catalog_series import SDES_BOIS
    return {sid: v[0] for sid, v in SDES_BOIS.items()}


class Collector(_Base):
    name = "sdes_bois"
    min_records = 2 * MIN_POR_SERIE

    def fetch(self, *, backfill: bool = False) -> dict[str, list[tuple]]:
        meta = http_get(f"{API}/datasets/{DATASET}", headers=UA).json()
        mil = ultimo_millesime(meta)
        r = http_get(f"{API}/datafiles/{DATAFILE}/csv", headers=UA,
                     params={"millesime": mil, "withColumnName": "true", "withColumnDescription": "true",
                             "withColumnUnit": "true"})
        save_raw("sdes_bois.csv", r.content)
        return parse_csv(r.content.decode("utf-8-sig"), columnas())

    def check(self, result: dict[str, list[tuple]]) -> None:
        super().check(result)
        # Que no falte una de las dos: si la fuente renombra una columna, parse_csv ya falla; esto cubre que una
        # columna llegue vacía o casi.
        for sid in columnas():
            n = len({d for d, _ in result.get(sid, [])})
            if n < MIN_POR_SERIE:
                raise RuntimeError(f"sdes_bois: {sid} trae solo {n} trimestres con dato (mínimo {MIN_POR_SERIE}); "
                                   "la fuente ha cambiado o la descarga está incompleta")


def ultimo_millesime(meta: dict) -> str:
    """La entrega más reciente del fichero de precios de la madera, leída de la ficha del conjunto de datos."""
    for f in meta.get("datafiles", []):
        if f.get("rid") == DATAFILE:
            mils = [m.get("millesime") for m in f.get("millesimes", []) if m.get("millesime")]
            if not mils:
                break
            return max(mils)   # "AAAA-MM": el orden de texto es el de las fechas
    raise RuntimeError(f"SDES: la ficha del conjunto {DATASET} no trae entregas del fichero {DATAFILE}")


def parse_csv(text: str, cols: dict[str, str]) -> dict[str, list[tuple]]:
    """Puntos trimestrales (primer día del trimestre, €/kg) de cada serie a partir del CSV del SDES."""
    rows = list(csv.reader(io.StringIO(text), delimiter=";"))
    # La fila de nombres de columna es la que empieza por PERIODE (la 3.ª con las cabeceras que pedimos).
    head = next((i for i, r in enumerate(rows[:10]) if r and r[0].strip() == "PERIODE"), None)
    if head is None:
        raise RuntimeError("SDES: no encuentro la fila de cabecera «PERIODE» en el CSV")
    names = [c.strip() for c in rows[head]]
    idx = {}
    for sid, col in cols.items():
        if col not in names:
            raise RuntimeError(f"SDES: no encuentro la columna {col} en el CSV")
        idx[sid] = names.index(col)
    # Unidad declarada en la 2.ª fila de cabecera: si deja de ser «euros TTC», la conversión ya no vale.
    if head >= 1:
        for sid, i in idx.items():
            unidad = rows[head - 1][i].strip() if i < len(rows[head - 1]) else ""
            if unidad and unidad.lower() != "euros ttc":
                raise RuntimeError(f"SDES: la columna {cols[sid]} viene en «{unidad}», no en euros TTC")
    out: dict[str, set[tuple]] = {sid: set() for sid in cols}
    for r in rows[head + 1:]:
        if not r or not r[0].strip():
            continue
        periodo = r[0].strip()
        try:
            year, month = periodo.split("-")
            q = (int(month) - 1) // 3 + 1
            fecha = f"{int(year):04d}-{QUARTER_MONTH[q]}-01"
        except (ValueError, KeyError):
            raise RuntimeError(f"SDES: periodo no reconocido «{periodo}»") from None
        for sid, i in idx.items():
            raw = r[i].strip() if i < len(r) else ""
            if not raw:
                continue   # mes sin dato: no se rellena
            # €/t con punto decimal → €/kg. Redondeo a 7 decimales solo para quitar el ruido de la división.
            out[sid].add((fecha, round(float(raw.replace(",", ".")) / 1000, 7)))
    # Un valor por trimestre si los tres meses coinciden (lo normal); si no, salen los distintos con la misma
    # fecha y la validación los manda a cuarentena.
    return {sid: sorted(pts) for sid, pts in out.items()}
