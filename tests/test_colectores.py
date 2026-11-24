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
from observatorio.collectors import ademe_bois, avebiom, cnmc_glp, eurostat, lena, pellets_eu, sdes_bois, worldbank

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
    pts = dict(cnmc_glp.parse_csv(texto, "Venta al P", 0.01))
    assert pts["2026-09"] == 1.436166
    assert pts["1994-01"] == 0.475333
    # la bombona de 12,5 kg sale del valor por kilo
    assert round(pts["2026-09"] * 12.5, 2) == 17.95


def test_cnmc_mes_con_dos_revisiones_se_queda_con_la_vigente():
    """El butano cambia a veces dos veces en el mismo mes: vale la ultima que entro en vigor.

    Paso de verdad en septiembre de 2026: el fichero traia el precio del dia 1 (1,4362 EUR/kg) y el del dia 15
    (1,5073), se guardaba uno u otro segun el orden del fichero, y la web enseño durante dias un precio que ya
    no estaba en vigor.
    """
    texto = """Fecha;Entrada en vigor;Precio de Venta al Público (c€/kg)
2026-09;2026-09-15;150,7293
2026-09;2026-09-01;143,6166
2026-03;2026-03-17;130,8448
2026-03;2026-03-22;117,2998
"""
    pts = dict(cnmc_glp.parse_csv(texto, "Venta al P", 0.01))
    assert len(pts) == 2, "un solo valor por mes"
    assert pts["2026-09"] == 1.507293
    assert pts["2026-03"] == 1.172998, "el orden del fichero no decide: decide la fecha de entrada en vigor"


def test_cnmc_sin_columna_de_vigor_se_queda_con_la_primera_fila_del_mes():
    # El fichero del GLP canalizado no trae "Entrada en vigor" y viene ordenado del reves (lo mas nuevo arriba).
    texto = """Fecha;A CONSUMIDOR FINAL Término variable (c€/kg)
2026-09;90,6022
2026-09;80,0000
"""
    pts = dict(cnmc_glp.parse_csv(texto, "rmino variable", 0.01))
    assert pts["2026-09"] == 0.906022


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


# Muestras reales, RECORTADAS: el texto que pdfplumber saca de los tres PDF del 3T·2026 (octubre de 2026), una
# página por salto de página (\f). El repositorio es público y AVEBIOM no permite redistribuir sus datos, así que
# solo quedan las filas que usamos y los cinco trimestres que ya están en data/series (ver la cabecera de cada
# fichero). La tabla anual se queda con sus columnas de 2026: sin medias anuales.
def paginas_avebiom(kind: str) -> list[str]:
    return fx(f"avebiom_{kind}_3T2026.txt").decode("utf-8").split("\f")


def redondeado(pts, dec=4):
    return [(d, round(v, dec)) for d, v in pts]


def test_avebiom_tabla_trimestral_del_pellet():
    from observatorio.catalog_series import AVB
    out = avebiom.parse_pdf("PELLET", paginas_avebiom("PELLET"), AVB)
    fechas = ["2025-07-01", "2025-10-01", "2026-01-01", "2026-04-01", "2026-07-01"]
    # saco de 15 kg: 5,12 5,31 5,29 5,67 5,92 €/saco → /15
    assert redondeado(out["pellet_saco_es"], 6) == list(zip(fechas, [round(x / 15, 6) for x in (5.12, 5.31, 5.29, 5.67, 5.92)]))
    # palet: 335,66 345,20 349,96 372,29 390,75 €/t → /1000
    assert redondeado(out["pellet_palet_es"], 6) == list(zip(fechas, [0.33566, 0.3452, 0.34996, 0.37229, 0.39075]))
    # granel en CISTERNA, que es lo que dice el catálogo (la fila de volquete no se usa)
    assert redondeado(out["pellet_granel_es"], 6) == list(zip(fechas, [0.33358, 0.34644, 0.36113, 0.36648, 0.38221]))
    # el extracto no trae medias anuales (la lectura de las anuales la prueban los tests de arriba)
    assert out["pellet_saco_es_anual"] == []


