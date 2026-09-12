"""Índice de precio de la leña en España: elaboración propia a partir de precios PÚBLICOS de tiendas online.

Reglas (ver FUENTES.md y DECISIONES.md):
  - Solo tiendas cuyo robots.txt y aviso legal permiten la lectura automatizada; se comprueba robots.txt en cada
    ejecución y la tienda se salta si deja de permitirlo. No se sortea ningún bloqueo (si una tienda devuelve 403 a
    nuestro User-Agent identificado, queda fuera).
  - Pocas peticiones, despacio (pausa entre páginas), User-Agent identificado con contacto. Donde la tienda ofrece
    una API pública de catálogo (WooCommerce Store API, Shopify products.json) se usa en vez de leer fichas.
  - Se publican AGREGADOS (mediana entre tiendas), nunca una tabla de precios por tienda con nombre.
  - Las lecturas individuales se guardan en data/lena/lecturas.csv con un código de tienda (S1…), sin URL.
  - La interpretación de cada producto (especie, kg, formato, humedad) la hace la API de Claude a partir del texto de
    la ficha, con caché por contenido (solo se paga cuando aparece un producto nuevo o cambia). Sin clave de API se
    usa un análisis por reglas más tosco.
  - Los kilos tienen que estar DECLARADOS por el vendedor (en el nombre, la opción o la descripción). Nunca se
    estiman a partir de litros o m³.
"""
from __future__ import annotations

import csv
import hashlib
import html as htmlmod
import json
import re
import statistics
import time
import urllib.robotparser
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from .. import config
from ..util import http_get, save_raw, today
from .base import Collector as _Base

UA = "CPC-Observatorio/0.1 (+https://cristalesparachimeneas.es/contacto/; recogida semanal de precios publicos de lena)"
HEADERS = {"User-Agent": UA, "Accept-Language": "es-ES,es;q=0.9"}
PAUSE = 4.0
LENA_DIR = config.DATA / "lena"
CACHE_FILE = LENA_DIR / "clasificacion_cache.json"
READINGS_FILE = LENA_DIR / "lecturas.csv"
HARDWOOD = {"encina", "roble", "olivo", "haya", "carrasca", "algarrobo", "naranjo", "quejigo", "fresno", "almendro", "alcornoque", "nogal"}

# Tiendas: código público, dominio, cómo se leen y si el precio visible incluye el transporte a península.
STORES = [
    {"code": "S1", "home": "https://tiendabiomasa.com/", "kind": "magento",
     "pages": ["https://tiendabiomasa.com/lena/lenagranel.html", "https://tiendabiomasa.com/lena/lenaempaquetada.html"],
     "transport_included": True, "note": "envío gratis a península a partir de un palet (los sacos sueltos pagan envío)"},
    {"code": "S2", "home": "https://llenyespolinya.cat/", "kind": "woo_api", "category": "lena",
     "transport_included": True, "note": "envíos a toda la península; confirmar que el precio del palet incluye el porte"},
    {"code": "S3", "home": "https://xn--leasonline-u9a.com/", "kind": "woo_api", "search": "leña",
     "transport_included": True, "note": "envío gratuito a península"},
    {"code": "S4", "home": "https://tienda.ertasa.es/", "kind": "shopify",
     "transport_included": True, "note": "precios incluyen envío a península y Baleares; solo pino"},
    {"code": "S6", "home": "https://mipelletymas.com/", "kind": "woo_api", "search": "leña",
     "transport_included": False, "note": "precios con IVA; coste de envío no visible → solo serie 'saco'"},
]


# ----------------------------------------------------------------------------- utilidades
def robots_ok(store: dict, url: str) -> bool:
    rp = urllib.robotparser.RobotFileParser()
    try:
        r = http_get(urljoin(store["home"], "/robots.txt"), headers=HEADERS, retries=1)
        rp.parse(r.text.splitlines())
    except Exception:  # noqa: BLE001 — sin robots.txt legible: se asume permitido (comportamiento estándar)
        return True
    return rp.can_fetch(UA, url) and rp.can_fetch("*", url)


def get(url: str) -> str:
    time.sleep(PAUSE)
    return http_get(url, headers=HEADERS, retries=2).text


def clean_text(s: str, limit: int = 1500) -> str:
    s = htmlmod.unescape(re.sub(r"<[^>]+>", " ", s or ""))
    s = re.sub(r"\s+", " ", s).strip()
    if len(s) <= limit:
        return s
    # nos quedamos con el principio y con las frases que hablan de peso/kilos
    frases = [f for f in re.split(r"(?<=[.:;])\s", s) if re.search(r"\bkg\b|kilo|peso", f, re.I)]
    return (s[:700] + " … " + " ".join(frases))[:limit]


