"""Definiciones de todas las series (ver FUENTES.md para el porqué de cada fuente y su licencia).

Convención de ids: <concepto>_<pais en minúsculas>. Unidades: EUR/l, EUR/kg, EUR/kWh, índice.
"""
from .catalog import Serie, Source, register

COUNTRIES = ["ES", "FR", "IT", "DE", "PT", "AT"]


def N(es, fr, it, de, pt):
    return {"es": es, "fr": fr, "it": it, "de": de, "pt": pt}


# ----------------------------------------------------------------------------- fuentes
SRC_WOB = Source(
    # El nombre es el oficial y nada más: aparece en las cinco páginas y el paréntesis que llevaba antes
    # ("datos comunicados por los Estados miembros; España: MITECO") era una explicación en español que se colaba
    # sin traducir en la francesa, la italiana, la alemana y la portuguesa. Eso se cuenta en FUENTES.md.
    name="Comisión Europea, Weekly Oil Bulletin",
    url="https://energy.ec.europa.eu/data-and-analysis/weekly-oil-bulletin_en",
    license=N("CC BY 4.0 (Decisión 2011/833/UE)", "CC BY 4.0 (décision 2011/833/UE)", "CC BY 4.0 (decisione 2011/833/UE)", "CC BY 4.0 (Beschluss 2011/833/EU)", "CC BY 4.0 (Decisão 2011/833/UE)"), license_url="https://commission.europa.eu/legal-notice_en",
    attribution="Fuente: Comisión Europea, Weekly Oil Bulletin")
SRC_CNMC = Source(
    name="CNMC Data (Comisión Nacional de los Mercados y la Competencia)",
    url="https://data.cnmc.es/energia/mercado-minorista-de-glp",
    license="CC BY-SA 4.0", license_url="https://data.cnmc.es/condiciones-de-uso",
    attribution="Fuente: CNMC Data, licencia CC BY-SA 4.0")
SRC_EUROSTAT = Source(
    name="Eurostat", url="https://ec.europa.eu/eurostat",
    license="CC BY 4.0", license_url="https://ec.europa.eu/eurostat/web/main/help/copyright-notice",
    attribution="Fuente: Eurostat")
SRC_REE = Source(
    name="Red Eléctrica (REData)", url="https://www.ree.es/es/datos/apidatos",
    license=N("Uso informativo citando fuente y fecha; sin redistribución del dato en bruto", "Usage informatif en citant la source et la date ; sans redistribution des données brutes", "Uso informativo citando fonte e data; senza ridistribuzione del dato grezzo", "Informative Nutzung mit Angabe von Quelle und Datum; keine Weitergabe der Rohdaten", "Uso informativo citando fonte e data; sem redistribuição dos dados em bruto"),
    license_url="https://www.ree.es/es/aviso-legal", attribution="Fuente: Red Eléctrica (REData)")
SRC_INE = Source(
    name="INE (Instituto Nacional de Estadística)", url="https://www.ine.es",
    license=N("Reutilización libre citando la fuente (aviso legal INE)", "Réutilisation libre en citant la source (mentions légales de l'INE)", "Riutilizzo libero citando la fonte (note legali dell'INE)", "Freie Weiterverwendung mit Quellenangabe (Impressum des INE)", "Reutilização livre citando a fonte (aviso legal do INE)"),
    license_url="https://www.ine.es/ss/Satellite?L=es_ES&c=Page&cid=1254735849170&p=1254735849170&pagename=Ayuda%2FINELayout",
    attribution="Elaboración propia con datos extraídos del sitio web del INE: www.ine.es")
SRC_WB = Source(
    name="World Bank Commodity Price Data (The Pink Sheet)",
    url="https://www.worldbank.org/en/research/commodity-markets",
    license="CC BY 4.0", license_url="https://datacatalog.worldbank.org/search/dataset/0038238",
    attribution="Fuente: World Bank Commodity Price Data (The Pink Sheet)")
SRC_AVEBIOM = Source(
    name="AVEBIOM, Índice de Precios de Biocombustibles Sólidos (IPB)",
    url="https://avebiom.org/actividades/indice-de-precios-biocombustibles-solidos/",
    license=N("Autorizado por AVEBIOM (correo del 14 sep 2026): citando la fuente con enlace y sin modificar los datos", "Autorisé par AVEBIOM (courriel du 14 sept. 2026) : en citant la source avec un lien et sans modifier les données", "Autorizzato da AVEBIOM (email del 14 set. 2026): citando la fonte con collegamento e senza modificare i dati", "Genehmigt von AVEBIOM (E-Mail vom 14.09.2026): mit Quellenangabe und Link, ohne die Daten zu verändern", "Autorizado pela AVEBIOM (e-mail de 14 set. 2026): citando a fonte com ligação e sem modificar os dados"),
    license_url="https://avebiom.org/actividades/indice-de-precios-biocombustibles-solidos/",
    attribution="Fuente: AVEBIOM, Índice de Precios de Biocombustibles Sólidos")