def test_avebiom_tabla_trimestral_del_hueso_y_la_astilla():
    from observatorio.catalog_series import AVB
    hueso = avebiom.parse_pdf("HUESO", paginas_avebiom("HUESO"), AVB)
    # granel en cisterna: 223,92 232,09 244,0 258,96 256,33 €/t
    assert redondeado(hueso["hueso_granel_es"], 6) == [
        ("2025-07-01", 0.22392), ("2025-10-01", 0.23209), ("2026-01-01", 0.244),
        ("2026-04-01", 0.25896), ("2026-07-01", 0.25633)]
    astilla = avebiom.parse_pdf("ASTILLA", paginas_avebiom("ASTILLA"), AVB)
    # 145,72 145,80 150,83 149,42 149,78 €/t
    assert redondeado(astilla["astilla_es"], 6) == [
        ("2025-07-01", 0.14572), ("2025-10-01", 0.1458), ("2026-01-01", 0.15083),
        ("2026-04-01", 0.14942), ("2026-07-01", 0.14978)]


def test_avebiom_las_dos_tablas_coinciden_en_los_trimestres_del_ano():
    # 1T, 2T y 3T de 2026 salen en la tabla anual y en la trimestral; en esta edición valen lo mismo y queda un
    # solo punto por fecha (si no coincidieran irían los dos y la validación los mandaría a cuarentena).
    from observatorio.catalog_series import AVB
    for kind in ("PELLET", "HUESO", "ASTILLA"):
        paginas = paginas_avebiom(kind)
        texto = "\n".join(paginas)
        for sid, (pdf, block, factor, _n, _k) in AVB.items():
            if pdf != kind:
                continue
            _anual, del_anio = avebiom.parse_block("\n".join(paginas[:3]), block, factor)
            trim = dict(avebiom.parse_trimestral(texto, block, factor))
            for d, v in del_anio:
                assert trim[d] == v, (sid, d)


def test_avebiom_sin_tabla_trimestral_sigue_con_la_anual(capsys):
    from observatorio.catalog_series import AVB
    paginas = paginas_avebiom("PELLET")[:3]     # sin la página de la tabla trimestral
    out = avebiom.parse_pdf("PELLET", paginas, AVB)
    assert [d for d, _ in out["pellet_saco_es"]] == ["2026-01-01", "2026-04-01", "2026-07-01"]
    assert "Precio medio trimestral" in capsys.readouterr().out


def test_avebiom_tabla_trimestral_con_columnas_que_no_cuadran():
    texto = "Precio medio trimestral para el PELLET\n3T · 2025 4T · 2025 1T · 2026\nSACO de 15 kg\n€/saco 5,12 5,31\n"
    with pytest.raises(RuntimeError, match="2 valores para 3 trimestres"):
        avebiom.parse_trimestral(texto, "SACO de 15 kg", 1 / 15)


def test_avebiom_los_trimestres_antiguos_entran_por_la_carga_de_historico():
    # Lo que ya está guardado (1T-3T 2026) cuenta como duplicado; los dos trimestres de 2025 son anteriores al
    # último punto, así que la recogida diaria los mandaría a cuarentena y la carga con --backfill los acepta
    # pasando el resto de reglas (rango, revisiones).
    import datetime as dt

    from observatorio.catalog_series import AVB
    from observatorio.validate import validate_points
    serie = catalog.get("pellet_saco_es")
    guardado = [("2026-01-01", 0.3527), ("2026-04-01", 0.378), ("2026-07-01", 0.3947)]
    nuevos = avebiom.parse_pdf("PELLET", paginas_avebiom("PELLET"), AVB)["pellet_saco_es"]
    hoy = dt.date(2026, 11, 21)
    diario = validate_points(serie, nuevos, guardado, reference=hoy)
    assert [r.date for r in diario.rejected] == ["2025-07-01", "2025-10-01"]
    carga = validate_points(serie, nuevos, guardado, backfill=True, reference=hoy)
    assert carga.rejected == [] and carga.backfilled == 2
    # los de 2026 vuelven como "revisión" solo porque el CSV guarda 4 decimales (5,29/15 = 0,35266…): al
    # escribirlos se redondean y el fichero no cambia
    assert {d for d, _ in carga.accepted} >= {"2025-07-01", "2025-10-01"}
    assert all(round(v, 4) == dict(guardado)[d] for d, v in carga.accepted if d in dict(guardado))


