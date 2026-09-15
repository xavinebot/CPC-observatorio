"""Eurostat (API JSON-stat, sin token): precios de electricidad y gas para hogares, HICP energía e índices de
precios industriales. Cada consulta trae el histórico completo.
"""
from __future__ import annotations

from ..util import http_get, save_raw
from .base import Collector as _Base

API = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/"
GEOS = ["ES", "FR", "IT", "DE", "PT", "AT"]


def jsonstat_points(d: dict, group_dim: str) -> dict[str, list[tuple]]:
    """Convierte una respuesta JSON-stat en {valor_de_group_dim: [(fecha, valor)]}. Las demás dimensiones
    deben tener tamaño 1 (ya filtradas en la consulta)."""
    ids = d["id"]
    sizes = d["size"]
    dims = d["dimension"]
    time_idx = ids.index("time")
    g_idx = ids.index(group_dim)
    for i, name in enumerate(ids):
        if name not in ("time", group_dim) and sizes[i] != 1:
            raise RuntimeError(f"Eurostat: la dimensión {name} tiene {sizes[i]} valores; la consulta debe fijarla")
    times = sorted(dims["time"]["category"]["index"].items(), key=lambda kv: kv[1])
    groups = sorted(dims[group_dim]["category"]["index"].items(), key=lambda kv: kv[1])
    # índice plano = suma(pos_i * stride_i) con strides "row-major"
    strides = [1] * len(sizes)
    for i in range(len(sizes) - 2, -1, -1):
        strides[i] = strides[i + 1] * sizes[i + 1]
    out: dict[str, list[tuple]] = {}
    values = d["value"]
    for g, gi in groups:
        pts = []
        for t, ti in times:
            flat = gi * strides[g_idx] + ti * strides[time_idx]
            v = values.get(str(flat))
            if v is None:
                continue
            pts.append((time_to_date(t), float(v)))
        out[g] = pts
    return out


def time_to_date(t: str) -> str:
    """'2025-S2' → '2025-07-01'; '2026-05' → '2026-05-01'; '2025' → '2025-01-01'."""
    if "-S" in t:
        y, s = t.split("-S")
        return f"{y}-{'01' if s == '1' else '07'}-01"
    if len(t) == 7:
        return t + "-01"
    return t[:4] + "-01-01"


def query(dataset: str, params: list[tuple]) -> dict:
    r = http_get(API + dataset, params=params + [("format", "JSON"), ("lang", "EN")])
    d = r.json()
    if "error" in d or "value" not in d:
        raise RuntimeError(f"Eurostat {dataset}: respuesta sin datos: {str(d)[:200]}")
    save_raw(f"eurostat_{dataset}_{params[0][1] if params else ''}.json", r.text)
    return d


class Nrg(_Base):
    name = "eurostat_nrg"
    min_records = 2 * 6 * 20

    def fetch(self, *, backfill: bool = False) -> dict[str, list[tuple]]:
        out = {}
        geo = [("geo", g) for g in GEOS]
        el = query("nrg_pc_204", geo + [("nrg_cons", "KWH2500-4999"), ("unit", "KWH"), ("tax", "I_TAX"), ("currency", "EUR")])
        for g, pts in jsonstat_points(el, "geo").items():
            out[f"electricidad_{g.lower()}"] = pts
        gas = query("nrg_pc_202", geo + [("nrg_cons", "GJ20-199"), ("unit", "KWH"), ("tax", "I_TAX"), ("currency", "EUR")])
        for g, pts in jsonstat_points(gas, "geo").items():
            out[f"gas_{g.lower()}"] = pts
        return out


class NrgInd(_Base):
    """Lo que paga una fábrica por la luz y el gas, no un hogar: bandas industriales y sin impuestos
    recuperables. Es el mayor coste de fundir vidrio y uno de los grandes de cualquier taller."""
    name = "eurostat_nrg_ind"
    min_records = 2 * 20

    def fetch(self, *, backfill: bool = False) -> dict[str, list[tuple]]:
        out = {}
        paises = [("geo", g) for g in GEOS if g != "AT"]
        el = query("nrg_pc_205", paises + [("nrg_cons", "MWH500-1999"), ("unit", "KWH"),
                                           ("tax", "X_TAX"), ("currency", "EUR")])
        for g, pts in jsonstat_points(el, "geo").items():
            out[f"electricidad_industria_{g.lower()}"] = pts
        gas = query("nrg_pc_203", paises + [("nrg_cons", "GJ1000-9999"), ("unit", "KWH"),
                                            ("tax", "X_TAX"), ("currency", "EUR")])
        for g, pts in jsonstat_points(gas, "geo").items():
            out[f"gas_industria_{g.lower()}"] = pts
        return out


