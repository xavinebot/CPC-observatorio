# INFORME.md — Observatorio de precios de la calefacción

12 de septiembre de 2026. Todo está en **staging**; producción no se ha tocado en ningún momento.

---

## 1. Qué hay montado y dónde verlo

Una sección que publica **93 series de precios** con **39.717 datos**, la más larga desde 2005 (el gasóleo, semana
a semana) y una desde 1994 (la bombona de butano). Siete páginas, cinco idiomas.

| Página | URL en staging |
|---|---|
| España | https://staging.cristalesparachimeneas.es/observatorio-precios-calefaccion/ |
| Francia | https://staging.cristalesparachimeneas.es/fr/observatoire-prix-chauffage/ |
| Italia | https://staging.cristalesparachimeneas.es/it/osservatorio-prezzi-riscaldamento/ |
| Alemania | https://staging.cristalesparachimeneas.es/de/heizkosten-observatorium/ |
| Portugal | https://staging.cristalesparachimeneas.es/pt-pt/observatorio-precos-aquecimento/ |
| Metodología | https://staging.cristalesparachimeneas.es/observatorio-precios-calefaccion/metodologia/ |
| Profesionales | https://staging.cristalesparachimeneas.es/observatorio-precios-calefaccion/precios-industriales/ |

Lo que ve un visitante en la página de España, por orden: la **comparativa de combustibles en euros por kWh de
calor útil** ordenada de más barato a más caro, y debajo cada combustible con su cifra, su variación en doce meses,
su gráfico histórico, su tabla de datos, su fuente con licencia y su descarga en CSV. Al final, la tabla de
conversión y el enlace a la tienda.

La comparativa de hoy para España, tal como sale publicada:

| Combustible | €/kWh de calor útil |
|---|---|
| Electricidad con bomba de calor | 0,089 |
| Gas natural | 0,104 |
| Butano | 0,126 |
| Gasóleo de calefacción | 0,155 |
| Leña dura en palet | 0,174 |
| Leña en saco pequeño | 0,217 |
| Electricidad con radiador | 0,267 |

Ese orden es, por sí solo, un argumento de venta: la leña sigue siendo tres veces más barata que un radiador
eléctrico, y quien tiene chimenea querrá usarla.

### Las piezas

- **Repositorio de datos** `F:\Xavi\Projectes NO G-Drive\CPC-observatorio` (aún no está en GitHub, eso lo haces tú).
  Recolectores en Python, un fichero por serie, validación, cuarentena, avisos y publicación.
- **Plugin** `cpc-observatorio` dentro del monorepo `CPC-plugins`, ya instalado y activo en staging.
- **Tests**: 13 pruebas nuevas con Playwright, dentro de los smoke tests que ya tenías. Las 23 pruebas del conjunto
  (11 antiguas + 13 nuevas, una compartida) **pasan en verde**, incluidas las del precio a medida, el recargo por
  país y el checkout: nada de lo que ya funcionaba se ha roto.

## 2. Qué revisar en staging

**Diseño.** Ábrelo en el móvil y en el ordenador. Fíjate en tres cosas: que la comparativa se lea de un vistazo,
que las tablas anchas se desplacen solas dentro de su recuadro sin mover la página, y que la tipografía y el naranja
sean los mismos de la tienda. Pasa el ratón por encima de un gráfico: debe salir una etiqueta con la fecha y el
valor. Prueba los botones "2 años / 5 años / Todo" debajo de cada gráfico.

**Datos.** Compara tres cifras con su fuente, que va enlazada al pie de cada serie:
- el gasóleo de calefacción de España (1,3962 €/l el 7 de septiembre) con el Boletín Petrolero de la Comisión;
- la bombona de butano (1,4362 €/kg, es decir 17,95 € la de 12,5 kg) con la CNMC;
- el índice de la leña (0,4622 €/kg) mirando dos o tres tiendas a mano. Ojo: verás la nota de que la horquilla va
  de 0,24 a 0,66 €/kg. Es real y es la parte más delicada del proyecto; lee el punto 6.

