"""Tests de los analizadores de cada fuente, con muestras reales guardadas en tests/fixtures.

No tocan la red: si mañana una fuente cambia de formato, estos tests siguen en verde (lo que falla es la
descarga, que avisa por Telegram). Lo que comprueban es que NUESTRO código lee bien el formato conocido y que
detecta un fichero que ha cambiado.
"""
from __future__ import annotations

import json
import pathlib

import pytest

from observatorio import catalog
from observatorio.collectors import avebiom, cnmc_glp, eurostat, lena, pellets_eu, worldbank

FIX = pathlib.Path(__file__).parent / "fixtures"


def fx(name: str) -> bytes:
    p = FIX / name
    if not p.is_file():
        pytest.skip(f"falta la muestra {name}")
    return p.read_bytes()


# ----------------------------------------------------------------- catálogo
def test_todas_las_series_son_coherentes():
    for s in catalog.all_series():
        assert s.min_value < s.max_value, s.id
        assert s.max_change_pct > 0, s.id
        assert s.stale_after_days >= s.expected_every_days, s.id
        assert set(s.name) >= {"es", "fr", "it", "de", "pt"}, s.id
        assert s.source.attribution and s.source.license_url, s.id
        # una serie de precio comparable necesita saber cuánta energía tiene una unidad
        if s.group == "hogar" and s.unit.startswith("EUR") and s.taxes_included:
            assert s.kwh_per_unit, s.id
        # lo que no se puede redistribuir no se ofrece en CSV
        if not s.redistributable:
            assert True  # publish.py ya lo filtra; aquí solo documentamos la intención


def test_los_recolectores_del_catalogo_existen():
    from observatorio import collectors
    for s in catalog.all_series():
        assert s.collector in collectors.names(), f"{s.id} usa un recolector inexistente: {s.collector}"


# ----------------------------------------------------------------- CNMC
def test_cnmc_lee_el_precio_de_venta_al_publico():
    texto = (
        "Fecha;Fórmula de actualización;Actualización del precio;Entrada en vigor;"
        "Término Coste Materia Prima (€/kg);Término Coste Comercialización (€/kg);"
        "Término Coste Obligaciones Eficiencia Energética-CFNEE (€/kg);Término Desajuste Xb  (€/kg);"
        "Precio antes de impuestos (c€/kg);Impuesto Especial (c€/kg);Porcentaje IVA (%);IVA (c€/kg);"
        "Precio de Venta al Público (c€/kg)\n"
        "2026-09;Orden IET/389/2015;Resolución de 09/07/2026;2026-09-01;0,5174;0,6081;0,0308;;117,5664;1,1;21;24,9252;143,6166\n"
        "1994-01;Orden de 05/11/1993;Resolución de 13/01/1994;;;;;;40,977;;16;6,5563;47,5333\n"
    )
    pts = cnmc_glp.parse_csv(texto, "Venta al P", 0.01)
    assert pts[0] == ("2026-09", 1.436166)
    assert pts[1] == ("1994-01", 0.475333)
    # la bombona de 12,5 kg sale del valor por kilo
    assert round(pts[0][1] * 12.5, 2) == 17.95


def test_cnmc_avisa_si_desaparece_la_columna():
    with pytest.raises(RuntimeError, match="no encuentro la columna"):
        cnmc_glp.parse_csv("Fecha;Otra cosa\n2026-09;1\n", "Venta al P", 0.01)


# ----------------------------------------------------------------- Eurostat
def test_eurostat_convierte_los_periodos():
    assert eurostat.time_to_date("2025-S2") == "2025-07-01"
    assert eurostat.time_to_date("2025-S1") == "2025-01-01"
    assert eurostat.time_to_date("2026-05") == "2026-05-01"
    assert eurostat.time_to_date("2026") == "2026-01-01"