# ----------------------------------------------------------------------------- extractores
def extract_magento(store: dict) -> list[dict]:
    """Listado Magento: productos simples con precio en el listado; configurables → se lee la ficha (opciones)."""
    items = []
    for url in store["pages"]:
        html = get(url)
        save_raw(f"lena_{store['code']}_{hashlib.sha1(url.encode()).hexdigest()[:8]}.html", html)
        soup = BeautifulSoup(html, "html.parser")
        for li in soup.select(".product-item"):
            a = li.select_one(".product-item-link")
            if not a:
                continue
            name, href = a.get_text(strip=True), a.get("href", "")
            price = li.select_one("[data-price-amount]")
            if price:
                try:
                    items.append({"name": name, "price": float(price["data-price-amount"]), "text": li.get_text(" ", strip=True)[:400]})
                    continue
                except (KeyError, ValueError):
                    pass
            if href:
                items += magento_product(href, name)
    return items


def magento_product(url: str, name: str) -> list[dict]:
    html = get(url)
    soup = BeautifulSoup(html, "html.parser")
    desc = clean_text(" ".join(str(x) for x in soup.select(".product.attribute.description, .product-info-main .value, .product.info.detailed")))
    cfg = None

    def walk(o):
        nonlocal cfg
        if cfg is not None:
            return
        if isinstance(o, dict):
            if "optionPrices" in o and "attributes" in o:
                cfg = o
                return
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)

    for sc in soup.find_all("script", type="text/x-magento-init"):
        try:
            walk(json.loads(sc.string or ""))
        except (ValueError, TypeError):
            continue
    items = []
    if cfg:
        for attr in cfg["attributes"].values():
            for opt in attr.get("options", []):
                for pid in opt.get("products", []):
                    p = cfg["optionPrices"].get(pid, {}).get("finalPrice", {}).get("amount")
                    if p:
                        items.append({"name": f"{name} · {attr.get('label', '')}: {opt.get('label', '')}", "price": float(p), "text": desc})
    else:
        price = soup.select_one('[itemprop="price"]')
        if price and price.get("content"):
            items.append({"name": name, "price": float(price["content"]), "text": desc})
    return items


def extract_woo_api(store: dict) -> list[dict]:
    """WooCommerce Store API (pública, solo lectura): /wp-json/wc/store/v1/products."""
    base = store["home"].rstrip("/") + "/wp-json/wc/store/v1/products"
    url = base + "?per_page=100" + (f"&search={store['search']}" if store.get("search") else "")
    raw = get(url)
    save_raw(f"lena_{store['code']}_api.json", raw)
    prods = json.loads(raw)
    items = []
    for p in prods:
        if store.get("category") and store["category"] not in [c.get("slug") for c in p.get("categories", [])]:
            continue
        minor = int(p["prices"].get("currency_minor_unit", 2))
        text = clean_text((p.get("short_description") or "") + " " + (p.get("description") or ""))
        name = htmlmod.unescape(p.get("name", ""))
        if p.get("type") == "variable" and p.get("variations"):
            for v in p["variations"][:8]:
                try:
                    vr = json.loads(get(f"{base}/{v['id']}"))
                    price = float(vr["prices"]["price"]) / (10 ** minor)
                except Exception:  # noqa: BLE001
                    continue
                attrs = ", ".join(a.get("value", "") for a in v.get("attributes", []))
                items.append({"name": f"{name} · {attrs}", "price": price, "text": text})
        else:
            try:
                price = float(p["prices"]["price"]) / (10 ** minor)
            except (KeyError, ValueError, TypeError):
                continue
            items.append({"name": name, "price": price, "text": text})
    return items


def extract_shopify(store: dict) -> list[dict]:
    raw = get(store["home"].rstrip("/") + "/products.json?limit=50")
    save_raw(f"lena_{store['code']}_api.json", raw)
    items = []
    for prod in json.loads(raw).get("products", []):
        body = clean_text(prod.get("body_html") or "", 800)
        for v in prod.get("variants", []):
            try:
                p = float(v["price"])
            except (KeyError, ValueError):
                continue
            if p <= 0:
                continue
            grams = v.get("grams") or 0
            extra = f" Peso declarado por la tienda: {grams / 1000:g} kg." if grams else ""
            items.append({"name": f"{prod.get('title', '')} · {v.get('title', '')}", "price": p, "text": body + extra})
    return items


EXTRACTORS = {"magento": extract_magento, "woo_api": extract_woo_api, "shopify": extract_shopify}