**SEO.** Comprueba que cada idioma tiene su título propio en la pestaña del navegador, que el menú de países lleva a
la página del idioma correcto (esto falló dos veces durante el desarrollo, ver punto 5) y que hay un solo H1 por
página. El marcado de datos está puesto: 16 bloques de tipo Dataset en la página de España, cada uno con su
licencia, su periodo cubierto y su enlace de descarga.

**Lo que no se puede comprobar en staging:** la etiqueta canónica y la indexación. Staging está marcado como "no
indexar" a propósito, así que Rank Math omite la canónica en todas sus páginas. En producción sí aparece (lo he
verificado en la home de producción, sin tocar nada). El hreflang sí se puede ver en staging y está correcto en los
cinco idiomas.

## 3. Fuentes incluidas

Doce fuentes, todas verificadas descargando datos reales, todas con licencia que permite publicar:

- **Comisión Europea, Boletín Petrolero semanal**: gasóleo de calefacción de los seis países, con y sin impuestos,
  cada semana desde enero de 2005. Es la serie estrella.
- **CNMC**: bombona de butano desde 1994 y propano canalizado desde 2006 (precios regulados).
- **Eurostat**: electricidad y gas de los hogares con todos los impuestos, semestral desde 2007, seis países. Más el
  índice armonizado de precios de la energía, mensual desde 1996, que incluye un subíndice de leña y pellet.
- **Red Eléctrica**: tarifa regulada PVPC y mercado mayorista, media diaria (PVPC desde 2021, mayorista desde 2014).
- **INE**: IPC de la energía e índices de precios industriales del vidrio plano, el vidrio técnico, la siderurgia, las
  estufas y cocinas, los radiadores y calderas, y los aislantes y refractarios.
- **Eurostat de nuevo**, para esos mismos índices industriales en Francia, Italia y Alemania.
- **Banco Mundial**: gas europeo, mineral de hierro, Brent y cobre, mensual desde 1960.
- **proPellets Austria**: índice del pellet austriaco desde 2006.
- **Índice propio de la leña en España**: dos series, semanal.
- **Ministerio francés**: gasóleo de calefacción, solo para contrastar internamente con el dato europeo.

## 4. Fuentes descartadas y por qué

- **Gasóleo C del Geoportal de gasolineras.** En 2026 solo once gasolineras de toda España publican precio de
  gasóleo C, y en 2007 eran 122. No representa nada, porque ese combustible se compra por cisterna. El canal de
  reparto es justo lo que recoge el Boletín Petrolero europeo, así que no perdemos el dato: lo ganamos mejor.
- **Bombona de propano de 11 kg.** Dejó de estar regulada en 2015 y no hay fuente oficial.
- **El token de ESIOS que ibas a pedir.** No hace falta: la API abierta de Red Eléctrica da lo mismo sin token. Si
  algún día quieres el precio de la luz de Canarias o Baleares, entonces sí habría que pedirlo.
- **Precio del acero europeo.** Solo lo venden agencias de pago con licencias que prohíben republicar. En su lugar van
  los índices oficiales de siderurgia y de tubos de acero, que cuentan la misma historia.
- **Litio.** No hay fuente mensual gratuita (el servicio geológico de Estados Unidos publica un precio al año en PDF)
  y su peso en el sector es casi nulo. Descartado, como pedías, documentándolo.
- **Derechos de emisión de CO2.** Miré cinco fuentes: la única gratuita con precio real en euros son los informes de
  subasta de EEX, y sus condiciones exigen licencia para publicarlos en una web. Descartado.
- **Pellet de Francia, Italia y Portugal.** Publican cifras en artículos o en imágenes de gráficos, sin serie
  numérica ni permiso.
- **Índice de leña fuera de España.** En Francia y Alemania ya existen barómetros propios y en Italia y Portugal el
  mercado online es local. Duplicarlo no aportaría nada.
