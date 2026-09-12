"""Almacenamiento: una serie = un CSV `date,value` en data/series/; estado global en data/state.json."""
from __future__ import annotations

import csv
import datetime as dt
import json
from pathlib import Path

from . import config

Point = tuple[str, float]  # ('YYYY-MM-DD', valor)


def series_path(serie_id: str) -> Path:
    return config.SERIES_DIR / f"{serie_id}.csv"


def read_series(serie_id: str) -> list[Point]:
    p = series_path(serie_id)
    if not p.is_file():
        return []
    out: list[Point] = []
    with p.open(encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            out.append((row["date"], float(row["value"])))
    out.sort()
    return out


def write_series(serie_id: str, points: list[Point], decimals: int = 4) -> None:
    config.ensure_dirs()
    pts = sorted({d: v for d, v in points}.items())  # una fila por fecha, la última gana
    with series_path(serie_id).open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["date", "value"])
        for d, v in pts:
            w.writerow([d, f"{v:.{decimals}f}".rstrip("0").rstrip(".") if decimals else f"{v:.0f}"])


def last_point(serie_id: str) -> Point | None:
    pts = read_series(serie_id)
    return pts[-1] if pts else None


# ---------------- estado ----------------

def load_state() -> dict:
    if config.STATE_FILE.is_file():
        return json.loads(config.STATE_FILE.read_text(encoding="utf-8"))
    return {"series": {}, "runs": [], "telegram_offset": 0}


def save_state(state: dict) -> None:
    config.ensure_dirs()
    state["runs"] = state.get("runs", [])[-60:]  # nos quedamos con las últimas 60 ejecuciones
    config.STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=1, sort_keys=True) + "\n",
                                 encoding="utf-8")


def now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()