SRC_LENA = Source(
    name="Observatorio de precios de cristalesparachimeneas.es (elaboración propia a partir de precios públicos de tiendas online)",
    url="https://cristalesparachimeneas.es/",
    license=N("CC BY 4.0 (índice agregado de elaboración propia)", "CC BY 4.0 (indice agrégé de production propre)", "CC BY 4.0 (indice aggregato di elaborazione propria)", "CC BY 4.0 (eigener aggregierter Index)", "CC BY 4.0 (índice agregado de elaboração própria)"), license_url="https://creativecommons.org/licenses/by/4.0/",
    attribution="Fuente: Observatorio de precios de calefacción, cristalesparachimeneas.es")


# ----------------------------------------------------------------------------- gasóleo de calefacción (WOB)
for cc in COUNTRIES:
    c = cc.lower()
    register(Serie(
        id=f"gasoleo_{c}",
        name=N("Gasóleo de calefacción, con impuestos", "Fioul domestique, taxes comprises",
               "Gasolio da riscaldamento, tasse incluse", "Heizöl, inkl. Steuern", "Gasóleo de aquecimento, com impostos"),
        country=cc, group="hogar", fuel="gasoleo", unit="EUR/l", source=SRC_WOB, collector="wob",
        native_freq="W", expected_every_days=7, stale_after_days=28, min_value=0.2, max_value=4.0,
        max_change_pct=30, kwh_per_unit=10.0, decimals=4, taxes_included=True,
        notes="Precio medio nacional de entregas de 2.000-5.000 litros a domicilio (canal de reparto), en €/litro."))
    register(Serie(
        id=f"gasoleo_sin_imp_{c}",
        name=N("Gasóleo de calefacción, sin impuestos", "Fioul domestique, hors taxes",
               "Gasolio da riscaldamento, senza tasse", "Heizöl, ohne Steuern", "Gasóleo de aquecimento, sem impostos"),
        country=cc, group="hogar", fuel="gasoleo", unit="EUR/l", source=SRC_WOB, collector="wob",
        native_freq="W", expected_every_days=7, stale_after_days=28, min_value=0.1, max_value=4.0,
        max_change_pct=30, kwh_per_unit=10.0, decimals=4, taxes_included=False,
        notes="Mismo dato sin IVA ni impuestos especiales: muestra el efecto de la fiscalidad."))

# ----------------------------------------------------------------------------- butano y propano (CNMC)
register(Serie(
    id="butano_es",
    name=N("Bombona de butano (8-20 kg), precio regulado con impuestos", "Bouteille de butane (8-20 kg), prix réglementé TTC",
           "Bombola di butano (8-20 kg), prezzo regolato tasse incluse", "Butangasflasche (8-20 kg), regulierter Preis inkl. Steuern",
           "Botija de butano (8-20 kg), preço regulado com impostos"),
    country="ES", group="hogar", fuel="butano", unit="EUR/kg", source=SRC_CNMC, collector="cnmc_glp",
    native_freq="M", expected_every_days=31, stale_after_days=75, min_value=0.2, max_value=5.0,
    max_change_pct=25, kwh_per_unit=12.7, decimals=4, taxes_included=True,
    notes="Precio máximo de venta al público en €/kg; la bombona de 12,5 kg = valor × 12,5. Se revisa cada dos meses."))
register(Serie(
    id="propano_canalizado_es",
    name=N("Propano canalizado, término variable (antes de impuestos)", "Propane en réseau, terme variable (hors taxes)",
           "Propano canalizzato, quota variabile (prima delle imposte)", "Leitungsgebundenes Propan, Arbeitspreis (vor Steuern)",
           "Propano canalizado, termo variável (antes de impostos)"),
    country="ES", group="hogar", fuel="propano", unit="EUR/kg", source=SRC_CNMC, collector="cnmc_glp",
    native_freq="M", expected_every_days=31, stale_after_days=75, min_value=0.2, max_value=5.0,
    max_change_pct=25, kwh_per_unit=12.8, decimals=4, taxes_included=False,
    notes="Precio regulado del GLP por canalización a consumidor final, sin impuestos ni término fijo. Se revisa cada mes."))

