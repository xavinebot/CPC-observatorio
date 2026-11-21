"""Francia, ADEME: precio de la leña en troncos para los hogares, en euros por MWh PCI. Un dato al año.

Fuente: conjunto «Prix des combustibles bois pour le chauffage domestique» de data.ademe.fr (ADEME, Licence Ouverte),
que resume la encuesta anual a revendedores de leña, pellet y troncos prensados (CODA Stratégies hasta 2024, Hearth
Connection en 2025). Una fila por año y combustible, con el precio sin entrega (`prix_non_livre`) y con entrega
(`prix_livre`), desde 2005.

Se descarga por la API abierta de data-fair, sin clave:
  1. el catálogo, buscando el conjunto por su TÍTULO exacto (DECISIONES §25: el identificador es un detalle de la
     fuente y puede cambiar; el título es como la ADEME habla de ese dato). Ahí se comprueba también que la licencia
     sigue siendo la Licence Ouverte: si cambia, no se publica nada hasta revisarlo;
  2. las filas del conjunto (JSON), con las cuatro columnas que hacen falta.

Un precio 0 o vacío es un dato que falta (en 2010 el precio con entrega viene a 0 en todos los combustibles): se
salta, no se rellena. Si un año trajera dos filas distintas para el mismo combustible, salen las dos con la misma fecha
y la validación las manda a cuarentena (DECISIONES §21).
"""
from __future__ import annotations

from ..util import http_get, save_raw
from .base import Collector as _Base

API = "https://data.ademe.fr/data-fair/api/v1"
TITULO = "Prix des combustibles bois pour le chauffage domestique"
COLUMNAS = ("annee", "type_combustible", "prix_non_livre", "prix_livre")
MIN_ANOS = 15   # años con dato que debe traer cada serie (hay 21, de 2005 a 2025): menos, descarga recortada


def productos() -> dict[str, tuple[str, str]]:
    """serie -> (combustible, columna). Vienen del catálogo para que no haya dos listas."""
    from ..catalog_series import ADEME_BOIS
    return dict(ADEME_BOIS)


class Collector(_Base):
    name = "ademe_bois"
    min_records = MIN_ANOS

    def fetch(self, *, backfill: bool = False) -> dict[str, list[tuple]]:
        cat = http_get(f"{API}/datasets", params={"q": TITULO, "size": 20,
                                                  "select": "id,title,slug,href,license,owner,dataUpdatedAt"}).json()
        href = buscar_conjunto(cat)
        r = http_get(f"{href}/lines", params={"size": 1000, "select": ",".join(COLUMNAS), "sort": "annee"})
        save_raw("ademe_bois.json", r.text)
        return parse_lines(r.json(), productos())

    def check(self, result: dict[str, list[tuple]]) -> None:
        super().check(result)
        for sid in productos():
            n = len({d for d, _ in result.get(sid, [])})
            if n < MIN_ANOS:
                raise RuntimeError(f"ademe_bois: {sid} trae solo {n} años con dato (mínimo {MIN_ANOS}); "
                                   "la fuente ha cambiado o la descarga está incompleta")


def buscar_conjunto(cat: dict) -> str:
    """La dirección (href) del conjunto, buscado por su título exacto y con la licencia comprobada."""
    for d in cat.get("results", []):
        if (d.get("title") or "").strip() != TITULO:
            continue
        owner = (d.get("owner") or {}).get("name", "")
        if owner and owner != "ADEME":
            continue
        lic = (d.get("license") or {}).get("title", "")
        if "licence ouverte" not in lic.lower():
            raise RuntimeError(f"ADEME: el conjunto «{TITULO}» ha cambiado de licencia («{lic}»); "
                               "no se publica hasta revisarla")
        if not d.get("href"):
            break
        return d["href"]
    raise RuntimeError(f"ADEME: no encuentro el conjunto «{TITULO}» en el catálogo de data.ademe.fr")


def parse_lines(d: dict, prods: dict[str, tuple[str, str]]) -> dict[str, list[tuple]]:
    """Puntos anuales (1 de enero del año de la encuesta, €/MWh tal cual) de cada serie."""
    filas = d.get("results")
    if not isinstance(filas, list) or not filas:
        raise RuntimeError("ADEME: la respuesta no trae filas")
    total = d.get("total")
    if isinstance(total, int) and total > len(filas):
        raise RuntimeError(f"ADEME: la respuesta trae {len(filas)} filas de {total}; descarga recortada")
    for col in COLUMNAS:
        if col not in filas[0]:
            raise RuntimeError(f"ADEME: no encuentro la columna «{col}» en el conjunto")
    tipos = {str(f.get("type_combustible", "")).strip() for f in filas}
    out: dict[str, set[tuple]] = {}
    for sid, (tipo, col) in prods.items():
        if tipo not in tipos:
            raise RuntimeError(f"ADEME: no encuentro el combustible «{tipo}» en el conjunto")
        pts = out.setdefault(sid, set())
        for f in filas:
            if str(f.get("type_combustible", "")).strip() != tipo:
                continue
            v = f.get(col)
            if v in (None, "") or float(v) == 0:
                continue   # dato que falta: no se rellena
            try:
                ano = int(f["annee"])
            except (TypeError, ValueError):
                raise RuntimeError(f"ADEME: año no reconocido «{f.get('annee')}»") from None
            pts.add((f"{ano:04d}-01-01", float(v)))
    return {sid: sorted(p) for sid, p in out.items()}
