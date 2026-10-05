"""Ejecución completa: decisiones pendientes de Telegram → recolectar → validar → guardar/cuarentena →
comprobar caducidad y contraste → publicar → avisar."""
from __future__ import annotations

import traceback

from . import alerts, catalog, collectors, config, contrast, publish, quarantine, recordatorios, storage
from .util import parse_date, today
from .validate import validate_points


def run(only: list[str] | None = None, *, backfill: bool = False, publish_after: bool = True,
        notify: bool = True) -> int:
    config.ensure_dirs()
    state = storage.load_state()
    started = storage.now_iso()
    decisions = quarantine.process_telegram_decisions(state)
    for d in decisions:
        print("[telegram]", d)

    names = only or collectors.names()
    failures: list[tuple[str, str]] = []
    soft_failures: list[tuple[str, str]] = []
    pasajeros: list[tuple[str, str]] = []   # primer fallo seguido: se apunta, no se avisa
    added_total = 0
    quarantined: list[str] = []
    for name in names:
        print(f"== {name}")
        sstate = state["series"].setdefault(name, {})
        sstate["last_attempt"] = storage.now_iso()
        opcional = False
        try:
            col = collectors.get(name)
            opcional = getattr(col, "optional", False)
            result = col.fetch(backfill=backfill)
            col.check(result)
        except Exception as e:  # noqa: BLE001 — cualquier fallo de la fuente se registra y se sigue
            msg = f"{type(e).__name__}: {e}"
            print("   FALLO" + (" (fuente opcional)" if opcional else "") + ":", msg)
            traceback.print_exc(limit=2)
            seguidos = sstate.get("consecutive_failures", 0) + 1
            sstate["consecutive_failures"] = seguidos
            sstate["last_error"] = msg[:500]
            # Un tropiezo suelto de una fuente NO se avisa. Cuando una web se cae un rato o devuelve una pagina
            # en blanco, la nuestra sigue enseñando el ultimo dato bueno y al dia siguiente se recoge solo: no
            # hay nada que hacer, y el aviso solo enseña a no mirar los avisos. En cinco dias de septiembre de
            # 2026 hubo tres, los tres se arreglaron solos.
            # Se avisa al SEGUNDO fallo seguido, que ya no es mala suerte. Y si una fuente fallara en dias
            # alternos sin llegar nunca a dos seguidos, lo caza el aviso de serie caducada, que mira el dato y
            # no la descarga. Los tropiezos quedan apuntados y salen en el resumen de los lunes.
            if opcional or seguidos < 2:
                (soft_failures if opcional else pasajeros).append((name, msg))
            else:
                failures.append((name, msg))
            continue
        sstate["consecutive_failures"] = 0
        sstate["last_error"] = None
        sstate["last_success"] = storage.now_iso()
        for serie_id, pts in result.items():
            serie = catalog.get(serie_id)
            existing = storage.read_series(serie_id)
            v = validate_points(serie, pts, existing, backfill=backfill)
            if v.accepted:
                storage.write_series(serie_id, existing + v.accepted, serie.decimals)
                added_total += len(v.accepted)
            print(f"   {serie_id}: +{len(v.accepted)} (dup {v.duplicates}, rev {v.revisions}, "
                  f"backfill {v.backfilled}), rechazados {len(v.rejected)}")
            if v.rejected:
                quarantine.add(serie_id, v.rejected)
                quarantined.append(serie_id)
    stale = stale_series()
    contrasts = contrast.check_all()
    state["runs"].append({"started": started, "finished": storage.now_iso(), "collectors": names,
                          "added": added_total, "failures": [f[0] for f in failures],
                          "soft_failures": [f[0] for f in soft_failures],
                          "pasajeros": [f[0] for f in pasajeros],
                          "quarantined": quarantined, "stale": [s[0] for s in stale],
                          "contrast_alerts": contrasts})
    state["last_run"] = storage.now_iso()
    storage.save_state(state)
    if publish_after:
        publish.build_all()
    if notify and quarantined:
        quarantine.notify_batch(quarantined)
    if notify and (failures or stale or contrasts):
        alerts.send(format_problems(failures, stale, contrasts))
    print(f"\nResumen: +{added_total} puntos · fallos {len(failures)} · tropiezos de un dia {len(pasajeros)} · fallos de fuentes opcionales "
          f"{len(soft_failures)} · cuarentena {len(quarantined)} · caducadas {len(stale)} · "
          f"contrastes {len(contrasts)}")
    return 1 if failures else 0