# ----------------------------------------------------------------------------- electricidad y gas hogares (Eurostat)
for cc in COUNTRIES:
    c = cc.lower()
    register(Serie(
        id=f"electricidad_{c}",
        name=N("Electricidad para hogares, todo incluido (2.500-5.000 kWh/año)", "Électricité résidentielle, toutes taxes comprises (2 500-5 000 kWh/an)",
               "Elettricità per le famiglie, tutto incluso (2.500-5.000 kWh/anno)", "Haushaltsstrom, alle Steuern inkl. (2.500-5.000 kWh/Jahr)",
               "Eletricidade doméstica, tudo incluído (2.500-5.000 kWh/ano)"),
        country=cc, group="hogar", fuel="electricidad", unit="EUR/kWh", source=SRC_EUROSTAT, collector="eurostat_nrg",
        native_freq="S", expected_every_days=183, stale_after_days=520, min_value=0.03, max_value=1.0,
        max_change_pct=40, kwh_per_unit=1.0, decimals=4, taxes_included=True,
        notes="Precio medio pagado por un hogar tipo (banda DC), con energía, peajes, cargos e impuestos. Eurostat nrg_pc_204."))
    register(Serie(
        id=f"gas_{c}",
        name=N("Gas natural para hogares, todo incluido (20-200 GJ/año)", "Gaz naturel résidentiel, toutes taxes comprises (20-200 GJ/an)",
               "Gas naturale per le famiglie, tutto incluso (20-200 GJ/anno)", "Haushaltsgas, alle Steuern inkl. (20-200 GJ/Jahr)",
               "Gás natural doméstico, tudo incluído (20-200 GJ/ano)"),
        country=cc, group="hogar", fuel="gas", unit="EUR/kWh", source=SRC_EUROSTAT, collector="eurostat_nrg",
        native_freq="S", expected_every_days=183, stale_after_days=520, min_value=0.01, max_value=0.6,
        max_change_pct=60, kwh_per_unit=1.0, decimals=4, taxes_included=True,
        notes="Precio medio pagado por un hogar con calefacción de gas (banda D2), con todos los impuestos. Eurostat nrg_pc_202."))

# ----------------------------------------------------------------------------- IPC energía (Eurostat HICP)
HICP = {
    "electricidad": (N("Índice de precios: electricidad", "Indice des prix : électricité", "Indice dei prezzi: elettricità", "Preisindex: Strom", "Índice de preços: eletricidade"), "electricidad"),
    "gas": (N("Índice de precios: gas", "Indice des prix : gaz", "Indice dei prezzi: gas", "Preisindex: Gas", "Índice de preços: gás"), "gas"),
    "comb_liquidos": (N("Índice de precios: combustibles líquidos (gasóleo)", "Indice des prix : combustibles liquides (fioul)", "Indice dei prezzi: combustibili liquidi (gasolio)", "Preisindex: flüssige Brennstoffe (Heizöl)", "Índice de preços: combustíveis líquidos (gasóleo)"), "gasoleo"),
    "comb_solidos": (N("Índice de precios: combustibles sólidos (leña, pellet, carbón)", "Indice des prix : combustibles solides (bois, granulés, charbon)", "Indice dei prezzi: combustibili solidi (legna, pellet, carbone)", "Preisindex: feste Brennstoffe (Holz, Pellets, Kohle)", "Índice de preços: combustíveis sólidos (lenha, pellets, carvão)"), "lena"),
    "lena_pellet": (N("Índice de precios: leña y pellet", "Indice des prix : bois de chauffage et granulés", "Indice dei prezzi: legna e pellet", "Preisindex: Brennholz und Pellets", "Índice de preços: lenha e pellets"), "pellet"),
}
for cc in COUNTRIES:
    for key, (name, fuel) in HICP.items():
        if cc == "ES" and key in ("comb_solidos", "lena_pellet"):
            continue  # el INE no publica esa subclase en el IPCA armonizado
        register(Serie(
            id=f"hicp_{key}_{cc.lower()}", name=name, country=cc, group="hogar_indice", fuel=fuel,
            unit="índice 2015=100", source=SRC_EUROSTAT, collector="eurostat_hicp",
            native_freq="M", expected_every_days=31, stale_after_days=75, min_value=10, max_value=1000,
            max_change_pct=40, kwh_per_unit=None, decimals=2, taxes_included=True,
            notes="Índice armonizado de precios de consumo (HICP), 2015=100. Mide cuánto ha subido, no cuánto cuesta. Eurostat prc_hicp_minr."))

