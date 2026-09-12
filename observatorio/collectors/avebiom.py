"""AVEBIOM, Índice de Precios de Biomasa: PDF trimestrales de pellet, hueso de aceituna y astilla.

Cada PDF trae la tabla "Precio medio anual" con las medias de cada año desde el inicio y los trimestres del año
en curso. Se localizan los PDF en la página del índice (las URL cambian cada trimestre) y se extrae el texto de la
página 2 con pdfplumber.

IMPORTANTE: las series quedan marcadas `publishable=False` hasta que AVEBIOM autorice por escrito la
reproducción (su aviso legal lo exige). Se recolectan para tener el histórico listo el día que llegue el permiso.
"""
from __future__ import annotations

import io
import re

import pdfplumber

from .. import catalog
from ..util import http_get, save_raw
from .base import Collector as _Base

PAGE = "https://www.avebiom.org/proyectos/indice-precios-biomasa-al-consumidor"
UA = {"User-Agent": "Mozilla/5.0 (compatible; CPC-Observatorio/0.1; +https://cristalesparachimeneas.es/contacto/)"}
QUARTER_MONTH = {"1": "01", "2": "04", "3": "07", "4": "10"}


class Collector(_Base):
    name = "avebiom"
    min_records = 3 * 10

    def find_pdfs(self) -> dict[str, str]:
        html = http_get(PAGE, headers=UA).text
        out = {}
        for kind in ("PELLET", "HUESO", "ASTILLA"):
            m = re.search(rf'href="([^"]*IPB-indice-precios-{kind}[^"]*\.pdf)"', html, re.I)
            if m:
                out[kind] = m.group(1)
        if len(out) < 3:
            raise RuntimeError(f"AVEBIOM: solo encuentro PDF de {list(out)} en la página del índice")
        return out

    def fetch(self, *, backfill: bool = False) -> dict[str, list[tuple]]:
        out = {}
        specs = {}
        for s in catalog.by_collector(self.name):
            if s.id.endswith("_anual"):
                continue
            specs[s.id] = s
        from ..catalog_series import AVB
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