- **Amazon, Leroy Merlin, Obramat y Carrefour para el índice de leña.** Prohíben la extracción automatizada en sus
  condiciones y además bloquean técnicamente. No se tocan.

## 5. Decisiones importantes (y lo que cambié de la propuesta)

El detalle está en `DECISIONES.md`. Lo que más te afecta:

1. **El pellet español está recogido pero no publicado.** AVEBIOM tiene el dato bueno (desde 2012) y su PDF se lee
   sin problema, pero su aviso legal exige **autorización escrita previa** para reproducir sus contenidos. El
   histórico ya está cargado y la serie aparece en la web como "pendiente". Te dejo el correo redactado en el punto
   8: con un sí por escrito, se activa cambiando una palabra. Lo mismo con el pellet alemán de C.A.R.M.E.N.
2. **La comparativa no es €/kWh sino €/kWh de calor útil.** Comparar por el contenido energético habría sido
   engañoso: una chimenea abierta aprovecha el 15 % de la leña y una estufa moderna el 75 %. La tabla de
   rendimientos está publicada y se cambia en un solo sitio.
3. **Dos series de electricidad, no una.** La semestral de Eurostat es lo que paga de verdad un hogar y es la que
   entra en la comparativa; la diaria de Red Eléctrica va etiquetada como "solo término de energía". Publicar el
   precio mayorista como "el precio de la luz" habría restado la mitad de la factura.
4. **Siete páginas, no cuarenta.** Con miles de páginas sin indexar, añadir una página por combustible habría
   empeorado el problema. Una por idioma, más metodología y profesionales.
5. **Gráficos dibujados en el servidor, sin librería de gráficos.** Google ve el gráfico y la tabla sin ejecutar
   nada, la página no espera ningún script externo y no hay una dependencia que actualizar cada año. El CSS y el JS
   solo se cargan en las páginas del observatorio: lo he comprobado en la home, la ficha, el carrito y el checkout.
6. **Un solo aviso de Telegram por ejecución.** La primera versión mandaba uno por serie y en la carga inicial te
   llegaron decenas; ya lo has visto. Corregido.
7. **La regla del "salto máximo" no se aplica al cargar el histórico.** Marcaba como sospechosos los saltos reales
   de la crisis energética de 2022. En el día a día sí se aplica, que es cuando protege de un error de lectura.

**Dos fallos que encontré y arreglé durante las pruebas**, por si reaparecen:
- El menú de países llevaba a la misma página en todos los idiomas. Causa: WPML y el arreglo de enlaces del tema
  reescriben cualquier enlace interno al idioma de la página. Solución: el menú lo pinta el plugin al final de la
  cadena de filtros, cuando esos arreglos ya han pasado.
- La etiqueta al pasar el ratón por el gráfico no aparecía. Causa: la opción "retrasar JavaScript" de WP Rocket
  sustituye la forma estándar de escuchar eventos y se queda los del ratón. Solución: asignar el manejador como
  propiedad directa. Está comentado en el código para que no se "arregle" al revés en el futuro.

## 6. El índice de la leña: lo que tienes que saber

Es lo más diferenciador (nadie publica el precio de la leña en España, y el índice europeo no cubre los combustibles
sólidos españoles) y también lo más frágil.

Hoy lee cinco tiendas y sale **0,4622 €/kg** para el palet entregado, con una horquilla real **de 0,24 a 0,66**
€/kg entre ofertas. Esa dispersión no es un error: una tienda mayorista cerca de Barcelona vende el palet de 1.000
kg de encina a 0,26 €/kg y otra vende medio palet con caja de cartón a 0,73. Cambian la especie, la longitud del
leño, el tamaño del palet y el margen. Por eso la página **publica la horquilla y el número de tiendas junto a la
cifra**, en vez de esconderlo detrás de una mediana. Si algún día quieres afinarlo, la palanca es incorporar más
tiendas grandes, y eso solo se consigue pidiéndoles el dato directamente.