# ----------------------------------------------------------------------------- electricidad viva (REData)
register(Serie(
    id="pvpc_es",
    name=N("PVPC, término de energía (media diaria, sin impuestos ni potencia)", "PVPC, terme énergie (moyenne journalière, hors taxes et abonnement)",
           "PVPC, quota energia (media giornaliera, senza imposte né potenza)", "PVPC, Energiepreis (Tagesmittel, ohne Steuern und Leistungspreis)",
           "PVPC, termo de energia (média diária, sem impostos nem potência)"),
    country="ES", group="hogar", fuel="electricidad", unit="EUR/kWh", source=SRC_REE, collector="ree",
    native_freq="D", expected_every_days=1, stale_after_days=7, min_value=0.0, max_value=1.5,
    max_change_pct=1000, kwh_per_unit=1.0, decimals=5, taxes_included=False, redistributable=False,
    notes="Tarifa regulada 2.0TD, término de facturación de energía activa: incluye energía, peajes y cargos de energía; no incluye potencia, impuestos ni alquiler de contador."))
register(Serie(
    id="spot_es",
    name=N("Mercado mayorista diario (OMIE), media diaria", "Marché de gros journalier (OMIE), moyenne journalière",
           "Mercato all'ingrosso giornaliero (OMIE), media giornaliera", "Großhandels-Spotmarkt (OMIE), Tagesmittel",
           "Mercado grossista diário (OMIE), média diária"),
    country="ES", group="hogar", fuel="electricidad", unit="EUR/kWh", source=SRC_REE, collector="ree",
    native_freq="D", expected_every_days=1, stale_after_days=7, min_value=-0.1, max_value=1.5,
    max_change_pct=100000, kwh_per_unit=1.0, decimals=5, taxes_included=False, redistributable=False,
    notes="Precio marginal del mercado diario ibérico (España). Solo energía, sin peajes ni impuestos."))

# ----------------------------------------------------------------------------- IPC INE (contraste + hogar_indice ES)
INE_IPC = {
    "ipc_electricidad_es": ("IPC291483", N("IPC electricidad (INE)", "IPC électricité (INE)", "IPC elettricità (INE)", "VPI Strom (INE)", "IPC eletricidade (INE)"), "electricidad"),
    "ipc_gas_es": ("IPC291843", N("IPC gas natural (INE)", "IPC gaz naturel (INE)", "IPC gas naturale (INE)", "VPI Erdgas (INE)", "IPC gás natural (INE)"), "gas"),
    "ipc_comb_liquidos_es": ("IPC291487", N("IPC combustibles líquidos (INE)", "IPC combustibles liquides (INE)", "IPC combustibili liquidi (INE)", "VPI flüssige Brennstoffe (INE)", "IPC combustíveis líquidos (INE)"), "gasoleo"),
}
for sid, (code, name, fuel) in INE_IPC.items():
    register(Serie(
        id=sid, name=name, country="ES", group="hogar_indice", fuel=fuel, unit="índice 2021=100",
        source=SRC_INE, collector="ine_ipc", native_freq="M", expected_every_days=31, stale_after_days=75,
        min_value=10, max_value=1000, max_change_pct=40, decimals=3, taxes_included=True,
        notes=f"Índice de precios de consumo del INE, subclase ECOICOP, base 2021=100 (serie {code})."))