# ----------------------------------------------------------------- SDES (Francia, pellet de los hogares)
# Muestra real recortada de la entrega 2026-11: cabeceras, los cuatro meses vacíos del final (jul-oct 2026), doce
# trimestres con dato (3T 2023 a 2T 2026), los tres primeros de 2007 y tres meses vacíos de 2006.
def sdes_csv() -> str:
    return fx("sdes_bois_2026-11.csv").decode("utf-8-sig")


def test_sdes_un_punto_por_trimestre_en_euros_por_kilo():
    pts = sdes_bois.parse_csv(sdes_csv(), sdes_bois.columnas())
    granel, saco = dict(pts["pellet_granel_fr"]), dict(pts["pellet_saco_fr"])
    # 387,68 y 385,23 €/t en abril, mayo y junio de 2026 → un solo punto, el 1 de abril
    assert granel["2026-04-01"] == 0.38768 and saco["2026-04-01"] == 0.38523
    assert granel["2026-01-01"] == 0.38271 and saco["2026-01-01"] == 0.36768
    # los €/t con cuatro decimales de los primeros años se guardan tal cual
    assert granel["2007-01-01"] == 0.2179495 and saco["2007-04-01"] == 0.2526252
    # 12 trimestres recientes + 3 de 2007, sin fechas repetidas y sin nada de los meses vacíos
    for serie in (pts["pellet_granel_fr"], pts["pellet_saco_fr"]):
        assert len(serie) == 15 and len({d for d, _ in serie}) == 15
        assert serie[0][0] == "2007-01-01" and serie[-1][0] == "2026-04-01"
        assert all(d[5:7] in ("01", "04", "07", "10") and d.endswith("-01") for d, _ in serie)


def test_sdes_trimestre_con_meses_distintos_va_a_cuarentena():
    """Si un trimestre trajera tres valores distintos, no se promedia ni se elige: van todos con la misma fecha y la
    validación los manda a cuarentena (fecha repetida en el lote). Caso inventado a partir de la muestra."""
    import datetime as dt

    from observatorio.validate import validate_points
    texto = sdes_csv().replace('"2026-05";387.68;385.23', '"2026-05";390.00;385.23')
    pts = sdes_bois.parse_csv(texto, sdes_bois.columnas())
    assert sorted(v for d, v in pts["pellet_granel_fr"] if d == "2026-04-01") == [0.38768, 0.39]
    assert [v for d, v in pts["pellet_saco_fr"] if d == "2026-04-01"] == [0.38523]   # la otra no se toca
    res = validate_points(catalog.get("pellet_granel_fr"), pts["pellet_granel_fr"], [], backfill=True,
                          reference=dt.date(2026, 11, 21))
    assert {r.date for r in res.rejected} == {"2026-04-01"}
    assert {r.reason for r in res.rejected} == {"fecha_duplicada_en_el_lote"}
    assert len(res.accepted) == 14


def test_sdes_avisa_si_cambia_el_fichero():
    texto = sdes_csv()
    with pytest.raises(RuntimeError, match="PX_BOIS_GRANSACS_TONNE"):
        sdes_bois.parse_csv(texto.replace("PX_BOIS_GRANSACS_TONNE", "PX_BOIS_SACS"), sdes_bois.columnas())
    with pytest.raises(RuntimeError, match="no en euros TTC"):
        sdes_bois.parse_csv(texto.replace('"n/a";"euros TTC"', '"n/a";"euros HT"'), sdes_bois.columnas())
    with pytest.raises(RuntimeError, match="PERIODE"):
        sdes_bois.parse_csv("\n".join(texto.splitlines()[3:]), sdes_bois.columnas())


def test_sdes_la_muestra_recortada_no_pasa_la_comprobacion():
    # La muestra solo trae 15 trimestres; una descarga así de corta es un fichero recortado, no un dato.
    pts = sdes_bois.parse_csv(sdes_csv(), sdes_bois.columnas())
    with pytest.raises(RuntimeError, match="registros|trimestres"):
        sdes_bois.Collector().check(pts)


