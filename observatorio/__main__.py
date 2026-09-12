"""Línea de comandos del observatorio.

  python -m observatorio run [--only nombre ...] [--backfill] [--no-notify]
  python -m observatorio status
  python -m observatorio approve <serie_id> | discard <serie_id>
  python -m observatorio summary        (envía el resumen semanal)
  python -m observatorio test-alert     (aviso de prueba por Telegram)
  python -m observatorio publish        (regenera los JSON sin descargar nada)
"""
from __future__ import annotations

import argparse
import sys

from . import alerts, catalog, collectors, publish, quarantine, runner, storage


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="observatorio")
    sub = p.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run", help="recolectar, validar, publicar y avisar")
    r.add_argument("--only", nargs="*", help="solo estos recolectores")
    r.add_argument("--backfill", action="store_true", help="aceptar puntos anteriores al último (carga de histórico)")
    r.add_argument("--no-notify", action="store_true")
    r.add_argument("--no-publish", action="store_true")
    sub.add_parser("status")
    a = sub.add_parser("approve")
    a.add_argument("serie_id")
    d = sub.add_parser("discard")
    d.add_argument("serie_id")
    sub.add_parser("summary")
    sub.add_parser("test-alert")
    sub.add_parser("publish")
    sub.add_parser("list", help="lista recolectores y series")
    args = p.parse_args(argv)

    if args.cmd == "run":
        unknown = [n for n in (args.only or []) if n not in collectors.names()]
        if unknown:
            print("Recolectores desconocidos:", unknown, "· disponibles:", collectors.names())
            return 2
        return runner.run(args.only, backfill=args.backfill, publish_after=not args.no_publish,
                          notify=not args.no_notify)
    if args.cmd == "status":
        state = storage.load_state()
        print(f"Última ejecución: {state.get('last_run', '-')}")
        stale = {s[0]: s for s in runner.stale_series()}
        for s in catalog.all_series():
            last = storage.last_point(s.id)
            flag = "CADUCADA" if s.id in stale and last else ("SIN DATOS" if not last else "ok")
            print(f"{s.id:32} {s.country:3} {flag:9} último: {last[0] if last else '-'} "
                  f"{last[1] if last else ''} {s.unit}")
        pend = quarantine.pending()
        print(f"\nEn cuarentena: {len(pend)}")
        for q in pend:
            print(f"  {q['serie']}: {len(q['points'])} puntos, p. ej. {q['points'][0]}")
        print("\nFallos recientes:")
        for name, st in state.get("series", {}).items():
            if st.get("consecutive_failures"):
                print(f"  {name}: {st['consecutive_failures']} seguidos · {st.get('last_error')}")
        return 0
    if args.cmd == "approve":
        n = quarantine.approve(args.serie_id)
        print(f"Aprobados {n} puntos")
        publish.build_all()
        return 0
    if args.cmd == "discard":
        n = quarantine.discard(args.serie_id)
        print(f"Descartados {n} puntos")
        return 0
    if args.cmd == "summary":
        txt = runner.weekly_summary()
        print(txt)
        alerts.send(txt)
        return 0
    if args.cmd == "test-alert":
        ok = alerts.send("🧪 <b>Observatorio CPC</b>: aviso de prueba. Si lees esto, el canal funciona.",
                         buttons=[[{"text": "👍 Recibido", "callback_data": "ack:test"}]])
        print("enviado" if ok else "NO enviado (falta TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID)")
        return 0 if ok else 1
    if args.cmd == "publish":
        publish.build_all()
        print("JSON publicados en data/published/")
        return 0
    if args.cmd == "list":
        print("Recolectores:", collectors.names())
        for s in catalog.all_series():
            print(f"  {s.id:32} {s.country} {s.group:9} {s.unit:12} cada {s.expected_every_days}d  {s.source.name}")
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