# ----------------------------------------------------------------------------- índices industriales (INE IPRI)
INE_IPRI = {
    "ipri_vidrio_plano_es": ("IPR37831", N("Precios industriales: fabricación de vidrio plano (CNAE 23.11)", "Prix à la production : verre plat (NACE 23.11)", "Prezzi alla produzione: vetro piano (NACE 23.11)", "Erzeugerpreise: Flachglas (NACE 23.11)", "Preços industriais: vidro plano (CAE 23.11)")),
    "ipri_vidrio_tecnico_es": ("IPR37827", N("Precios industriales: otro vidrio, incl. vidrio técnico (CNAE 23.19)", "Prix à la production : autres verres, dont verre technique (NACE 23.19)", "Prezzi alla produzione: altro vetro, incl. vetro tecnico (NACE 23.19)", "Erzeugerpreise: sonstiges Glas inkl. technisches Glas (NACE 23.19)", "Preços industriais: outro vidro, incl. vidro técnico (CAE 23.19)")),
    "ipri_vidrio_es": ("IPR37386", N("Precios industriales: vidrio y productos de vidrio (CNAE 23.1)", "Prix à la production : verre et articles en verre (NACE 23.1)", "Prezzi alla produzione: vetro e prodotti in vetro (NACE 23.1)", "Erzeugerpreise: Glas und Glaswaren (NACE 23.1)", "Preços industriais: vidro e produtos de vidro (CAE 23.1)")),
    "ipri_siderurgia_es": ("IPR37378", N("Precios industriales: siderurgia, hierro y acero (CNAE 24.1)", "Prix à la production : sidérurgie (NACE 24.1)", "Prezzi alla produzione: siderurgia (NACE 24.1)", "Erzeugerpreise: Eisen und Stahl (NACE 24.1)", "Preços industriais: siderurgia (CAE 24.1)")),
    "ipri_aparatos_domesticos_es": ("IPR37767", N("Precios industriales: aparatos domésticos no eléctricos, estufas y cocinas (CNAE 27.52)", "Prix à la production : appareils ménagers non électriques, poêles (NACE 27.52)", "Prezzi alla produzione: apparecchi domestici non elettrici, stufe (NACE 27.52)", "Erzeugerpreise: nichtelektrische Haushaltsgeräte, Öfen (NACE 27.52)", "Preços industriais: aparelhos domésticos não elétricos, salamandras (CAE 27.52)")),
    "ipri_radiadores_calderas_es": ("IPR37796", N("Precios industriales: radiadores y calderas de calefacción (CNAE 25.21)", "Prix à la production : radiateurs et chaudières (NACE 25.21)", "Prezzi alla produzione: radiatori e caldaie (NACE 25.21)", "Erzeugerpreise: Heizkörper und Heizkessel (NACE 25.21)", "Preços industriais: radiadores e caldeiras (CAE 25.21)")),
    "ipri_aislantes_refractarios_es": ("IPR37811", N("Precios industriales: otros minerales no metálicos, aislantes y refractarios (CNAE 23.99)", "Prix à la production : autres minéraux non métalliques, isolants (NACE 23.99)", "Prezzi alla produzione: altri minerali non metallici, isolanti (NACE 23.99)", "Erzeugerpreise: sonstige Mineralerzeugnisse, Dämmstoffe (NACE 23.99)", "Preços industriais: outros minerais não metálicos, isolantes (CAE 23.99)")),
}
for sid, (code, name) in INE_IPRI.items():
    register(Serie(
        id=sid, name=name, country="ES", group="industria", fuel="indice", unit="índice 2021=100",
        source=SRC_INE, collector="ine_ipri", native_freq="M", expected_every_days=31, stale_after_days=75,
        min_value=5, max_value=1000, max_change_pct=25, decimals=3,
        notes=f"Índice de precios industriales del INE, mercado interior, base 2021=100 (serie {code})."))

# Eurostat STS (mismo concepto en otros países; y ES de Eurostat solo para contraste)
STS = [
    ("ipri_vidrio_es_eurostat", "ES", "C231", "vidrio", True),
    ("ipri_vidrio_fr", "FR", "C231", "vidrio", False),
    ("ipri_vidrio_it", "IT", "C231", "vidrio", False),
    ("ipri_vidrio_de", "DE", "C231", "vidrio", False),
    ("ipri_aparatos_domesticos_de", "DE", "C2752", "aparatos", False),
    ("ipri_aparatos_domesticos_it", "IT", "C2752", "aparatos", False),
    ("ipri_aparatos_domesticos_fr", "FR", "C275", "aparatos275", False),
    ("ipri_siderurgia_de", "DE", "C241", "siderurgia", False),
    ("ipri_siderurgia_it", "IT", "C241", "siderurgia", False),
    ("ipri_siderurgia_fr", "FR", "C241", "siderurgia", False),
]
STS_NAMES = {
    "vidrio": N("Precios industriales: vidrio y productos de vidrio (NACE C23.1)", "Prix à la production : verre et articles en verre (NACE C23.1)", "Prezzi alla produzione: vetro e prodotti in vetro (NACE C23.1)", "Erzeugerpreise: Glas und Glaswaren (NACE C23.1)", "Preços industriais: vidro e produtos de vidro (NACE C23.1)"),
    "aparatos": N("Precios industriales: aparatos domésticos no eléctricos, estufas (NACE C27.52)", "Prix à la production : appareils ménagers non électriques, poêles (NACE C27.52)", "Prezzi alla produzione: apparecchi domestici non elettrici, stufe (NACE C27.52)", "Erzeugerpreise: nichtelektrische Haushaltsgeräte, Öfen (NACE C27.52)", "Preços industriais: aparelhos domésticos não elétricos, salamandras (NACE C27.52)"),
    "aparatos275": N("Precios industriales: aparatos domésticos (NACE C27.5)", "Prix à la production : appareils ménagers (NACE C27.5)", "Prezzi alla produzione: apparecchi domestici (NACE C27.5)", "Erzeugerpreise: Haushaltsgeräte (NACE C27.5)", "Preços industriais: aparelhos domésticos (NACE C27.5)"),
    "siderurgia": N("Precios industriales: siderurgia, hierro y acero (NACE C24.1)", "Prix à la production : sidérurgie (NACE C24.1)", "Prezzi alla produzione: siderurgia (NACE C24.1)", "Erzeugerpreise: Eisen und Stahl (NACE C24.1)", "Preços industriais: siderurgia (NACE C24.1)"),
}
for sid, cc, nace, nk, hidden in STS:
    register(Serie(
        id=sid, name=STS_NAMES[nk], country=cc, group="industria", fuel="indice",
        unit="índice 2021=100", source=SRC_EUROSTAT, collector="eurostat_sts", native_freq="M",
        expected_every_days=31, stale_after_days=90, min_value=5, max_value=1000, max_change_pct=25,
        decimals=1, hidden=hidden,
        notes=f"Índice de precios de producción industrial, mercado interior, 2021=100 (Eurostat sts_inppd_m, NACE {nace})."))