def test_sdes_toma_la_ultima_entrega_de_la_ficha():
    meta = json.loads(fx("sdes_dataset_2026-11.json"))
    assert sdes_bois.ultimo_millesime(meta) == "2026-11"
    # con varias entregas, la más reciente (la ficha real de hoy solo trae una; se añade otra para probarlo)
    fich = next(f for f in meta["datafiles"] if f["rid"] == sdes_bois.DATAFILE)
    fich["millesimes"] = [{"millesime": "2026-10"}, *fich["millesimes"], {"millesime": "2025-12"}]
    assert sdes_bois.ultimo_millesime(meta) == "2026-11"
    meta["datafiles"] = [f for f in meta["datafiles"] if f["rid"] != sdes_bois.DATAFILE]
    with pytest.raises(RuntimeError, match="no trae entregas"):
        sdes_bois.ultimo_millesime(meta)


def test_sdes_la_comparativa_lleva_el_saco_como_en_espana():
    assert catalog.get("pellet_saco_fr").en_comparativa is True
    assert catalog.get("pellet_granel_fr").en_comparativa is False
    assert catalog.get("pellet_saco_es").en_comparativa is True
    assert catalog.get("pellet_granel_es").en_comparativa is False
    for sid in ("pellet_saco_fr", "pellet_granel_fr"):
        s = catalog.get(sid)
        assert s.redistributable and s.publishable and s.taxes_included and s.kwh_per_unit == 4.76


# ----------------------------------------------------------------- ADEME (leña de Francia, JSON de data-fair)
def ademe_lineas() -> dict:
    return json.loads(fx("ademe_bois_lineas_2026-11.json"))


def test_ademe_un_punto_al_ano_en_euros_por_mwh_tal_cual():
    pts = ademe_bois.parse_lines(ademe_lineas(), ademe_bois.productos())
    serie = pts["lena_buche_fr"]
    # de 2005 a 2025, un punto por año, fechado el 1 de enero, sin huecos y sin convertir nada
    assert len(serie) == 21 and serie[0] == ("2005-01-01", 28.0) and serie[-1] == ("2025-01-01", 47.0)
    d = dict(serie)
    assert d["2010-01-01"] == 33.0 and d["2024-01-01"] == 46.5 and d["2023-01-01"] == 46.0
    assert ademe_bois.Collector().check(pts) is None


def test_ademe_un_precio_a_cero_es_un_dato_que_falta():
    """En 2010 el precio CON entrega viene a 0 en todos los combustibles: no es gratis, es que no está."""
    pts = ademe_bois.parse_lines(ademe_lineas(), {"x": ("Bûches de 33 cm", "prix_livre")})
    fechas = [d for d, _ in pts["x"]]
    assert "2010-01-01" not in fechas and len(fechas) == 20
    assert all(v > 0 for _, v in pts["x"])


def test_ademe_dos_filas_del_mismo_ano_van_a_cuarentena():
    """Caso inventado a partir de la muestra: si un año trae dos valores, no se elige uno."""
    import datetime as dt

    from observatorio.validate import validate_points
    d = ademe_lineas()
    d["results"].append({"annee": 2025, "type_combustible": "Bûches de 33 cm", "prix_non_livre": 48, "prix_livre": 48})
    pts = ademe_bois.parse_lines(d, ademe_bois.productos())["lena_buche_fr"]
    assert sorted(v for f, v in pts if f == "2025-01-01") == [47.0, 48.0]
    res = validate_points(catalog.get("lena_buche_fr"), pts, [], backfill=True, reference=dt.date(2026, 11, 21))
    assert {r.date for r in res.rejected} == {"2025-01-01"} and len(res.accepted) == 20


