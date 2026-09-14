"""Publicación: convierte los CSV validados en los JSON que lee el plugin de WordPress.

Salida en data/published/:
  index.json          → lista de series con metadatos, último dato y estado (ok / caducada / pendiente)
  <pais>.json         → todas las series de ese país (hogar e industria), con puntos nativos y medias mensuales
  csv/<serie>.csv     → CSV descargable con cabecera de fuente y licencia (solo series redistribuibles)
Nunca se rellenan huecos: si una serie no tiene datos, aparece con status 'pendiente' y sin puntos.
"""
from __future__ import annotations

import json
from collections import defaultdict

from . import catalog, config, storage
from .util import parse_date, today

MAX_NATIVE_POINTS_DAILY = 800   # para series diarias publicamos ~2 años en detalle; el resto, mensual

COUNTRIES = ["ES", "FR", "IT", "DE", "PT", "AT", "EU"]


def monthly_average(points: list[storage.Point]) -> list[list]:
    acc: dict[str, list[float]] = defaultdict(list)
    for d, v in points:
        acc[d[:7]].append(v)
    return [[m, round(sum(vs) / len(vs), 4)] for m, vs in sorted(acc.items())]


def serie_status(s: catalog.Serie, points: list[storage.Point]) -> str:
    if not s.publishable:
        return "pendiente_autorizacion"
    if s.min_points and len(points) < s.min_points:
        return "en_construccion"
    if not points:
        return "pendiente"
    age = (today() - parse_date(points[-1][0])).days
    return "caducada" if age > s.stale_after_days else "ok"


def serie_payload(s: catalog.Serie, points: list[storage.Point]) -> dict:
    estado = serie_status(s, points)
    faltan = max(0, s.min_points - len(points)) if s.min_points else 0
    if estado in ("pendiente_autorizacion", "en_construccion"):
        points = []   # recolectada, pero todavía no se enseña (falta permiso o falta historia)
    native = points
    if s.native_freq == "D" and len(points) > MAX_NATIVE_POINTS_DAILY:
        native = points[-MAX_NATIVE_POINTS_DAILY:]
    return {
        "id": s.id, "name": s.name, "country": s.country, "group": s.group, "fuel": s.fuel,
        "unit": s.unit, "kwh_per_unit": s.kwh_per_unit, "taxes_included": s.taxes_included,
        "freq": s.native_freq, "decimals": s.decimals, "notes": s.notes,
        "source": fuente_publicada(s.source),
        "redistributable": s.redistributable,
        "en_comparativa": s.en_comparativa,
        "status": estado,
        "faltan": faltan,
        "min_points": s.min_points,
        "first_date": points[0][0] if points else None,
        "last_date": points[-1][0] if points else None,
        "last_value": points[-1][1] if points else None,
        "n": len(points),
        "points": [[d, v] for d, v in native],
        "monthly": monthly_average(points) if s.native_freq in ("D", "W") else [],
    }


def extras_lena() -> dict:
    """Dispersion de la ultima lectura del indice de lena (numero de tiendas, referencias y horquilla)."""
    f = config.DATA / "lena" / "ultimo_resumen.json"
    if not f.is_file():
        return {}
    try:
        d = json.loads(f.read_text(encoding="utf-8"))
    except ValueError:
        return {}
    return d.get("series", {})


def build_all() -> None:
    config.ensure_dirs()
    extras = extras_lena()
    (config.PUBLISHED_DIR / "csv").mkdir(exist_ok=True)
    generated = storage.now_iso()
    index = {"generated": generated, "series": []}
    per_country: dict[str, dict] = {c: {"generated": generated, "country": c, "series": []} for c in COUNTRIES}
    for s in catalog.all_series():
        if s.hidden:
            continue
        pts = storage.read_series(s.id)
        payload = serie_payload(s, pts)
        if s.id in extras:
            payload["extra"] = extras[s.id]
        index["series"].append({k: payload[k] for k in ("id", "name", "country", "group", "fuel", "unit",
                                                        "status", "first_date", "last_date", "last_value", "n",
                                                        "faltan")})
        per_country.setdefault(s.country, {"generated": generated, "country": s.country, "series": []})
        per_country[s.country]["series"].append(payload)
        if s.redistributable and payload["status"] == "ok" and pts:
            write_csv(s, pts, generated)
        else:
            # Si una serie deja de publicarse (p. ej. pasa a "en construcción"), su CSV no puede quedarse
            # colgado: seguiría descargándose y el marcado lo anunciaría.
            viejo = config.PUBLISHED_DIR / "csv" / f"{s.id}.csv"
            if viejo.is_file():
                viejo.unlink()
    (config.PUBLISHED_DIR / "index.json").write_text(json.dumps(index, ensure_ascii=False, separators=(",", ":")),
                                                     encoding="utf-8")
    for c, payload in per_country.items():
        (config.PUBLISHED_DIR / f"{c.lower()}.json").write_text(
            json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")


def fuente_publicada(src: catalog.Source) -> dict:
    """La fuente tal como la lee el plugin.

    `license` va siempre en español (repuesto y compatibilidad con la versión anterior del plugin) y,
    cuando la condición está escrita en los cinco idiomas, se añade `license_i18n` para que cada página
    la enseñe en el suyo.
    """
    out = {"name": src.name, "url": src.url, "license": catalog.licencia_es(src),
           "license_url": src.license_url, "attribution": src.attribution}
    if isinstance(src.license, dict):
        out["license_i18n"] = dict(src.license)
    return out


def write_csv(s: catalog.Serie, pts: list[storage.Point], generated: str) -> None:
    lines = [
        f"# {s.name['es']} ({s.country})",
        f"# Unidad: {s.unit}",
        f"# Fuente: {s.source.name} - {s.source.url}",
        f"# Licencia: {catalog.licencia_es(s.source)} - {s.source.license_url}",
        f"# Cita obligatoria: {s.source.attribution}",
        f"# Recopilado por Observatorio de precios de cristalesparachimeneas.es - generado {generated}",
        "date,value",
    ]
    lines += [f"{d},{v:g}" for d, v in pts]
    (config.PUBLISHED_DIR / "csv" / f"{s.id}.csv").write_text("\n".join(lines) + "\n", encoding="utf-8")
