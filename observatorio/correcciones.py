"""Registro público de correcciones (21-nov-2026).

Una fuente seria dice cuándo ha cambiado un dato que ya había publicado. Aquí se apunta, solo, cada vez que un dato
YA PUBLICADO cambia de valor:
  - `revision_fuente`: la fuente corrigió el dato y el cambio era pequeño (se acepta solo, validate.py, regla 4);
  - `revision_aprobada`: la fuente lo corrigió con un cambio grande, fue a cuarentena y una persona lo aprobó.
No se apuntan los cambios que no se ven en la web: si antes y después son iguales con los decimales de la serie
(p. ej. 5,29/15 guardado otra vez con 4 decimales), no es una corrección.

El registro vive en `data/correcciones.json` (empieza el 21-nov-2026: lo anterior no se registraba) y se publica en
`data/published/correcciones.json`, solo con las series que se publican.
"""
from __future__ import annotations

import json

from . import catalog, config, storage

DESDE = "2026-11-21"
FICHERO = config.DATA / "correcciones.json"


def cargar() -> dict:
    if FICHERO.is_file():
        return json.loads(FICHERO.read_text(encoding="utf-8"))
    return {"desde": DESDE, "correcciones": []}


def registrar(serie_id: str, cambios: list[tuple[str, float, float]], motivo: str) -> int:
    """Apunta los cambios (fecha del dato, antes, después) que se notan con los decimales de la serie."""
    try:
        dec = catalog.get(serie_id).decimals
    except KeyError:
        dec = 4
    nuevos = [(d, a, b) for d, a, b in cambios if round(a, dec) != round(b, dec)]
    if not nuevos:
        return 0
    reg = cargar()
    hoy = storage.now_iso()[:10]
    for d, a, b in nuevos:
        reg["correcciones"].append({"fecha": hoy, "serie": serie_id, "dato": d,
                                    "antes": round(a, dec), "despues": round(b, dec), "motivo": motivo})
    FICHERO.write_text(json.dumps(reg, ensure_ascii=False, indent=1), encoding="utf-8")
    return len(nuevos)


def publicar() -> None:
    """Copia el registro a lo publicado, sin las series que no se publican ni las ocultas."""
    reg = cargar()
    visibles = {s.id for s in catalog.all_series() if s.publishable and not s.hidden}
    salida = {"desde": reg.get("desde", DESDE),
              "correcciones": [c for c in reg.get("correcciones", []) if c["serie"] in visibles]}
    (config.PUBLISHED_DIR / "correcciones.json").write_text(
        json.dumps(salida, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