def test_ademe_avisa_si_cambia_el_conjunto():
    d = ademe_lineas()
    with pytest.raises(RuntimeError, match="Bûches 33 cm"):
        ademe_bois.parse_lines(d, {"x": ("Bûches 33 cm", "prix_non_livre")})
    sin_col = {"total": d["total"], "results": [{k: v for k, v in f.items() if k != "prix_non_livre"}
                                                 for f in d["results"]]}
    with pytest.raises(RuntimeError, match="prix_non_livre"):
        ademe_bois.parse_lines(sin_col, ademe_bois.productos())
    with pytest.raises(RuntimeError, match="recortada"):
        ademe_bois.parse_lines({"total": 170, "results": d["results"][:20]}, ademe_bois.productos())
    # una descarga con pocos años no pasa la comprobación
    corta = ademe_bois.parse_lines({"total": 9, "results": [f for f in d["results"] if f["annee"] >= 2017][:9 * 9]},
                                   ademe_bois.productos())
    with pytest.raises(RuntimeError, match="registros|años"):
        ademe_bois.Collector().check(corta)


def test_ademe_busca_el_conjunto_por_su_titulo_y_su_licencia():
    cat = json.loads(fx("ademe_catalogo_2026-11.json"))
    # en el catálogo real hay también el de chauffage collectif, que se busca con las mismas palabras
    assert ademe_bois.buscar_conjunto(cat).endswith("/datasets/prix-bois-domestique")
    fich = next(d for d in cat["results"] if d["title"] == ademe_bois.TITULO)
    fich["license"] = {"title": "Tous droits réservés"}
    with pytest.raises(RuntimeError, match="licencia"):
        ademe_bois.buscar_conjunto(cat)
    cat["results"] = [d for d in cat["results"] if d["title"] != ademe_bois.TITULO]
    with pytest.raises(RuntimeError, match="no encuentro"):
        ademe_bois.buscar_conjunto(cat)


def test_ademe_la_lena_de_francia_va_a_la_comparativa_en_su_unidad():
    s = catalog.get("lena_buche_fr")
    assert s.unit == "EUR/MWh" and s.kwh_per_unit == 1000.0 and s.fuel == "lena" and s.native_freq == "A"
    assert s.redistributable and s.publishable and s.en_comparativa and s.country == "FR"


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


def _fix_json(nombre):
    import json as _json
    from pathlib import Path as _Path
    return _json.loads((_Path(__file__).parent / "fixtures" / nombre).read_text(encoding="utf-8"))


def test_propellets_granel_de_centimos_a_euros_por_kilo_desde_2006():
    pts = pellets_eu.parse_23degrees(_fix_json("propellets_granel_datos_2026-11.json"), por_kg=100.0)
    assert pts[0][0] == "2006-01-01"                      # lo de 2005 no entra: la recogida sistemática empieza en 2006
    assert abs(pts[0][1] - 0.1778) < 0.001                 # 17,78 céntimos el kilo en enero de 2006
    assert pts[-1][0] == "2026-11-01"
    assert abs(pts[-1][1] - 0.447734) < 0.00001          # 44,77 céntimos el kilo = 447,73 € la tonelada (su web)


def test_propellets_saco_de_15_kg_a_euros_por_kilo():
    pts = pellets_eu.parse_23degrees(_fix_json("propellets_saco_datos_2026-11.json"), por_kg=15.0)
    assert pts[0][0] == "2021-11-01"
    assert pts[-1][0] == "2026-11-01"
    assert abs(pts[-1][1] * 15 - 7.4228) < 0.001         # 7,42 € el saco, como en su web


def test_propellets_no_lee_si_el_grafico_deja_de_decir_con_iva():
    ficha = _fix_json("propellets_granel_grafico_2026-11.json")
    assert pellets_eu.id_datos(ficha) == "6af958785e4c1fc4f7b543fb"
    import json as _json
    sin_iva = _json.loads(_json.dumps(ficha).replace("inkl. USt", "ohne USt"))
    with pytest.raises(RuntimeError, match="inkl. USt"):
        pellets_eu.id_datos(sin_iva)


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


# ----------------------------------------------------------------- CNMC: el conjunto se busca por titulo
class _Resp:
    def __init__(self, payload):
        self._p = payload
    def json(self):
        return self._p


