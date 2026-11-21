"""AVEBIOM, Índice de Precios de Biomasa: PDF trimestrales de pellet, hueso de aceituna y astilla.

Cada PDF trae la tabla "Precio medio anual" con las medias de cada año desde el inicio y los trimestres del año en
curso, y unas páginas después la tabla "Precio medio trimestral" con los cinco últimos trimestres (del mismo
trimestre del año anterior al actual). Se leen las dos: la primera da las medias anuales y los trimestres del año;
la segunda añade los trimestres del año anterior que la primera ya da como media anual, y con ellos se puede
calcular la variación de doce meses. Son valores que publica AVEBIOM tal cual, no cálculos nuestros.

Los PDF cambian de dirección cada trimestre, así que se localizan leyendo la página del índice; si la página
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
# Columnas de la tabla trimestral: "3T · 2025" (el punto medio a veces sale como "." o "-", o sin espacios)
TRIM_COL = re.compile(r"\b([1-4])\s*T\s*[·.\-]?\s*((?:19|20)\d\d)\b")
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
            out.update(parse_pdf(kind, pdf_pages(content), AVB))
        return out


def pdf_pages(content: bytes) -> list[str]:
    """Texto de cada página del PDF (la tabla trimestral está en la 4.ª o la 5.ª, según el combustible)."""
    with pdfplumber.open(io.BytesIO(content)) as pdf:
        return [(p.extract_text() or "") for p in pdf.pages]


def parse_pdf(kind: str, pages: list[str], series: dict) -> dict[str, list[tuple]]:
    """Puntos de todas las series de un PDF (`kind` = PELLET, HUESO o ASTILLA). `series` es `AVB` del catálogo."""
    annual_text = "\n".join(pages[:3])   # la tabla anual va en la 2.ª página; la 4.ª ya es un gráfico con años
    full_text = "\n".join(pages)
    out = {}
    for sid, (pdf, block, factor, _name, _kwh) in series.items():
        if pdf != kind:
            continue
        annual, quarterly = parse_block(annual_text, block, factor)
        # La tabla trimestral es un añadido: si un trimestre AVEBIOM cambia la maqueta y no se lee, se sigue con
        # la anual (que trae el trimestre en curso) y se apunta en el registro de la ejecución. Lo ya guardado
        # de trimestres anteriores no se pierde.
        try:
            extra = parse_trimestral(full_text, block, factor)
        except RuntimeError as e:
            print(f"   avebiom: {e}; sigo solo con la tabla anual")
            extra = []
        # Los trimestres del año en curso salen en las dos tablas. Con el mismo valor, queda un punto; si alguna
        # vez no coincidieran, van los dos y la validación los manda a cuarentena (fecha repetida con valores
        # distintos en el mismo lote): ante la duda no se publica ni se elige uno.
        out[sid] = sorted(set(quarterly) | set(extra))
        out[sid + "_anual"] = annual
    return out


def _numeros(values_line: str) -> list[float]:
    return [float(x.replace(".", "").replace(",", ".")) for x in re.findall(r"\d+(?:,\d+)?", values_line.split(" ", 1)[1])]


def _linea_de_valores(lines: list[str], block: str) -> str | None:
    """La línea '€/saco ...' o '€/tn ...' del bloque. La astilla tiene un solo bloque: su primera línea '€/tn'."""
    if block.startswith("Astilla"):
        return next((l for l in lines if re.match(r"^€/tn\s", l)), None)
    for i, l in enumerate(lines):
        if l.upper().startswith(block.upper()):
            for j in range(i + 1, min(i + 4, len(lines))):
                if re.match(r"^€/(saco|tn)\s", lines[j]):
                    return lines[j]
    return None


def parse_trimestral(text: str, block: str, factor: float) -> list[tuple]:
    """Puntos de la tabla "Precio medio trimestral" (cinco últimos trimestres) del bloque, en €/kg.

    Las filas se buscan con el mismo rótulo que en la tabla anual ("SACO de 15 kg", "PALET de sacos",
    "GRANEL en CISTERNA"; en la trimestral sale "GRANEL en cisterna", por eso se compara sin mayúsculas), así que
    cada serie lee el mismo producto y formato en las dos tablas. La fecha es el primer día del trimestre.
    """
    lines = [l.strip() for l in text.splitlines()]
    header = None
    for i, l in enumerate(lines):
        if not l.lower().startswith("precio medio trimestral"):
            continue
        # la cabecera de trimestres va justo debajo del título (en la astilla, tras el rótulo del producto)
        header = next((j for j in range(i + 1, min(i + 4, len(lines))) if len(TRIM_COL.findall(lines[j])) >= 2), None)
        if header is not None:
            break
    if header is None:
        raise RuntimeError("AVEBIOM: no encuentro la tabla «Precio medio trimestral»")
    cols = TRIM_COL.findall(lines[header])
    # la tabla acaba en el pie de página ("www.avebiom.org octubre 2026 5")
    end = next((j for j in range(header + 1, len(lines)) if lines[j].lower().startswith("www.")), len(lines))
    values_line = _linea_de_valores(lines[header + 1:end], block)
    if not values_line:
        raise RuntimeError(f"AVEBIOM: no encuentro los valores trimestrales del bloque '{block}'")
    nums = _numeros(values_line)
    if len(nums) != len(cols):
        raise RuntimeError(f"AVEBIOM: {len(nums)} valores para {len(cols)} trimestres en '{block}' (tabla trimestral)")
    return [(f"{year}-{QUARTER_MONTH[q]}-01", v * factor) for (q, year), v in zip(cols, nums)]


def parse_block(text: str, block: str, factor: float) -> tuple[list[tuple], list[tuple]]:
    """Devuelve (puntos anuales, puntos trimestrales) del bloque (p. ej. 'SACO de 15 kg') en €/kg."""
    lines = [l.strip() for l in text.splitlines()]
    # cabecera de años: "2012 2013 ... 2026 (1T) 2026 (2T)". También vale si solo trae trimestres
    # ("2026 (1T) 2026 (2T)"), que es como queda el extracto recortado de los tests.
    header = None
    for l in lines:
        if re.match(r"^(19|20)\d\d(\s*\(\dT\))?(\s+(19|20)\d\d(\s*\(\dT\))?)+", l):
            header = l
            break
    if not header:
        raise RuntimeError("AVEBIOM: no encuentro la cabecera de años")
    cols = re.findall(r"(20\d\d)(?:\s*\((\d)T\))?", header)
    # línea de valores: para la astilla el bloque es la primera línea '€/tn'; para el resto va tras el rótulo
    values_line = _linea_de_valores(lines, block)
    if not values_line:
        raise RuntimeError(f"AVEBIOM: no encuentro los valores del bloque '{block}'")
    nums = _numeros(values_line)
    if len(nums) != len(cols):
        raise RuntimeError(f"AVEBIOM: {len(nums)} valores para {len(cols)} columnas en '{block}'")
    annual, quarterly = [], []
    for (year, q), v in zip(cols, nums):
        if q:
            quarterly.append((f"{year}-{QUARTER_MONTH[q]}-01", v * factor))
        else:
            annual.append((f"{year}-01-01", v * factor))
    return annual, quarterly
