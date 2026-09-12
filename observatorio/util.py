"""Utilidades comunes: HTTP con reintentos y User-Agent identificado, fechas, guardado de descargas brutas."""
from __future__ import annotations

import datetime as dt
import math
import time
from pathlib import Path

import requests

from . import config

_session: requests.Session | None = None


def session() -> requests.Session:
    global _session
    if _session is None:
        s = requests.Session()
        s.headers.update({"User-Agent": config.USER_AGENT, "Accept-Language": "es,en;q=0.8"})
        _session = s
    return _session


def http_get(url: str, *, retries: int = 3, backoff: float = 3.0, timeout: int = config.HTTP_TIMEOUT,
             **kwargs) -> requests.Response:
    """GET con reintentos ante errores de red o 5xx. Lanza excepción si todos fallan."""
    last_exc: Exception | None = None
    for attempt in range(retries):
        try:
            r = session().get(url, timeout=timeout, **kwargs)
            if r.status_code >= 500:
                raise requests.HTTPError(f"HTTP {r.status_code} en {url}", response=r)
            r.raise_for_status()
            return r
        except (requests.ConnectionError, requests.Timeout, requests.HTTPError) as e:
            last_exc = e
            if attempt < retries - 1:
                time.sleep(backoff * (attempt + 1))
    raise RuntimeError(f"No se pudo descargar {url}: {last_exc}")


def save_raw(name: str, content: bytes | str) -> Path:
    """Guarda la última descarga bruta (para depurar). La carpeta data/raw no va a git."""
    config.ensure_dirs()
    p = config.RAW_DIR / name
    if isinstance(content, str):
        p.write_text(content, encoding="utf-8")
    else:
        p.write_bytes(content)
    return p


def today() -> dt.date:
    return dt.date.today()


def parse_date(s: str) -> dt.date:
    """Acepta 'YYYY-MM-DD', 'YYYY-MM' (→ día 1) y 'YYYY' (→ 1 de enero)."""
    s = s.strip()
    if len(s) == 4:
        return dt.date(int(s), 1, 1)
    if len(s) == 7:
        y, m = s.split("-")
        return dt.date(int(y), int(m), 1)
    return dt.date.fromisoformat(s[:10])


def is_number(v) -> bool:
    try:
        f = float(v)
    except (TypeError, ValueError):
        return False
    return math.isfinite(f)


def pct_change(old: float, new: float) -> float:
    if old == 0:
        return math.inf if new != 0 else 0.0
    return abs(new - old) / abs(old) * 100.0