# ----------------------------------------------------------------------------- materias primas (Banco Mundial)
WB = {
    "gas_ttf_eu": ("Natural gas, Europe", "USD/mmbtu", N("Gas natural en Europa (TTF), precio mayorista", "Gaz naturel en Europe (TTF), prix de gros", "Gas naturale in Europa (TTF), prezzo all'ingrosso", "Erdgas Europa (TTF), Großhandelspreis", "Gás natural na Europa (TTF), preço grossista")),
    "mineral_hierro": ("Iron ore, cfr spot", "USD/dmtu", N("Mineral de hierro (62 % Fe), precio spot", "Minerai de fer (62 % Fe), prix spot", "Minerale di ferro (62 % Fe), prezzo spot", "Eisenerz (62 % Fe), Spotpreis", "Minério de ferro (62 % Fe), preço spot")),
    "brent": ("Crude oil, Brent", "USD/bbl", N("Petróleo Brent", "Pétrole Brent", "Petrolio Brent", "Rohöl Brent", "Petróleo Brent")),
    "cobre": ("Copper", "USD/t", N("Cobre (LME)", "Cuivre (LME)", "Rame (LME)", "Kupfer (LME)", "Cobre (LME)")),
}
WB_RANGES = {"gas_ttf_eu": (0.1, 200), "mineral_hierro": (1, 1000), "brent": (0.5, 500), "cobre": (200, 50000)}
for sid, (col, unit, name) in WB.items():
    lo, hi = WB_RANGES[sid]
    register(Serie(
        id=sid, name=name, country="EU", group="industria", fuel="indice", unit=unit, source=SRC_WB,
        collector="worldbank", native_freq="M", expected_every_days=31, stale_after_days=70,
        min_value=lo, max_value=hi, max_change_pct=60, decimals=2,
        notes=f"Media mensual en dólares nominales (columna '{col}' del Pink Sheet). Mostrar la variación interanual evita el efecto del tipo de cambio."))

# ----------------------------------------------------------------------------- biomasa (AVEBIOM) — autorizado el 14 sep 2026
# De la biomasa, a la comparativa solo va el formato que usa de verdad una casa con estufa: el saco de pellet y
# el hueso de aceituna. El pellet a granel y en palet son el mismo combustible en otro envase, y la astilla pide
# una caldera con silo: si entran, encabezan el ranking y la frase "lo más barato para calentar una casa" deja de
# ser cierta para quien tiene una estufa.
SIN_COMPARATIVA = {"pellet_palet_es", "pellet_granel_es", "astilla_es"}

