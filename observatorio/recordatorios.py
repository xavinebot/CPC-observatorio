"""Recordatorios con fecha, que se cuelan en el resumen de los lunes.

Un apunte en un documento no avisa a nadie; el resumen semanal ya llega al móvil por Telegram, así que es el sitio
natural para las cosas que hay que hacer en una fecha y que si no se olvidan.

Cada recordatorio tiene una ventana: aparece en todos los resúmenes entre `desde` y `hasta`, y después desaparece
solo. No hay que acordarse de borrarlo. Para añadir uno, una línea más en la lista.
"""
from __future__ import annotations

import datetime as _dt

# (desde, hasta, texto). Las fechas son inclusivas, en formato AAAA-MM-DD.
RECORDATORIOS: list[tuple[str, str, str]] = [
    (
        "2026-10-12", "2026-11-15",
        "📣 <b>Toca la ronda de prensa.</b> Es la ventana buena: la segunda quincena de octubre y la primera de "
        "noviembre, cuando se escriben los artículos de cuánto cuesta la calefacción. Antes de enviar nada, "
        "actualiza los números con <code>python -m observatorio prensa</code>: si la historia ha cambiado, cambia "
        "la nota. El correo y el orden de destinatarios están en NOTA-PRENSA.md.",
    ),
    (
        "2026-10-22", "2026-11-30",
        "🔗 <b>Toca el siguiente enlace interno al observatorio.</b> De uno en uno y con días de por medio, para "
        "poder atribuir el efecto: la guía de limpieza del cristal, las guías de leña y /b2b/ hacia los índices "
        "industriales. Desde la ficha del cristal a medida, nada. El detalle está en OBSERVATORIO.md §6.",
    ),
    (
        "2026-10-19", "2026-11-09",
        "🌳 <b>Mira el índice de la leña.</b> Debería haberse publicado solo al llegar a las ocho semanas de "
        "lecturas. Si sigue en «series en construcción», algo falla en la recogida de las tiendas.",
    ),
    (
        "2026-10-13", "2026-11-23",
        "🔎 <b>Comprueba Google Dataset Search.</b> Entra en <code>datasetsearch.research.google.com</code> y busca "
        "«precio gasóleo calefacción España». Deberían salir las series del observatorio: el marcado está puesto y "
        "completo desde el 15 de septiembre, y Google tarda unas semanas. Si a finales de noviembre no aparecen, "
        "hay que mirar el marcado con la prueba de resultados enriquecidos de Google.",
    ),
    (
        "2026-09-29", "2026-12-15",
        "🏛️ <b>Mira si ya está publicada la ficha de datos.gob.es.</b> Busca «Cristales para Chimeneas» en "
        "<code>datos.gob.es/es/empresas</code> y en el catálogo de aplicaciones. El 18 de septiembre pidieron la "
        "licencia y cinco imágenes y se contestó el mismo día, así que la pelota está en su tejado. Cuando "
        "aparezca, apúntala en la pestaña <code>GSC_enlaces</code> de la hoja «Datos CPC» como dominio que enlaza, "
        "tipo administración. Si a mediados de diciembre no está, escribe al contacto del portal.",
    ),
    (
        "2026-09-28", "2026-10-26",
        "🔍 <b>¿Están indexadas las ocho páginas nuevas?</b> La indexación se pidió el 15 y el 17 de septiembre. "
        "En Search Console, Inspección de URLs, mira si ya salen como indexadas: son las de profesionales y "
        "metodología en francés, italiano, alemán y portugués (lista en SEO.md §31). Si alguna sigue fuera a "
        "finales de octubre, mírale la cobertura; estar en el mapa del sitio ya basta para que Google llegue, "
        "así que una que no entre suele señalar otra cosa.",
    ),
    (
        "2026-10-05", "2026-11-09",
        "🇩🇪 <b>¿Contestó C.A.R.M.E.N. lo del gráfico?</b> El 18 de septiembre se les respondió aceptando su "
        "condición (tabla de dos filas, sin medias anuales, sin CSV) y preguntando si el gráfico puede enseñar "
        "el histórico desde 2005. Si no han dicho nada, una llamada al <code>+49 9421 960-300</code>, que es una "
        "asociación pequeña y el correo se les queda sin leer. Con su respuesta se publica el precio del pellet "
        "alemán: 260 meses desde 2005, que es lo que le falta a la página alemana. Detalle en CORREO-CARMEN.md.",
    ),
]


def pendientes(hoy: _dt.date | None = None) -> list[str]:
    """Los recordatorios cuya ventana incluye hoy."""
    hoy = hoy or _dt.date.today()
    fuera = []
    for desde, hasta, texto in RECORDATORIOS:
        if _dt.date.fromisoformat(desde) <= hoy <= _dt.date.fromisoformat(hasta):
            fuera.append(texto)
    return fuera