# ----------------------------------------------------------------------------- clasificación (Claude o reglas)
SCHEMA = {
    "type": "object",
    "properties": {
        "es_lena": {"type": "boolean", "description": "true si el producto es leña (troncos, tacos o rajas de madera para quemar). false para briquetas, pellet, carbón, astillas, cortezas, encendedores, cuadradillos para pizzería, etc."},
        "especie": {"type": "string", "description": "encina, roble, olivo, haya, carrasca, algarrobo, naranjo, alcornoque, pino, mezcla (si mezcla de maderas duras), desconocida"},
        "kg": {"type": "number", "description": "kilos totales que se compran por ese precio, según lo DECLARADO por el vendedor (nombre, opción elegida o descripción, incluido 'peso aproximado'). Si el nombre dice N sacos y la descripción el peso de cada saco, multiplica. Si solo hay litros o m3 sin kilos, pon 0. Nunca estimes."},
        "formato": {"type": "string", "enum": ["palet", "saca", "saco", "caja", "otro"], "description": "palet (también 'palet con caja' o 'palet de sacos'), saca/big bag, saco pequeño (≤ 30 kg), caja, otro"},
        "humedad_pct": {"type": "number", "description": "humedad declarada en %, 0 si no se indica"},
        "seca": {"type": "boolean", "description": "true si se declara seca, secada, lista para usar, o humedad <= 20 %"},
    },
    "required": ["es_lena", "especie", "kg", "formato", "humedad_pct", "seca"],
}


def classify_rules(name: str, text: str) -> dict:
    s = f"{name} {text}".lower()
    m = re.search(r"(\d{1,4}(?:[.,]\d{1,3})?)\s*kg", name.lower()) or re.search(r"peso aproximado:?\s*(\d{2,4})\s*kg", s)
    kg = float(m.group(1).replace(".", "").replace(",", ".")) if m else 0.0
    n = re.search(r"(\d{1,3})\s*(?:sacos|paquetes|unidades|uds)\b", name.lower())
    if n and kg and kg <= 30:
        kg = kg * float(n.group(1))
    especie = next((e for e in sorted(HARDWOOD | {"pino", "mezcla"}) if e in s), "desconocida")
    formato = "palet" if "palet" in s or "pallet" in s else ("saca" if "saca" in s or "big bag" in s else ("saco" if "saco" in s or "malla" in s or "paquete" in s else "otro"))
    hum = re.search(r"(\d{1,2})\s*%", s)
    es_lena = ("leña" in s or "lena" in s or "llenya" in s) and not any(x in s for x in ("briqueta", "pellet", "carbón", "carbon ", "astilla", "encend", "corteza", "cuadradillo"))
    return {"es_lena": bool(es_lena), "especie": especie, "kg": kg, "formato": formato,
            "humedad_pct": float(hum.group(1)) if hum else 0.0, "seca": ("seca" in s) or ("secad" in s)}


def classify_claude(name: str, text: str) -> dict | None:
    key = config.secret("ANTHROPIC_API_KEY")
    if not key:
        return None
    try:
        import anthropic
    except ImportError:
        return None
    client = anthropic.Anthropic(api_key=key)
    prompt = (f"Ficha de una tienda online española de leña.\nNombre (con la opción elegida): {name}\nTexto de la ficha: {text}\n\n"
              "Extrae los datos con la herramienta. Los kilos solo si están declarados por el vendedor; si no, 0.")
    try:
        msg = client.messages.create(
            model="claude-haiku-4-5-20251001", max_tokens=300,
            tools=[{"name": "ficha_lena", "description": "Datos estructurados de una ficha de leña", "input_schema": SCHEMA}],
            tool_choice={"type": "tool", "name": "ficha_lena"},
            messages=[{"role": "user", "content": prompt}])
        for block in msg.content:
            if getattr(block, "type", "") == "tool_use":
                return dict(block.input)
    except Exception as e:  # noqa: BLE001
        print(f"   lena: API de Claude no disponible ({type(e).__name__}); uso reglas")
    return None


def classify(name: str, text: str, cache: dict) -> dict:
    h = hashlib.sha1(f"{name}|{text}".encode("utf-8")).hexdigest()[:16]
    if h in cache:
        return cache[h]
    res = classify_claude(name, text)
    method = "claude"
    if res is None:
        res = classify_rules(name, text)
        method = "reglas"
    res["_metodo"] = method
    cache[h] = res
    return res


# ----------------------------------------------------------------------------- recolector
MIN_STORES = {"palet": 3, "saco": 2}
MIN_KG_PALET = 500   # por debajo de media tonelada el precio por kilo no es comparable (palets pequenos)


