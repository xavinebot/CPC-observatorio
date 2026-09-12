"""Rutas, carga de secretos y constantes globales.

Los secretos se leen, por este orden: variables de entorno ya definidas (GitHub Actions), el fichero
`~/cpc-observatorio.env` (PC del usuario, fuera del repositorio) y `.env` en la raíz del repo (ignorado por git).
"""
from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
SERIES_DIR = DATA / "series"
QUARANTINE_DIR = DATA / "quarantine"
PUBLISHED_DIR = DATA / "published"
RAW_DIR = DATA / "raw"
STATE_FILE = DATA / "state.json"

USER_AGENT = "CPC-Observatorio/0.1 (+https://cristalesparachimeneas.es/contacto/; bot de recogida de precios publicos)"
HTTP_TIMEOUT = 60

# Ficheros de secretos, en orden de prioridad (el primero que exista gana para cada clave que falte).
ENV_FILES = [Path.home() / "cpc-observatorio.env", ROOT / ".env"]

_loaded = False


def load_env() -> None:
    """Carga las claves de los ficheros .env que existan SIN pisar variables ya definidas."""
    global _loaded
    if _loaded:
        return
    for f in ENV_FILES:
        if not f.is_file():
            continue
        for line in f.read_text(encoding="utf-8-sig").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            k, v = k.strip(), v.strip().strip('"').strip("'")
            if k and v and not os.environ.get(k):
                os.environ[k] = v
    _loaded = True


def secret(name: str, default: str | None = None) -> str | None:
    load_env()
    v = os.environ.get(name)
    return v if v else default


def in_github_actions() -> bool:
    return os.environ.get("GITHUB_ACTIONS") == "true"


def ensure_dirs() -> None:
    for d in (SERIES_DIR, QUARANTINE_DIR, PUBLISHED_DIR, RAW_DIR):
        d.mkdir(parents=True, exist_ok=True)
