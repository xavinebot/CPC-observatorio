"""Cuarentena: datos sospechosos que NO se publican hasta que el usuario los apruebe (o los descarte).

Un fichero por serie en data/quarantine/<id>.json. Se aprueba/descarta por Telegram (botones) o por CLI.
"""
from __future__ import annotations

import json
from pathlib import Path

from . import alerts, catalog, config, storage
from .validate import Rejected


def path(serie_id: str) -> Path:
    return config.QUARANTINE_DIR / f"{serie_id}.json"


def load(serie_id: str) -> dict | None:
    p = path(serie_id)
    return json.loads(p.read_text(encoding="utf-8")) if p.is_file() else None


def pending() -> list[dict]:
    config.ensure_dirs()
    return [json.loads(p.read_text(encoding="utf-8")) for p in sorted(config.QUARANTINE_DIR.glob("*.json"))]


def add(serie_id: str, rejected: list[Rejected]) -> dict:
    """Añade puntos rechazados a la cuarentena de la serie (sin duplicar fechas). NO avisa: el runner manda un
    único resumen al final de la ejecución (ver notify_batch)."""
    config.ensure_dirs()
    q = load(serie_id) or {"serie": serie_id, "created": storage.now_iso(), "points": []}
    known = {p["date"] for p in q["points"]}
    new = [r for r in rejected if r.date not in known]
    for r in new:
        q["points"].append({"date": r.date, "value": r.value, "reason": r.reason})
    q["updated"] = storage.now_iso()
    path(serie_id).write_text(json.dumps(q, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    if new:
        notify(serie_id, new)
    return q


def notify(serie_id: str, points: list[Rejected]) -> None:
    s = catalog.get(serie_id)
    last = storage.last_point(serie_id)
    lines = [f"⚠️ <b>Dato en cuarentena</b>: {alerts.esc(s.name['es'])} ({s.country})",
             f"Fuente: {alerts.esc(s.source.name)} · unidad {alerts.esc(s.unit)}"]
    if last:
        lines.append(f"Último dato bueno: {last[0]} = {last[1]:g}")
    for r in points[:8]:
        lines.append(f"• {r.date}: {r.value if r.value is not None else '—'} → {alerts.esc(r.reason)}")
    if len(points) > 8:
        lines.append(f"… y {len(points) - 8} más")
    lines.append("La web sigue mostrando el último valor bueno. ¿Qué hago?")
    alerts.send("\n".join(lines), buttons=[[
        {"text": "✅ Aprobar y publicar", "callback_data": f"approve:{serie_id}"},
        {"text": "🗑 Descartar", "callback_data": f"discard:{serie_id}"},
    ]])


def approve(serie_id: str) -> int:
    """Pasa los puntos en cuarentena a la serie (sin revalidar: es una decisión humana). Devuelve nº puntos."""
    q = load(serie_id)
    if not q:
        return 0
    s = catalog.get(serie_id)
    pts = storage.read_series(serie_id)
    valid = [(p["date"], float(p["value"])) for p in q["points"] if p.get("value") is not None]
    storage.write_series(serie_id, pts + valid, s.decimals)
    path(serie_id).unlink()
    return len(valid)


def discard(serie_id: str) -> int:
    q = load(serie_id)
    if not q:
        return 0
    path(serie_id).unlink()
    return len(q["points"])


def process_telegram_decisions(state: dict) -> list[str]:
    """Lee las pulsaciones de botones pendientes en Telegram y las aplica. Devuelve un resumen por línea."""
    offset = int(state.get("telegram_offset", 0))
    updates = alerts.get_updates(offset)
    out: list[str] = []
    for u in updates:
        state["telegram_offset"] = u["update_id"] + 1
        cq = u.get("callback_query")
        if not cq:
            continue
        data = cq.get("data", "")
        if ":" not in data:
            continue
        action, serie_id = data.split(":", 1)
        if action == "approve":
            n = approve(serie_id)
            msg = f"Aprobados {n} puntos de {serie_id}" if n else f"{serie_id}: no había nada en cuarentena"
        elif action == "discard":
            n = discard(serie_id)
            msg = f"Descartados {n} puntos de {serie_id}" if n else f"{serie_id}: no había nada en cuarentena"
        else:
            continue
        alerts.answer_callback(cq["id"], msg)
        alerts.send(f"✔️ {alerts.esc(msg)}")
        out.append(msg)
    return out