AVB = {
    "pellet_saco_es": ("PELLET", "SACO de 15 kg", 1 / 15, N("Pellet en saco de 15 kg, con IVA", "Granulés en sac de 15 kg, TTC", "Pellet in sacco da 15 kg, IVA inclusa", "Pellets im 15-kg-Sack, inkl. MwSt.", "Pellets em saco de 15 kg, com IVA"), 4.76),
    "pellet_palet_es": ("PELLET", "PALET de sacos", 1 / 1000, N("Pellet en palet de sacos, con IVA", "Granulés en palette de sacs, TTC", "Pellet in pallet di sacchi, IVA inclusa", "Pellets auf Palette, inkl. MwSt.", "Pellets em palete de sacos, com IVA"), 4.76),
    "pellet_granel_es": ("PELLET", "GRANEL en CISTERNA", 1 / 1000, N("Pellet a granel en cisterna, con IVA", "Granulés en vrac (camion souffleur), TTC", "Pellet sfuso in cisterna, IVA inclusa", "Pellets lose per Tankwagen, inkl. MwSt.", "Pellets a granel em cisterna, com IVA"), 4.76),
    "hueso_granel_es": ("HUESO", "GRANEL en CISTERNA", 1 / 1000, N("Hueso de aceituna a granel en cisterna, con IVA", "Noyaux d’olive en vrac, TTC", "Nocciolino di oliva sfuso, IVA inclusa", "Olivenkerne lose, inkl. MwSt.", "Caroço de azeitona a granel, com IVA"), 4.76),
    "astilla_es": ("ASTILLA", "Astilla a granel", 1 / 1000, N("Astilla de madera a granel (G30), con IVA", "Plaquettes forestières en vrac (G30), TTC", "Cippato sfuso (G30), IVA inclusa", "Hackschnitzel lose (G30), inkl. MwSt.", "Estilha a granel (G30), com IVA"), 4.42),
}
ANUAL = {"es": "media anual", "fr": "moyenne annuelle", "it": "media annua", "de": "Jahresmittel", "pt": "média anual"}
for sid, (pdf, block, factor, name, kwh) in AVB.items():
    fuel = {"PELLET": "pellet", "HUESO": "hueso", "ASTILLA": "astilla"}[pdf]
    register(Serie(
        id=sid, name=name, country="ES", group="hogar", fuel=fuel, unit="EUR/kg", source=SRC_AVEBIOM,
        collector="avebiom", native_freq="Q", expected_every_days=92, stale_after_days=230,
        min_value=0.03, max_value=2.0, max_change_pct=60, kwh_per_unit=kwh, decimals=4, taxes_included=True,
        publishable=True, redistributable=False, en_comparativa=sid not in SIN_COMPARATIVA,
        notes="Precio medio a consumidor final en España, con 21 % de IVA; trimestral. PCI usado por AVEBIOM: 4,76 kWh/kg (pellet)."))
    register(Serie(
        id=sid + "_anual", name={k: v + " · " + ANUAL[k] for k, v in name.items()},
        country="ES", group="hogar", fuel=fuel, unit="EUR/kg", source=SRC_AVEBIOM,
        collector="avebiom", native_freq="A", expected_every_days=366, stale_after_days=760,
        min_value=0.03, max_value=2.0, max_change_pct=80, kwh_per_unit=kwh, decimals=4, taxes_included=True,
        publishable=True, redistributable=False, en_comparativa=False,
        notes="Media anual publicada por AVEBIOM."))

# ----------------------------------------------------------------------------- leña (índice propio)
register(Serie(
    id="lena_palet_es",
    name=N("Leña dura seca en palet o saca (≥300 kg), entregada en península, con IVA",
           "Bois dur sec en palette (≥300 kg), livré en péninsule, TTC",
           "Legna dura secca in pallet (≥300 kg), consegnata in penisola, IVA inclusa",
           "Trockenes Hartholz auf Palette (≥300 kg), geliefert, inkl. MwSt.",
           "Lenha dura seca em palete (≥300 kg), entregue na península, com IVA"),
    country="ES", group="hogar", fuel="lena", unit="EUR/kg", source=SRC_LENA, collector="lena",
    native_freq="W", expected_every_days=7, stale_after_days=21, min_value=0.10, max_value=1.20,
    max_change_pct=20, kwh_per_unit=4.1, decimals=4, taxes_included=True, min_points=8,
    notes="Mediana entre tiendas online españolas (una referencia representativa por tienda: encina, roble, olivo, haya). Transporte a domicilio incluido. Índice de elaboración propia; ver metodología."))
register(Serie(
    id="lena_saco_es",
    name=N("Leña en saco pequeño (8-25 kg), precio en tienda sin portes, con IVA",
           "Bois en petit sac (8-25 kg), prix magasin hors livraison, TTC",
           "Legna in sacco piccolo (8-25 kg), prezzo senza trasporto, IVA inclusa",
           "Brennholz im Kleinsack (8-25 kg), ohne Lieferung, inkl. MwSt.",
           "Lenha em saco pequeno (8-25 kg), preço sem portes, com IVA"),
    country="ES", group="hogar", fuel="lena", unit="EUR/kg", source=SRC_LENA, collector="lena",
    native_freq="W", expected_every_days=7, stale_after_days=21, min_value=0.15, max_value=2.5,
    max_change_pct=25, kwh_per_unit=4.1, decimals=4, taxes_included=True, min_points=8,
    notes="Mediana entre tiendas del precio por kg del saco pequeño. Formato de conveniencia, mucho más caro por kg que el palet."))


