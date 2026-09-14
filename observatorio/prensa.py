"""Los números de la nota de prensa, sacados de los datos publicados.

No inventa ni redondea la historia: saca el último dato, el de hace doce meses, la variación, el máximo y el
mínimo del histórico, y el contraste con el índice del INE/Eurostat. La nota está en `NOTA-PRENSA.md`; esto solo
sirve para no copiar a mano una cifra vieja el día que se envíe.

La comparación en euros por kWh de calor útil NO se calcula aquí a propósito: el rendimiento de cada aparato vive
en el plugin (`class-cpc-obs-factores.php`) y tenerlo en dos sitios es la mejor forma de que un día no coincidan.
Esas cifras se leen de la propia página, que es además lo que verá el periodista.
"""
from __future__ import annotations

import datetime as _dt
from typing import Optional

from . import storage

# Series que sostienen la nota: la de precio y la que la corrobora desde otra fuente.
TITULAR = "gasoleo_es"
CONTRASTE = "hicp_comb_liquidos_es"
OTRAS = ("butano_es", "electricidad_es", "gas_es", "pellet_saco_es")


def _fecha(d: str) -> _dt.date:
    return _dt.date.fromisoformat(d)


def _hace_un_ano(puntos, desde: str):
    """El punto más cercano a doce meses antes de `desde` (None si queda a más de 45 días)."""
    objetivo = _fecha(desde) - _dt.timedelta(days=365)
    mejor = min(puntos, key=lambda p: abs((_fecha(p[0]) - objetivo).days))
    return mejor if abs((_fecha(mejor[0]) - objetivo).days) <= 45 else None


def _variacion(puntos) -> Optional[tuple]:
    if len(puntos) < 2:
        return None
    ultimo = puntos[-1]
    antes = _hace_un_ano(puntos, ultimo[0])
    if not antes or not antes[1]:
        return None
    return ultimo, antes, (ultimo[1] - antes[1]) / abs(antes[1]) * 100


def _linea(serie_id: str) -> str:
    puntos = storage.read_series(serie_id)
    if not puntos:
        return f"{serie_id:24} sin datos"
    v = _variacion(puntos)
    if not v:
        return f"{serie_id:24} último {puntos[-1][0]} {puntos[-1][1]} (sin punto de hace un año)"
    ultimo, antes, pct = v
    return (f"{serie_id:24} {ultimo[1]:>10.4f} ({ultimo[0]})   hace un año {antes[1]:>10.4f} ({antes[0]})"
            f"   {pct:+.1f} %")


def informe() -> str:
    out = ["NÚMEROS PARA LA NOTA DE PRENSA", "=" * 72, ""]

    puntos = storage.read_series(TITULAR)
    if not puntos:
        return "No hay datos de " + TITULAR

    v = _variacion(puntos)
    out.append("EL TITULAR")
    out.append("  " + _linea(TITULAR))
    if v:
        ultimo, antes, pct = v
        # Cuánto de la subida es de los últimos tres meses: es el matiz que hace creíble la nota.
        hace3 = [p for p in puntos if _fecha(p[0]) <= _fecha(ultimo[0]) - _dt.timedelta(days=90)]
        if hace3:
            out.append(f"  de los que, desde {hace3[-1][0]} ({hace3[-1][1]:.4f}), "
                       f"{(ultimo[1] - hace3[-1][1]) / abs(hace3[-1][1]) * 100:+.1f} %")
    maximo = max(puntos, key=lambda p: p[1])
    minimo = min(puntos, key=lambda p: p[1])
    out.append(f"  máximo del histórico: {maximo[1]:.4f} ({maximo[0]})"
               f"   hoy está un {(puntos[-1][1] - maximo[1]) / maximo[1] * 100:+.1f} % respecto a ese máximo")
    out.append(f"  mínimo del histórico: {minimo[1]:.4f} ({minimo[0]})")
    out.append(f"  la serie arranca en {puntos[0][0]} con {len(puntos)} datos")
    out.append("")

    out.append("LA SEGUNDA FUENTE (para que el número no dependa de una sola)")
    out.append("  " + _linea(CONTRASTE))
    out.append("")

    out.append("OTRAS SERIES, POR SI LA HISTORIA DE OCTUBRE ES OTRA")
    for s in OTRAS:
        out.append("  " + _linea(s))
    out.append("")

    out.append("NO SALE DE AQUÍ: los euros por kWh de calor útil y el coste anual de 10.000 kWh se leen de la")
    out.append("propia página (tabla de portada y desplegable del coste anual). El rendimiento de cada aparato")
    out.append("está en el plugin, y se deja en un solo sitio a propósito.")
    out.append("")
    out.append("Y la regla de siempre: si el número ha cambiado de signo, cambia la nota. No se envía una cifra")
    out.append("vieja porque contase una historia mejor.")
    return "\n".join(out)