Mi recomendación antes de publicar en producción: mira dos semanas seguidas cómo se mueve el índice. Si oscila más
de un 10 % sin que el mercado se mueva, conviene fijar más el formato (por ejemplo, solo palets de 1.000 kg o más).

## 7. Rendimiento

Medido en staging con navegador real, tres páginas, escritorio y móvil:

| Medida | Escritorio | Móvil |
|---|---|---|
| Tiempo hasta el primer pintado | 0,26 a 1,5 s | 0,26 a 1,5 s |
| Peso del HTML de la página | 148 a 182 KB | 148 a 182 KB |
| Desplazamiento inesperado del contenido | 0 | 0 |
| Errores de JavaScript | 0 | 0 |

El HTML pesa más que una página normal porque lleva los datos dentro (es lo que hace que Google los vea sin
ejecutar nada). Aun así son 180 KB, menos que una foto de producto. El JavaScript propio son 7 KB. Cero peticiones
a servidores externos.

## 8. Lo que tienes que hacer tú

**1. ~~Publicar el repositorio en GitHub~~ HECHO el 12 de septiembre de 2026.** Está en
`github.com/xavinebot/CPC-observatorio`, público, con los tres secretos guardados y las dos tareas programadas
en verde (la diaria y la semanal). El resumen de "todo va bien" ya llegó por Telegram.

**2. ~~Cambiar la URL de los datos en el plugin~~ HECHO.** Staging lee los datos directamente del repositorio
público de GitHub, que es como funcionará producción. La carpeta temporal de datos que había en el servidor se ha
borrado. Comprobado después del cambio: la página sigue completa (9 gráficos, 21 tablas, 16 bloques Dataset) y los
24 smoke tests siguen en verde.

**3. Escribir a AVEBIOM.** Es lo único que queda pendiente por tu parte. Te dejo el correo listo:

> Asunto: Autorización para citar el Índice de Precios de Biomasa
>
> Buenos días:
>
> Soy Xavier Nebot, de Cristales para Chimeneas (cristalesparachimeneas.es). Estamos publicando un observatorio de
> precios de la calefacción para usuarios de chimeneas y estufas, con datos de fuentes oficiales (Comisión Europea,
> Eurostat, CNMC, INE), y nos gustaría incluir la serie del pellet, el hueso de aceituna y la astilla de su Índice de
> Precios de Biomasa, citando a AVEBIOM como fuente y enlazando a la página del índice en cada gráfico.
>
> Como su aviso legal pide autorización escrita previa para reproducir contenidos, les escribo para pedirla. Si lo
> prefieren, podemos limitarnos a mostrar el gráfico con la marca de AVEBIOM y sin ofrecer descarga de los datos.
>
> Quedamos a su disposición para cualquier condición que quieran establecer.

Si dicen que sí, avísame y se activa en un minuto. Si no contestan en dos semanas, la web seguirá mostrando esa
serie como pendiente, que es lo honesto.

**4. Nada más.** El token de ESIOS ya no hace falta. No hay que instalar nada en el servidor ni contratar nada.

## 9. Costes

| Concepto | Coste |
|---|---|
| GitHub Actions (tareas programadas) | 0 € (repositorio público, minutos ilimitados) |
| Todas las fuentes de datos | 0 € |
| API de Claude para clasificar productos de leña | menos de 0,10 € al mes (con caché; solo paga productos nuevos) |
| Hosting | 0 € adicionales (el servidor solo sirve las páginas; la descarga de datos ocurre en GitHub) |

**Total: por debajo de 1 € al año**, y el sistema funciona sin Claude: son Python, GitHub Actions y un plugin de
WordPress, herramientas estándar que puedes mantener o que puede mantener cualquier programador.

## 10. Riesgos de mantenimiento