# ----------------------------------------------------------------------------- pellet en otros paises
SRC_PROPELLETS = Source(
    name="proPellets Austria, Pelletpreisindex PPI06", url="https://www.propellets.at/aktuelle-pelletpreise",
    license=N("Uso con cita de la fuente (permiso revocable, Impressum de proPellets)", "Usage avec citation de la source (autorisation révocable, mentions légales de proPellets)", "Uso con citazione della fonte (permesso revocabile, note legali di proPellets)", "Nutzung mit Quellenangabe (widerrufliche Erlaubnis, Impressum von proPellets)", "Uso com citação da fonte (permissão revogável, Impressum da proPellets)"),
    license_url="https://www.propellets.at/impressum", attribution="Quelle: proPellets Austria")
SRC_CARMEN = Source(
    name="C.A.R.M.E.N. e.V., Marktpreise Pellets",
    url="https://www.carmen-ev.de/service/marktueberblick/marktpreise-energieholz/marktpreise-pellets/",
    license=N("Uso comercial previa consulta con C.A.R.M.E.N. (pendiente)", "Usage commercial sur demande préalable auprès de C.A.R.M.E.N. (en attente)", "Uso commerciale previa richiesta a C.A.R.M.E.N. (in attesa)", "Kommerzielle Nutzung nach vorheriger Rücksprache mit C.A.R.M.E.N. (ausstehend)", "Uso comercial mediante consulta prévia à C.A.R.M.E.N. (pendente)"),
    license_url="https://www.carmen-ev.de/service/marktueberblick/marktpreise-energieholz/",
    attribution="Quelle: C.A.R.M.E.N. e.V.")
register(Serie(
    id="pellet_indice_at",
    name=N("Índice de precio del pellet a granel (6 t), enero 2006 = 100",
           "Indice du prix des granulés en vrac (6 t), janvier 2006 = 100",
           "Indice del prezzo del pellet sfuso (6 t), gennaio 2006 = 100",
           "Pelletpreisindex lose Ware (6 t), Jänner 2006 = 100",
           "Índice de preço dos pellets a granel (6 t), janeiro 2006 = 100"),
    country="AT", group="hogar_indice", fuel="pellet", unit="índice ene-2006=100", source=SRC_PROPELLETS,
    collector="pellets_eu", native_freq="M", expected_every_days=31, stale_after_days=75, min_value=20,
    max_value=2000, max_change_pct=40, decimals=2, taxes_included=True, redistributable=False,
    notes="Índice mensual de proPellets Austria (encuesta a más de 50 distribuidores; pellet ENplus A1 a granel, pedido de 6 t)."))
register(Serie(
    id="pellet_granel_de",
    name=N("Pellet a granel (5 t), con IVA", "Granulés en vrac (5 t), TTC", "Pellet sfuso (5 t), IVA inclusa",
           "Pellets lose (5 t), inkl. MwSt.", "Pellets a granel (5 t), com IVA"),
    country="DE", group="hogar", fuel="pellet", unit="EUR/kg", source=SRC_CARMEN, collector="pellets_eu",
    native_freq="M", expected_every_days=31, stale_after_days=75, min_value=0.05, max_value=2.0, max_change_pct=40,
    kwh_per_unit=4.8, decimals=4, taxes_included=True, publishable=False, redistributable=False,
    notes="Media alemana del precio de 5 t de pellet a granel, IVA incluido (C.A.R.M.E.N. e.V., encuesta mensual a unos 50 proveedores). Pendiente de confirmar el uso comercial."))

# ----------------------------------------------------------------------------- contraste: fioul de Francia
SRC_FR_ECOLOGIE = Source(
    name="Ministere de la Transition ecologique (Francia), Prix des produits petroliers",
    url="https://www.ecologie.gouv.fr/prix-des-produits-petroliers", license="Licence Ouverte / etalab-2.0",
    license_url="https://www.etalab.gouv.fr/licence-ouverte-open-licence/",
    attribution="Source : Ministere de la Transition ecologique")
register(Serie(
    id="fioul_fr_ministere",
    name=N("Fioul domestique (2.000-4.999 l), con impuestos — fuente nacional",
           "Fioul domestique (2 000-4 999 l), TTC — source nationale",
           "Gasolio da riscaldamento (2.000-4.999 l), tasse incluse — fonte nazionale",
           "Heizöl (2.000-4.999 l), inkl. Steuern — nationale Quelle",
           "Gasóleo de aquecimento (2.000-4.999 l), com impostos — fonte nacional"),
    country="FR", group="hogar", fuel="gasoleo", unit="EUR/l", source=SRC_FR_ECOLOGIE, collector="fr_fioul",
    native_freq="W", expected_every_days=7, stale_after_days=28, min_value=0.2, max_value=4.0, max_change_pct=30,
    kwh_per_unit=10.0, decimals=4, taxes_included=True, hidden=True,
    notes="Solo para contrastar el Weekly Oil Bulletin (es el mismo dato que Francia comunica a la Comision)."))