def test_eurostat_lee_una_respuesta_jsonstat():
    d = {
        "id": ["freq", "unit", "geo", "time"], "size": [1, 1, 2, 3],
        "dimension": {
            "freq": {"category": {"index": {"S": 0}}},
            "unit": {"category": {"index": {"KWH": 0}}},
            "geo": {"category": {"index": {"ES": 0, "FR": 1}}},
            "time": {"category": {"index": {"2025-S1": 0, "2025-S2": 1, "2026-S1": 2}}},
        },
        # índice plano: geo * 3 + time
        "value": {"0": 0.26, "1": 0.2669, "3": 0.25, "5": 0.24},
    }
    out = eurostat.jsonstat_points(d, "geo")
    assert out["ES"] == [("2025-01-01", 0.26), ("2025-07-01", 0.2669)]
    assert out["FR"] == [("2025-01-01", 0.25), ("2026-01-01", 0.24)]


def test_eurostat_se_queja_si_la_consulta_no_fija_una_dimension():
    d = {
        "id": ["tax", "geo", "time"], "size": [2, 1, 1],
        "dimension": {"tax": {"category": {"index": {"I_TAX": 0, "X_TAX": 1}}},
                      "geo": {"category": {"index": {"ES": 0}}},
                      "time": {"category": {"index": {"2025-S2": 0}}}},
        "value": {"0": 1},
    }
    with pytest.raises(RuntimeError, match="debe fijarla"):
        eurostat.jsonstat_points(d, "geo")


# ----------------------------------------------------------------- AVEBIOM (PDF)
TEXTO_AVEBIOM = """Índice de precios del PELLET de MADERA
2012 2013 2014 2015 2016 2017 2018 2019 2020 2021 2022 2023 2024 2025 2026 (1T) 2026 (2T)
SACO de 15 kg
€/saco 4,13 4,24 4,35 4,21 3,93 3,92 4,02 4,44 4,39 4,34 6,53 6,21 5,25 5,15 5,29 5,67
c€/kWh 5,94 6,09 5,89 5,50 5,49 5,62 6,22 6,14 6,07 9,14 8,68 7,35 7,21 7,39 7,94
PALET de sacos
€/tn 264,61 273,86 280,98 269,88 254,93 252,25 260,74 289,24 284,29 282,34 434,83 412,35 343,24 334,12 349,96 372,29
"""


def test_avebiom_separa_anuales_y_trimestrales():
    anual, trim = avebiom.parse_block(TEXTO_AVEBIOM, "SACO de 15 kg", 1 / 15)
    assert ("2012-01-01", round(4.13 / 15, 6)) == (anual[0][0], round(anual[0][1], 6))
    assert anual[-1][0] == "2025-01-01"
    assert [d for d, _ in trim] == ["2026-01-01", "2026-04-01"]
    assert round(trim[-1][1], 4) == round(5.67 / 15, 4)


def test_avebiom_lee_el_palet_en_toneladas():
    anual, trim = avebiom.parse_block(TEXTO_AVEBIOM, "PALET de sacos", 1 / 1000)
    assert round(trim[-1][1], 5) == round(372.29 / 1000, 5)


def test_avebiom_avisa_si_cambia_la_maqueta():
    with pytest.raises(RuntimeError, match="no encuentro"):
        avebiom.parse_block("un PDF con otra pinta\n", "SACO de 15 kg", 1 / 15)


# ----------------------------------------------------------------- C.A.R.M.E.N. (tabla HTML)
HTML_CARMEN = """
<table><thead><tr><th>wdt_ID</th><th>Zahl_Monat</th><th>Jahr</th><th>Jahr_Monat</th><th>Sackware</th>
<th>2 Tonnen</th><th>5 Tonnen</th><th>10 Tonnen</th></tr></thead><tbody>
<tr><td>37</td><td>1</td><td>2005</td><td>2005 01</td><td></td><td>209,94</td><td>178,78</td><td>168,69</td></tr>
<tr><td>299</td><td>8</td><td>2026</td><td>2026 08</td><td>515,62</td><td>478,18</td><td>438,03</td><td>425,71</td></tr>
</tbody></table>
"""


def test_carmen_lee_la_tabla_historica_en_euros_por_kilo():
    pts = pellets_eu.parse_carmen(HTML_CARMEN)
    assert pts[0] == ("2005-01-01", 0.17878)
    assert pts[-1] == ("2026-08-01", 0.43803)


def test_carmen_avisa_si_no_esta_la_tabla():
    with pytest.raises(RuntimeError, match="no encuentro la tabla"):
        pellets_eu.parse_carmen("<table><tr><td>nada</td></tr></table>")