def test_cnmc_distingue_dos_conjuntos_de_titulo_parecido(monkeypatch):
    """«Estadistica GLP - Precio GLP envasado regulado» NO es «Precio GLP envasado regulado de Venta al Publico».

    Coexisten en el catalogo de la CNMC, se buscan con las mismas palabras y traen columnas distintas. Si se
    coge el que no es, se publica otro dato con la misma cara.
    """
    bueno = "https://catalogodatos.cnmc.es/x/bueno.csv"
    respuesta = {"result": {"results": [
        {"title": "Precio GLP envasado regulado de Venta al Público",
         "resources": [{"format": "CSV", "url": "https://catalogodatos.cnmc.es/x/otro.csv"}]},
        {"title": "Estadística GLP - Precio GLP envasado regulado",
         "resources": [{"format": "CSV", "url": bueno}]},
    ]}}
    monkeypatch.setattr(cnmc_glp, "http_get", lambda *a, **k: _Resp(respuesta))
    url, del_catalogo = cnmc_glp.Collector().resolve_csv("Estadística GLP - Precio GLP envasado regulado")
    assert url == bueno
    assert del_catalogo is True


def test_cnmc_si_el_catalogo_no_responde_usa_la_ultima_que_funciono(monkeypatch, tmp_path):
    """La CNMC renumera (dos veces en tres semanas). La direccion aprendida es la red, no una URL escrita a mano.

    Una URL fija en el codigo envejece y el dia que muere nadie se acuerda de donde estaba; la aprendida se
    actualiza sola cada vez que el catalogo responde.
    """
    import json as _json
    cache = tmp_path / "cnmc_urls.json"
    cache.write_text(_json.dumps({"Precio GLP Canalizado (antes de impuestos)": "https://x/ayer.csv"}),
                     encoding="utf-8")
    monkeypatch.setattr(cnmc_glp, "CACHE_URLS", cache)
    def caido(*a, **k):
        raise RuntimeError("catalogo caido")
    monkeypatch.setattr(cnmc_glp, "http_get", caido)
    url, del_catalogo = cnmc_glp.Collector().resolve_csv("Precio GLP Canalizado (antes de impuestos)")
    assert url == "https://x/ayer.csv"
    assert del_catalogo is False, "no se reaprende de una direccion vieja: solo el catalogo enseña"

    # y si no hay ni catalogo ni memoria, se dice en voz alta en vez de inventarse nada
    cache.unlink()
    with pytest.raises(RuntimeError, match="no hay dirección guardada"):
        cnmc_glp.Collector().resolve_csv("Precio GLP Canalizado (antes de impuestos)")


# ----------------------------------------------------------------- que ningun recolector se quede sin correr
def test_la_recogida_diaria_no_se_deja_ningun_recolector():
    """Un recolector que no corre no falla: sus series se quedan congeladas y nadie se entera.

    Paso de verdad: comext (6 materias primas) y eurostat_nrg_ind (10 series de energia industrial) se dieron de
    alta el 15 de septiembre de 2026 en el catalogo, pero no en la lista del workflow diario. Estuvieron cinco
    semanas publicando el mismo dato sin que fallara nada, y solo salto cuando el aviso de serie caducada llego
    a los 110 dias. Las otras diez habrian tardado un año y medio en avisar, porque son semestrales.

    Por eso el workflow dice ahora "todos salvo la leña" en vez de enumerar los que si. Este test comprueba que
    sigue siendo asi: si alguien vuelve a poner una lista fija, salta aqui y no cinco semanas despues.
    """
    import re
    from pathlib import Path

    from observatorio import collectors

    wf = Path(__file__).resolve().parents[1] / ".github" / "workflows" / "observatorio.yml"
    texto = wf.read_text(encoding="utf-8")
    orden = re.search(r"run:\s*python -m observatorio run([^\n]*)", texto)
    assert orden, "no encuentro la orden de recogida en el workflow diario"
    args = orden.group(1)

    assert "--only" not in args, (
        "el workflow diario vuelve a llevar una lista fija de recolectores: cada uno nuevo habria que "
        "acordarse de añadirlo aqui, y cuando se olvida sus series se congelan en silencio. Usa --salvo.")
    assert "--salvo" in args, "la recogida diaria tiene que ser 'todos salvo los que tienen su propio horario'"

    excluidos = args.split("--salvo", 1)[1].split("--")[0].split()
    for n in excluidos:
        assert n in collectors.names(), f"el workflow excluye '{n}', que no es un recolector"
    # la lena tiene su propio workflow los lunes; cualquier otra exclusion hay que justificarla aqui
    assert set(excluidos) == {"lena"}, f"exclusiones sin justificar en el workflow diario: {excluidos}"


