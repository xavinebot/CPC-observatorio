"""Red Eléctrica (REData, sin token): PVPC (id 1001, desde 2021-06) y mercado spot (id 600, desde 2014),
en €/MWh por hora. Aquí se promedian por día y se guardan en €/kWh.

Límites comprobados de la API: solo `time_trunc=hour` y como máximo ~1 mes por llamada. En modo normal se piden
el mes en curso y el anterior; con --backfill se recorre mes a mes desde el inicio (~150 llamadas, pausadas).
"""
from __future__ import annotations

import datetime as dt
import time
from collections import defaultdict

from ..util import http_get, today
from .base import Collector as _Base

URL = "https://apidatos.ree.es/es/datos/mercados/precios-mercados-tiempo-real"
START = {"pvpc_es": dt.date(2021, 6, 1), "spot_es": dt.date(2014, 1, 1)}
IDS = {"1001": "pvpc_es", "600": "spot_es"}


def month_range(start: dt.date, end: dt.date):
    y, m = start.year, start.month
    while (y, m) <= (end.year, end.month):
        first = dt.date(y, m, 1)
        last = (dt.date(y + (m == 12), m % 12 + 1, 1) - dt.timedelta(days=1))
        yield first, min(last, end)
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)


class Collector(_Base):
    name = "ree"
    min_records = 20
    pause = 0.7  # segundos entre llamadas (cortesía)

    def fetch(self, *, backfill: bool = False) -> dict[str, list[tuple]]:
        end = today()
        if backfill:
            start = START["spot_es"]
        else:
            start = (end.replace(day=1) - dt.timedelta(days=1)).replace(day=1)  # primer día del mes anterior
        daily: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
        for first, last in month_range(start, end):
            params = {"start_date": f"{first.isoformat()}T00:00", "end_date": f"{last.isoformat()}T23:59",
                      "time_trunc": "hour"}
            try:
                r = http_get(URL, params=params, retries=2)
                d = r.json()
            except Exception as e:  # noqa: BLE001
                if backfill:
                    print(f"   ree: {first} sin datos ({e})")
                    continue
                raise
            for inc in d.get("included", []):
                sid = IDS.get(str(inc.get("id")))
                if not sid:
                    continue
                for v in inc["attributes"]["values"]:
                    if v.get("value") is None:
                        continue
                    daily[sid][v["datetime"][:10]].append(float(v["value"]))
            time.sleep(self.pause)
        out = {}
        for sid, days in daily.items():
            pts = []
            for day, vals in sorted(days.items()):
                if len(vals) < 20:   # día incompleto (hoy, cambios de hora raros): no se guarda
                    continue
                pts.append((day, sum(vals) / len(vals) / 1000.0))  # €/MWh → €/kWh
            out[sid] = pts
        return out
