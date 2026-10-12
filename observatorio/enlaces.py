"""Los enlaces que la web enseña, ¿siguen vivos?

Cada serie publica su fuente y su licencia con un enlace al original: es la mitad de la promesa del observatorio
—«cada cifra con su fuente y su fecha a la vista»— y la única forma que tiene un lector de comprobarnos. Un
enlace muerto no rompe nada visible, no da error en ninguna recogida y no lo nota nadie hasta que alguien lo
pulsa. Por eso se mira solo, una vez a la semana, con el resumen de los lunes.

Pasó el 12 de octubre de 2026 con dos: la CNMC reorganizó su portal y Eurostat movió su aviso de derechos. Las
descargas de datos seguían funcionando; lo que estaba roto era el enlace que enseñábamos.

**Solo se avisa de lo que es definitivo (404 y 410).** Un tiempo de espera agotado, un 500 o un 403 de un
cortafuegos que no quiere robots no son un enlace muerto, son un mal día, y avisar de eso enseña a no mirar los
avisos.
"""
from __future__ import annotations

import ssl
import urllib.error
import urllib.request

from . import catalog

UA = {"User-Agent": "Mozilla/5.0 (compatible; CPC-Observatorio/0.1; +https://cristalesparachimeneas.es/contacto/)"}
MUERTOS = (404, 410)   # definitivos: la dirección ya no existe
TIMEOUT = 20


def direcciones() -> dict[str, set[str]]:
    """Cada dirección que la web enseña → quién la usa. Solo de series publicadas."""
    out: dict[str, set[str]] = {}
    for s in catalog.all_series():
        if not s.publishable:
            continue
        out.setdefault(s.source.url, set()).add(s.source.name)
        if s.source.license_url:
            out.setdefault(s.source.license_url, set()).add(f"{s.source.name} (licencia)")
    return out


def _codigo(url: str) -> int | str:
    ctx = ssl.create_default_context()
    try:
        req = urllib.request.Request(url, headers=UA, method="GET")
        with urllib.request.urlopen(req, timeout=TIMEOUT, context=ctx) as r:
            return r.status
    except urllib.error.HTTPError as e:
        return e.code
    except Exception as e:  # noqa: BLE001 — sin red, DNS caído, certificado raro: no es un enlace muerto
        return type(e).__name__


def comprobar() -> list[tuple[str, int, list[str]]]:
    """Las direcciones definitivamente muertas, con quién las usa. Lista vacía = todo bien."""
    rotas = []
    for url, quien in sorted(direcciones().items()):
        c = _codigo(url)
        if c in MUERTOS:
            rotas.append((url, int(c), sorted(quien)))
    return rotas