def stale_series() -> list[tuple[str, int, int]]:
    """Series cuyo último dato es más viejo de lo tolerable: (id, días sin dato, días tolerados).

    Las series que no se publican (pendientes de autorización de la fuente) no cuentan: no hay nada roto en la web.
    """
    out = []
    for s in catalog.all_series():
        if not s.publishable:
            continue
        last = storage.last_point(s.id)
        if not last:
            out.append((s.id, -1, s.stale_after_days))
            continue
        age = (today() - parse_date(last[0])).days
        if age > s.stale_after_days:
            out.append((s.id, age, s.stale_after_days))
    return out


def format_problems(failures, stale, contrasts) -> str:
    lines = ["🔴 <b>Observatorio CPC: incidencias</b>"]
    if failures:
        lines.append("\n<b>Fallos de descarga</b> (la web sigue con el último dato bueno):")
        for name, msg in failures:
            lines.append(f"• {alerts.esc(name)}: {alerts.esc(msg[:200])}")
    if stale:
        lines.append("\n<b>Series sin datos nuevos</b> más tiempo del esperado:")
        for sid, age, tol in stale:
            s = catalog.get(sid)
            lines.append(f"• {alerts.esc(s.name['es'])} ({s.country}): "
                         + ("sin ningún dato" if age < 0 else f"{age} días (tolerancia {tol})"))
    if contrasts:
        lines.append("\n<b>Contraste entre fuentes</b> (mismo dato, valores que no cuadran):")
        for c in contrasts:
            lines.append(f"• {alerts.esc(c)}")
    return "\n".join(lines)


def _lena_con_reglas() -> str:
    """Por que la ultima lectura de la leña no uso la API, o cadena vacia si la uso."""
    try:
        import json

        from .collectors.lena import LENA_DIR
        d = json.loads((LENA_DIR / "ultimo_resumen.json").read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001 — sin fichero todavia o ilegible: no se inventa nada
        return ""
    return str(d.get("motivo_reglas") or "")


def weekly_summary() -> str:
    """Resumen 'todo va bien' con cifras, para saber que el sistema sigue vivo."""
    state = storage.load_state()
    series = catalog.all_series()
    ok = fresh = 0
    lines = []
    stale = {s[0] for s in stale_series()}
    for s in series:
        last = storage.last_point(s.id)
        if last:
            ok += 1
            if s.id not in stale:
                fresh += 1
    pend = quarantine.pending()
    runs = state.get("runs", [])[-7:]
    fails = sum(len(r.get("failures", [])) for r in runs)
    blandos = sorted({n for r in runs for n in r.get("soft_failures", [])})
    added = sum(r.get("added", 0) for r in runs)
    lines.append("🟢 <b>Observatorio CPC: resumen semanal</b>")
    lines.append(f"Series con datos: {ok}/{len(series)} · al día: {fresh} · caducadas: {len(stale)}")
    lines.append(f"Ejecuciones (7 últimas): {len(runs)} · puntos nuevos: {added} · fallos: {fails}")
    lines.append(f"En cuarentena pendientes: {len(pend)}" + (" ⚠️" if pend else ""))
    if blandos:
        lines.append("Fuentes opcionales que no responden (no se publican, no urge): "
                     + ", ".join(alerts.esc(b) for b in blandos))
    # Los tropiezos de un dia que se arreglaron solos no avisan, pero tampoco se esconden.
    pasajeros = sorted({n for r in runs for n in r.get("pasajeros", [])})
    if pasajeros:
        lines.append("Fuentes que fallaron un dia y volvieron solas: " + ", ".join(alerts.esc(b) for b in pasajeros))
    # El indice de la leña clasifica las fichas de las tiendas con la API de Claude y, si no puede, con reglas.
    # Se sigue publicando igual, asi que no es una incidencia y no despierta a nadie; pero si la clave caduca,
    # podria pasarse meses clasificando peor sin que se notara. Aqui se ve.
    motivo = _lena_con_reglas()
    if motivo:
        lines.append("🪵 El índice de la leña está clasificando <b>con reglas</b>, no con la API: "
                     + alerts.esc(motivo) + ". Se sigue publicando, pero las fichas nuevas se leen peor. "
                     "La clave es <code>ANTHROPIC_API_KEY</code>, en el secreto del repositorio.")
    if state.get("last_run"):
        lines.append(f"Última ejecución: {state['last_run'][:16].replace('T', ' ')} UTC")
    if not runs:
        lines.append("⚠️ No hay ejecuciones registradas esta semana: comprueba GitHub Actions.")
    # Cosas que hay que hacer en una fecha concreta. Un apunte en un documento no avisa a nadie y este resumen
    # ya llega al móvil; cada recordatorio tiene su ventana y desaparece solo cuando pasa.
    for texto in recordatorios.pendientes():
        lines.append("")
        lines.append(texto)
    return "\n".join(lines)