| Riesgo | Probabilidad | Qué pasa y qué hacer |
|---|---|---|
| Una fuente cambia el formato de su fichero | Media (una o dos veces al año) | La descarga falla, te llega un aviso y la web sigue con el último dato bueno. Hay que ajustar el lector de esa fuente. |
| El INE cambia los códigos de sus series | Ocurrió en 2026 | La serie deja de devolver datos y avisa. Hay que actualizar el código en un fichero. |
| Una tienda de leña cambia su web o bloquea | Alta (varias al año) | Esa tienda se salta sola. Si quedan menos de tres, esa semana no se publica índice y avisa. |
| GitHub desactiva las tareas por inactividad (a los 60 días) | Baja | No puede pasar: la tarea de los lunes escribe en el repositorio cada semana. |
| Te llega un dato raro aprobado por error | Baja | Los datos están en git: se puede ver qué se publicó y volver atrás. |
| AVEBIOM dice que no | Media | La serie del pellet español se queda pendiente. El índice europeo de leña y pellet (que sí es libre) cubre Francia, Italia, Alemania, Portugal y Austria, pero no España. |

La tabla de "qué hacer cuando llegue cada aviso" está en `GITHUB_SETUP.md`, pensada para leerla desde el móvil
cuando suene Telegram.

## 11. Siguientes pasos recomendados antes de pensar en producción

Tal como pediste, esto se queda en staging. Cuando lo retomes, en este orden:

1. **Publicar el repositorio y dejarlo correr dos semanas** con las tareas programadas. Es la única forma de saber
   que las fuentes aguantan y de ver cómo se mueve el índice de la leña.
2. **Escribir a AVEBIOM** (punto 8). Es lo único que puede mejorar mucho el contenido, porque el pellet es el
   combustible que más se busca después de la leña.
3. **Revisar los textos** de las cinco páginas. Los he escrito yo y son correctos, pero el tono de la casa lo pones tú.
4. **Decidir los enlaces desde páginas existentes.** No he tocado ninguna página de la tienda, como pediste. Mi
   propuesta, para aplicar **después** de la medición del 1 de octubre y de una en una:
   - Desde `/como-limpiar-el-cristal-de-tu-chimenea/` y las guías de leña, un enlace al observatorio con el texto
     "cuánto cuesta hoy calentar con leña".
   - Desde la ficha del cristal a medida, nada: no conviene añadir salidas a la página que convierte.
   - Desde el pie de página, un enlace permanente al observatorio en los cinco idiomas. Es la forma más barata de
     que Google lo descubra y no interfiere con nada.
   - En la página de profesionales (`/b2b/`), un enlace a los índices industriales: es el argumento más creíble para
     un distribuidor.
5. **Publicar en producción cuando toque** (recuerda: nada estructural hasta febrero de 2027). El paso es: subir el
   plugin con el botón de despliegue que ya tienes, crear las siete páginas y activar el plugin. Cuando llegue el
   momento te dejo el guion, porque las páginas hay que crearlas en producción con sus propios identificadores.
6. **Cuando esté en producción, enviar el dato a quien lo usa.** Un observatorio de precios con series desde 2005 y
   descarga en CSV es exactamente lo que citan los medios del sector y los blogs de energía. Ahí está el retorno en
   enlaces, que era el objetivo principal.

## 12. Lo que quedó pendiente o sin verificar

1. **Las fechas exactas de los cambios del IVA de la leña** (21 %, 5 %, 10 %, 21 %, 10 % y otra vez 21 %) salen de
   resúmenes del sector, no del BOE. Antes de publicar el aviso en la metodología conviene comprobarlas.
2. **Si el palet de una de las cinco tiendas incluye el porte** en el precio visible. Su texto dice "envíos a toda la
   península" pero no lo afirma del precio. Un correo a la tienda lo resuelve.
3. **Factores kilos por metro cúbico de encina, olivo y roble**: solo encontré cifras de vendedores, no académicas.
   No afecta al índice (solo usamos kilos declarados), pero sería bueno citar una fuente en la metodología.
4. **La serie mensual de pellet del CEEB francés** dentro del portal de datos del ministerio: la búsqueda
   automática no la encontró. Merece un intento a mano.
5. **La etiqueta canónica y la indexación** no se pueden verificar en staging (está en "no indexar" a propósito).
