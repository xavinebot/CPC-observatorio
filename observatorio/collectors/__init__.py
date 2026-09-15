"""Registro de recolectores. Cada módulo define una clase Collector; aquí se listan por nombre."""
from __future__ import annotations

import importlib

# nombre del recolector -> módulo (en orden de ejecución)
COLLECTORS: dict[str, str] = {
    "wob": "wob",
    "cnmc_glp": "cnmc_glp",
    "eurostat_nrg": "eurostat",
    "eurostat_nrg_ind": "eurostat",
    "eurostat_hicp": "eurostat",
    "eurostat_sts": "eurostat",
    "ree": "ree",
    "ine_ipc": "ine",
    "ine_ipri": "ine",
    "worldbank": "worldbank",
    "comext": "comext",
    "avebiom": "avebiom",
    "pellets_eu": "pellets_eu",
    "fr_fioul": "fr_fioul",
    "lena": "lena",
}


def get(name: str):
    mod = importlib.import_module(f"{__name__}.{COLLECTORS[name]}")
    cls = getattr(mod, "COLLECTORS", {}).get(name) or mod.Collector
    return cls()


def names() -> list[str]:
    return list(COLLECTORS)