# ----------------------------------------------------------------- AIEL (Italia), autorizado el 24-11-2026
def test_aiel_cumple_las_cuatro_condiciones():
    """Las condiciones del correo de AIEL, fijadas: si alguien las toca, este test lo para."""
    from observatorio.collectors import aiel
    ids = [s for s in catalog.all_series() if s.collector == "aiel"]
    assert {s.id for s in ids} == {"pellet_saco_it", "pellet_granel_it", "lena_a1_it"}
    pts = aiel.leer(aiel.fichero().read_text(encoding="utf-8"))
    for s in ids:
        # 1. cita con enlace directo a su página de precios (no a la portada ni a un artículo)
        assert s.source.url == "https://energiadallegno.it/tag/prezzibiocombustibili/", s.id
        assert "AIEL" in s.source.attribution, s.id
        # 2. todo con IVA (las mediciones sin IVA no entran)
        assert s.taxes_included is True, s.id
        # 3. cada dato con su mes de medición: enero, abril o septiembre, como mide AIEL
        assert pts[s.id] and all(d[5:7] in ("01", "04", "09") and d.endswith("-01") for d, _ in pts[s.id]), s.id
        # 4. que no se pueda descargar: sin CSV / marcado / incrustar / PNG, y fuera de la imagen de la comparativa
        assert s.redistributable is False and s.sin_descarga is True and s.publishable is True, s.id
        assert s.country == "IT", s.id   # solo en la página italiana


def test_aiel_no_cruza_el_cambio_de_metodo_del_granel():
    from observatorio.collectors import aiel
    pts = aiel.leer(aiel.fichero().read_text(encoding="utf-8"))
    assert min(d for d, _ in pts["pellet_granel_it"]) >= "2025-01-01"


def test_aiel_rechaza_una_medicion_sin_iva():
    from observatorio.collectors import aiel
    texto = ("serie,medicion,valor,unidad,iva,publicado,articulo,tabla\n"
             "pellet_saco_it,2023-09,6.5,EUR/sacco15kg,esclusa,2023-10-26,https://energiadallegno.it/x/,Tabella 1\n")
    with pytest.raises(RuntimeError, match="IVA"):
        aiel.leer(texto)


def test_aiel_pasa_el_saco_a_kilo_y_la_tonelada_a_kilo():
    from observatorio.collectors import aiel
    texto = ("serie,medicion,valor,unidad,iva,publicado,articulo,tabla\n"
             "pellet_saco_it,2026-09,7.61,EUR/sacco15kg,inclusa,2026-10-13,https://energiadallegno.it/a/,Tabella 1\n"
             "lena_a1_it,2026-09,258.6,EUR/t,inclusa,2026-10-13,https://energiadallegno.it/b/,Tabella 1\n")
    p = aiel.leer(texto)
    assert round(p["pellet_saco_it"][0][1] * 15, 2) == 7.61 and p["pellet_saco_it"][0][0] == "2026-09-01"
    assert p["lena_a1_it"][0][1] == pytest.approx(0.2586)


def test_aiel_detecta_una_medicion_nueva_sin_cargar():
    from observatorio.collectors import aiel
    html = ('<a href="https://energiadallegno.it/prezzo-del-pellet-a-gennaio-2027/">x</a>'
            '<a href="https://energiadallegno.it/prezzo-della-legna-da-ardere-ad-aprile-2026/">y</a>'
            '<a href="https://energiadallegno.it/prezzo-del-pellet-in-autobotte-a-settembre-2022/">z</a>')
    assert aiel.ultima_publicada(html) == "2027-01"


def test_aiel_sin_csv_al_publicar():
    from observatorio import publish
    s = catalog.get("pellet_saco_it")
    p = publish.serie_payload(s, [("2026-09-01", 0.5073)])
    assert p["redistributable"] is False and p["sin_descarga"] is True