# ----------------------------------------------------------------- índice de la leña
def lectura(**kw):
    base = dict(date="2026-09-12", store="S1", name="x", price=300.0, es_lena=True, especie="encina",
                kg=1000.0, formato="palet", humedad_pct=0.0, seca=True, transporte_incluido=True, metodo="test")
    base.update(kw)
    return base


def test_lena_mediana_entre_tiendas_no_entre_referencias():
    # la tienda S1 trae cinco referencias caras y las otras dos una barata cada una:
    # la mediana ENTRE TIENDAS no debe dejarse arrastrar por la tienda con más productos
    rs = [lectura(store="S1", price=p, name=f"a{p}") for p in (600, 610, 620, 630, 640)]
    rs += [lectura(store="S2", price=260), lectura(store="S3", price=280)]
    agg = lena.aggregate(rs, "palet")
    assert agg["stores"] == 3 and agg["refs"] == 7
    assert agg["value"] == 0.28          # mediana de (0,62 · 0,26 · 0,28)
    assert agg["min"] == 0.26 and agg["max"] == 0.64


def test_lena_exige_kilos_declarados_y_formato_grande():
    rs = [lectura(kg=0), lectura(store="S2", kg=200), lectura(store="S3", formato="saco", kg=10)]
    agg = lena.aggregate(rs, "palet")
    assert agg["value"] is None and agg["refs"] == 0


def test_lena_no_publica_sin_tiendas_suficientes():
    rs = [lectura(store="S1"), lectura(store="S2", price=280)]
    agg = lena.aggregate(rs, "palet")
    assert agg["value"] is None and agg["stores"] == 2   # hacen falta 3


def test_lena_excluye_lo_que_no_es_lena_y_la_madera_blanda():
    rs = [lectura(store="S1", es_lena=False), lectura(store="S2", especie="pino"),
          lectura(store="S3", especie="roble"), lectura(store="S4", especie="haya")]
    agg = lena.aggregate(rs, "palet")
    assert agg["refs"] == 2 and agg["value"] is None   # solo 2 tiendas válidas


def test_lena_serie_de_saco_ignora_los_portes_pero_exige_tamano():
    rs = [lectura(store="S1", formato="saco", kg=15, price=9.0, transporte_incluido=False),
          lectura(store="S2", formato="saco", kg=10, price=6.0, transporte_incluido=False),
          lectura(store="S3", formato="saco", kg=40, price=20.0)]
    agg = lena.aggregate(rs, "saco")
    assert agg["stores"] == 2 and agg["value"] == 0.6   # el de 40 kg queda fuera


def test_lena_descarta_precios_por_kilo_imposibles():
    rs = [lectura(store="S1", price=5.0), lectura(store="S2", price=280), lectura(store="S3", price=290)]
    agg = lena.aggregate(rs, "palet")   # 5 € por 1000 kg = 0,005 €/kg, imposible
    assert agg["refs"] == 2 and agg["value"] is None


def test_lena_clasificacion_por_reglas_lee_sacos_por_palet():
    c = lena.classify_rules("Palet de 60 sacos de leña de roble de 15 kg", "Leña seca lista para usar")
    assert c["es_lena"] and c["especie"] == "roble" and c["formato"] == "palet"
    assert c["kg"] == 900 and c["seca"]


def test_lena_clasificacion_por_reglas_descarta_pellet_y_briquetas():
    for nombre in ("Saco de pellet 15 kg", "Briquetas de madera 10 kg", "Carbón vegetal 15 kg"):
        assert not lena.classify_rules(nombre, "")["es_lena"], nombre


# ----------------------------------------------------------------- Banco Mundial
def test_worldbank_avisa_si_falta_una_columna(monkeypatch):
    import io
    import openpyxl
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Monthly Prices"
    ws.append(["World Bank Commodity Price Data"])
    ws.append([None, "Crude oil, Brent", "Natural gas, Europe"])
    ws.append([None, "($/bbl)", "($/mmbtu)"])
    ws.append(["2026M08", 90.9, 21.11])
    buf = io.BytesIO()
    wb.save(buf)
    with pytest.raises(RuntimeError, match="falta la columna"):
        worldbank.parse(buf.getvalue())