class Hicp(_Base):
    """HICP ECOICOP v2 (prc_hicp_minr, dimension coicop18). El dataset antiguo prc_hicp_midx quedo congelado en
    2025-12. Una consulta por COICOP: la consulta conjunta devuelve 413 "asincrono". Espana no publica CP0454 ni
    CP04542 (combustibles solidos / lena y pellet)."""
    name = "eurostat_hicp"
    min_records = 4 * 6 * 100
    COICOP = {"CP0451": "electricidad", "CP0452": "gas", "CP0453": "comb_liquidos", "CP0454": "comb_solidos",
              "CP04542": "lena_pellet"}

    def fetch(self, *, backfill: bool = False) -> dict[str, list[tuple]]:
        out = {}
        for code, key in self.COICOP.items():
            geos = [g for g in GEOS if not (g == "ES" and code in ("CP0454", "CP04542"))]
            d = query("prc_hicp_minr", [("geo", g) for g in geos] + [("coicop18", code), ("unit", "I15")])
            for g, pts in jsonstat_points(d, "geo").items():
                out[f"hicp_{key}_{g.lower()}"] = pts
        return out


class Sts(_Base):
    name = "eurostat_sts"
    min_records = 6 * 50
    QUERIES = [
        ("C231", {"ES": "ipri_vidrio_es_eurostat", "FR": "ipri_vidrio_fr", "IT": "ipri_vidrio_it", "DE": "ipri_vidrio_de"}),
        ("C2752", {"DE": "ipri_aparatos_domesticos_de", "IT": "ipri_aparatos_domesticos_it"}),
        ("C275", {"FR": "ipri_aparatos_domesticos_fr"}),
        ("C241", {"DE": "ipri_siderurgia_de", "IT": "ipri_siderurgia_it", "FR": "ipri_siderurgia_fr"}),
        # Lo que compra un fabricante de chimeneas y estufas ademas del acero y el vidrio.
        # Lo que compra un fabricante de chimeneas, pais por pais. Portugal solo publica vidrio y electronica:
        # comprobado en Eurostat el 15 sep 2026, las demas ramas no las da para PT.
        # Radiadores y aislantes NO se piden para España: esas dos ya vienen del INE y una serie solo puede
        # tener un recolector. Pedirlas aquí sería escribir el mismo id desde dos fuentes distintas.
        ("C2521", {"FR": None, "IT": None, "DE": None}),
        ("C2399", {"FR": None, "IT": None, "DE": None}),
        # Portugal publica C26 congelado en 100,6 desde 2024 y sin dato desde junio de 2026: una linea plana
        # que no informa de nada. Comprobado el 15 sep 2026 y retirada; el vidrio portugues si es real.
        ("C26", {"ES": "ipri_electronica_es", "FR": None, "IT": None, "DE": None}),
        ("C2811", {"ES": "ipri_motores_es", "FR": None, "IT": None, "DE": None}),
        ("C2594", {"ES": "ipri_tornilleria_es", "FR": None, "IT": None, "DE": None}),
        ("C1721", {"ES": "ipri_carton_es", "FR": None, "IT": None, "DE": None}),
        ("C2012", {"ES": "ipri_pigmentos_es", "FR": None, "IT": None, "DE": None}),
        ("C231", {"PT": None}),                                         # vidrio en Portugal
    ]
    # Los None se rellenan con el id que toca: ipri_<rama>_<pais>. Se escribe una vez y no se repite en cada linea.
    RAMAS = {"C2521": "radiadores_calderas", "C2399": "aislantes_refractarios", "C26": "electronica",
             "C2811": "motores", "C2594": "tornilleria", "C1721": "carton", "C2012": "pigmentos", "C231": "vidrio"}

    def fetch(self, *, backfill: bool = False) -> dict[str, list[tuple]]:
        out = {}
        for nace, mapa in self.QUERIES:
            mapping = {g: (sid or f"ipri_{self.RAMAS[nace]}_{g.lower()}") for g, sid in mapa.items()}
            d = query("sts_inppd_m", [("geo", g) for g in mapping] + [("nace_r2", nace), ("s_adj", "NSA"),
                                                                       ("unit", "I21"), ("indic_bt", "PRC_PRR_DOM")])
            for g, pts in jsonstat_points(d, "geo").items():
                if g in mapping:
                    out[mapping[g]] = pts
        return out


COLLECTORS = {"eurostat_nrg": Nrg, "eurostat_nrg_ind": NrgInd, "eurostat_hicp": Hicp, "eurostat_sts": Sts}
Collector = Nrg