class Collector(_Base):
    name = "lena"
    min_records = 1
    supports_backfill = False

    def fetch(self, *, backfill: bool = False) -> dict[str, list[tuple]]:
        LENA_DIR.mkdir(parents=True, exist_ok=True)
        cache = json.loads(CACHE_FILE.read_text(encoding="utf-8")) if CACHE_FILE.is_file() else {}
        date = today().isoformat()
        readings = []
        stores_ok = []
        for store in STORES:
            try:
                first = store.get("pages", [store["home"]])[0]
                if not robots_ok(store, first):
                    print(f"   lena: {store['code']} robots.txt no permite la lectura; se salta la tienda")
                    continue
                items = EXTRACTORS[store["kind"]](store)
            except Exception as e:  # noqa: BLE001 — una tienda caída no tumba el índice
                print(f"   lena: {store['code']} no leída ({type(e).__name__}: {str(e)[:120]})")
                continue
            if items:
                stores_ok.append(store["code"])
            for it in items:
                c = classify(it["name"], it["text"], cache)
                readings.append({"date": date, "store": store["code"], "name": it["name"][:120], "price": it["price"],
                                 **{k: c.get(k) for k in ("es_lena", "especie", "kg", "formato", "humedad_pct", "seca")},
                                 "transporte_incluido": store["transport_included"], "metodo": c.get("_metodo", "")})
        CACHE_FILE.write_text(json.dumps(cache, ensure_ascii=False, indent=0), encoding="utf-8")
        append_readings(readings)
        print(f"   lena: {len(readings)} lecturas de {len(stores_ok)} tiendas {stores_ok}")
        out = {}
        stats = {"date": date, "stores_read": stores_ok, "readings": len(readings), "series": {}}
        for kind, sid in (("palet", "lena_palet_es"), ("saco", "lena_saco_es")):
            agg = aggregate(readings, kind)
            stats["series"][sid] = agg
            if agg["value"] is not None:
                out[sid] = [(date, agg["value"])]
        (LENA_DIR / "ultimo_resumen.json").write_text(json.dumps(stats, ensure_ascii=False, indent=1), encoding="utf-8")
        if not out:
            raise RuntimeError(f"leña: sin tiendas suficientes para publicar ({stats})")
        print(f"   lena: {stats['series']}")
        return out


def aggregate(readings: list[dict], kind: str) -> dict:
    """Mediana entre tiendas del €/kg; dentro de cada tienda, la mediana de sus referencias válidas.

    Devuelve un diccionario con el valor y la dispersión (mínimo y máximo entre referencias válidas), porque en la
    leña la horquilla es muy ancha: cambian la especie, la longitud del leño y el tamaño del palet. Enseñar solo la
    mediana daría una falsa sensación de precisión.
    """
    per_store: dict[str, list[float]] = {}
    for r in readings:
        if not r.get("es_lena") or not r.get("kg"):
            continue
        kg = float(r["kg"])
        if kind == "palet":
            if r.get("especie") not in HARDWOOD | {"mezcla"} or kg < MIN_KG_PALET or r.get("formato") not in ("palet", "saca"):
                continue
            if not r.get("transporte_incluido"):
                continue
        else:
            if kg < 8 or kg > 25 or r.get("formato") not in ("saco", "caja", "otro"):
                continue
        eur_kg = float(r["price"]) / kg
        if not (0.05 <= eur_kg <= 3.0):
            continue
        per_store.setdefault(r["store"], []).append(eur_kg)
    todos = [v for vals in per_store.values() for v in vals]
    out = {"value": None, "stores": len(per_store), "refs": len(todos),
           "min": round(min(todos), 4) if todos else None, "max": round(max(todos), 4) if todos else None}
    if len(per_store) >= MIN_STORES[kind]:
        out["value"] = round(statistics.median(statistics.median(v) for v in per_store.values()), 4)
    return out


def append_readings(readings: list[dict]) -> None:
    """Anade las lecturas al registro historico, sin repetir una misma referencia el mismo dia."""
    if not readings:
        return
    ya = set()
    if READINGS_FILE.is_file():
        with READINGS_FILE.open(encoding="utf-8", newline="") as f:
            for row in csv.DictReader(f):
                ya.add((row.get("date"), row.get("store"), row.get("name")))
    readings = [r for r in readings if (r["date"], r["store"], r["name"]) not in ya]
    if not readings:
        return
    new = not READINGS_FILE.is_file()
    with READINGS_FILE.open("a", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(readings[0].keys()), lineterminator="\n")
        if new:
            w.writeheader()
        for r in readings:
            w.writerow(r)
