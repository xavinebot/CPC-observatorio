"""AVEBIOM, Índice de Precios de Biomasa: PDF trimestrales de pellet, hueso de aceituna y astilla.

Cada PDF trae la tabla "Precio medio anual" con las medias de cada año desde el inicio y los trimestres del año en
curso. Los PDF cambian de dirección cada trimestre, así que se localizan leyendo la página del índice; si la página
no se puede leer (ha pasado: desde los servidores de GitHub la web responde distinto que desde casa), se prueban
las direcciones previsibles del trimestre en curso y de los anteriores.

AUTORIZACIÓN: AVEBIOM autorizó la reproducción por correo el 14 de septiembre de 2026 (respuesta a la petición de
`CORREO-AVEBIOM.md`; el correo es el permiso escrito que exige su aviso legal). Condiciones que impone y que hay que
respetar al tocar esto:
  1. Citar AVEBIOM como fuente en cada gráfico y en cada tabla, con enlace al portal del índice
     (https://avebiom.org/actividades/indice-de-precios-biocombustibles-solidos/), no al PDF suelto.
  2. Indicar la fecha de la última actualización y que los precios llevan el 21 % de IVA.
  3. No modificar los datos. Por eso las series siguen con `redistributable=False`: no se ofrece CSV. AVEBIOM
     permite además enlazar su propio PDF o una gráfica suya, siempre con la cita del punto 1.
"""
from __future__ import annotations

import datetime as dt
import io
import re

import pdfplumber

from ..util import http_get, save_raw, today
from .base import Collector as _Base

# La primera dirección redirige a la segunda desde septiembre de 2026; se prueban las dos.
PAGES = [
    "https://avebiom.org/actividades/indice-de-precios-biocombustibles-solidos/",
    "https://www.avebiom.org/proyectos/indice-precios-biomasa-al-consumidor",
]
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/128.0 Safari/537.36 CPC-Observatorio/0.1 (+https://cristalesparachimeneas.es/contacto/)"}
QUARTER_MONTH = {"1": "01", "2": "04", "3": "07", "4": "10"}
KINDS = ("PELLET", "ASTILLA", "HUESO")


class Collector(_Base):
    name = "avebiom"
    min_records = 3 * 10
    optional = False  # desde el 14 sep 2026 su dato está publicado: si falla, es una incidencia de verdad

    def find_pdfs(self) -> dict[str, str]:
        """Busca los tres PDF en la página del índice; si no, prueba las direcciones previsibles."""
        errores = []
        for page in PAGES:
            try:
                html = http_get(page, headers=UA).text
            except Exception as e:  # noqa: BLE001
                errores.append(f"{page}: {type(e).__name__}")
                continue
            out = {}
            for kind in KINDS:
                # patrón normal y, por si cambian el nombre, cualquier PDF que mencione el combustible
                m = (re.search(rf'href="([^"]*IPB[^"]*{kind}[^"]*\.pdf)"', html, re.I)
                     or re.search(rf'href="([^"]*{kind}[^"]*\.pdf)"', html, re.I))
                if m:
                    out[kind] = m.group(1)
            if len(out) == 3:
                return out
            errores.append(f"{page}: solo {sorted(out)} ({len(html)} bytes)")
        # Plan B: la dirección sigue el patrón /wp-content/uploads/<año>/<mes>/IPB-indice-precios-<TIPO>-<n>T<año>.pdf
        adivinadas = self.probar_patron()
        if len(adivinadas) == 3:
            print(f"   avebiom: la página no listaba los PDF ({'; '.join(errores)}); uso las direcciones previsibles")
            return adivinadas
        raise RuntimeError("AVEBIOM: no encuentro los tres PDF del índice. " + "; ".join(errores))

    def probar_patron(self) -> dict[str, str]:
        """Prueba el trimestre en curso y los tres anteriores con el patrón conocido de nombres."""
        out: dict[str, str] = {}
        hoy = today()
        for atras in range(0, 4):
            mes = hoy.month - 3 * atras
            anyo = hoy.year
            while mes <= 0:
                mes += 12
                anyo -= 1
            trimestre = (mes - 1) // 3 + 1
            # el PDF se sube en el primer mes del trimestre siguiente
            subida = dt.date(anyo, mes, 1) + dt.timedelta(days=92)
            for carpeta in ({f"{subida.year}/{subida.month:02d}", f"{anyo}/{mes:02d}"}):
                for kind in KINDS:
                    if kind in out:
                        continue
                    url = (f"https://avebiom.org/wp-content/uploads/{carpeta}/"
                           f"IPB-indice-precios-{kind}-{trimestre}T{anyo}.pdf")
                    try:
                        r = http_get(url, headers=UA, retries=1)
                    except Exception:  # noqa: BLE001 — el 404 es lo normal al tantear
                        continue
                    if r.content[:4] == b"%PDF":
                        out[kind] = url
            if len(out) == 3:
                break
        return out

    def fetch(self, *, backfill: bool = False) -> dict[str, list[tuple]]:
        from ..catalog_series import AVB
        out = {}
        for kind, url in self.find_pdfs().items():
            content = http_get(url, headers=UA).content
            save_raw(f"avebiom_{kind}.pdf", content)
            text = pdf_text(content)
            for sid, (pdf, block, factor, _name, _kwh) in AVB.items():
                if pdf != kind:
                    continue
                annual, quarterly = parse_block(text, block, factor)
                out[sid] = quarterly
                out[sid + "_anual"] = annual
        return out


def pdf_text(content: bytes) -> str:
    with pdfplumber.open(io.BytesIO(content)) as pdf:
        return "\n".join((p.extract_text() or "") for p in pdf.pages[:3])


def parse_block(text: str, block: str, factor: float) -> tuple[list[tuple], list[tuple]]:
    """Devuelve (puntos anuales, puntos trimestrales) del bloque (p. ej. 'SACO de 15 kg') en €/kg."""
    lines = [l.strip() for l in text.splitlines()]
    # cabecera de años: "2012 2013 ... 2026 (1T) 2026 (2T)"
    header = None
    for l in lines:
        if re.match(r"^(19|20)\d\d(\s+(19|20)\d\d)+", l):
            header = l
            break
    if not header:
        raise RuntimeError("AVEBIOM: no encuentro la cabecera de años")
    cols = re.findall(r"(20\d\d)(?:\s*\((\d)T\))?", header)
    # línea de valores: para la astilla el bloque es la primera línea '€/tn'; para el resto va tras el rótulo
    values_line = None
    if block.startswith("Astilla"):
        values_line = next((l for l in lines if re.match(r"^€/tn\s", l)), None)
    else:
        for i, l in enumerate(lines):
            if l.upper().startswith(block.upper()):
                for j in range(i + 1, min(i + 4, len(lines))):
                    if re.match(r"^€/(saco|tn)\s", lines[j]):
                        values_line = lines[j]
                        break
                if values_line:
                    break
    if not values_line:
        raise RuntimeError(f"AVEBIOM: no encuentro los valores del bloque '{block}'")
    nums = [float(x.replace(".", "").replace(",", ".")) for x in re.findall(r"\d+(?:,\d+)?", values_line.split(" ", 1)[1])]
    if len(nums) != len(cols):
        raise RuntimeError(f"AVEBIOM: {len(nums)} valores para {len(cols)} columnas en '{block}'")
    annual, quarterly = [], []
    for (year, q), v in zip(cols, nums):
        if q:
            quarterly.append((f"{year}-{QUARTER_MONTH[q]}-01", v * factor))
        else:
            annual.append((f"{year}-01-01", v * factor))
    return annual, quarterly
