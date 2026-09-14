# FUENTES.md — de dónde sale cada dato, con qué licencia y qué se descartó

Investigación hecha los días 11 y 12 de septiembre de 2026. Todo lo que aparece aquí se comprobó descargando una
muestra real. Cuando algo no se pudo verificar, se dice.

**Regla que manda sobre todo lo demás:** solo se publica lo que la licencia de la fuente permite publicar. Lo que
se puede recoger pero no republicar se queda recogido y sin publicar, esperando permiso.

---

## 1. Lo que se publica (fuentes admitidas)

| Dato | Países | Fuente | Frecuencia | Histórico desde | Licencia | CSV descargable |
|---|---|---|---|---|---|---|
| Gasóleo de calefacción, con y sin impuestos | ES FR IT DE PT AT | Comisión Europea, Boletín Petrolero semanal | semanal | enero 2005 | CC BY 4.0 | sí |
| Bombona de butano (precio regulado) | ES | CNMC Data | mensual | enero 1994 | CC BY-SA 4.0 | sí |
| Propano canalizado (precio regulado) | ES | CNMC Data | mensual | enero 2006 | CC BY-SA 4.0 | sí |
| Electricidad para hogares, todo incluido | ES FR IT DE PT AT | Eurostat (nrg_pc_204) | semestral | 2007 | CC BY 4.0 | sí |
| Gas natural para hogares, todo incluido | ES FR IT DE PT AT | Eurostat (nrg_pc_202) | semestral | 2007 | CC BY 4.0 | sí |
| Índices de precios de la energía del hogar (electricidad, gas, gasóleo, combustibles sólidos, leña y pellet) | ES FR IT DE PT AT | Eurostat, IPC armonizado (prc_hicp_minr) | mensual | 1996 | CC BY 4.0 | sí |
| Tarifa regulada de la luz (PVPC) y mercado mayorista, media diaria | ES | Red Eléctrica (REData) | diaria | PVPC 2021, mayorista 2014 | uso informativo con cita | **no** |
| Índice de precios de consumo de la energía | ES | INE | mensual | 2002 | libre con cita | sí |
| Precios industriales: vidrio plano, vidrio técnico, vidrio, siderurgia, estufas y cocinas, radiadores y calderas, aislantes y refractarios | ES | INE (IPRI) | mensual | 1975 / 2002 | libre con cita | sí |
| Precios industriales de vidrio, siderurgia y estufas en otros países | FR IT DE | Eurostat (sts_inppd_m) | mensual | 2005 | CC BY 4.0 | sí |
| Materias primas: gas europeo (TTF), mineral de hierro, Brent, cobre | mundial | Banco Mundial (Pink Sheet) | mensual | 1960 | CC BY 4.0 | sí |
| Índice del precio del pellet a granel | AT | proPellets Austria | mensual | enero 2006 | uso con cita, revocable | **no** |
| Índice propio del precio de la leña (palet entregado y saco) | ES | elaboración propia | semanal | septiembre 2026 | CC BY 4.0 | sí |
| Pellet, hueso de aceituna y astilla (saco, palet, granel; trimestral y media anual) | ES | AVEBIOM, Índice de Precios de Biocombustibles Sólidos | trimestral | 2012 (pellet), 2014 (hueso y astilla) | autorización escrita de AVEBIOM, 14 sep 2026 | **no** |

## 2. Lo que se recoge pero NO se publica todavía

| Dato | Fuente | Por qué no se publica |
|---|---|---|
| Pellet a granel en Alemania | C.A.R.M.E.N. e.V. | Sus condiciones piden "consulta previa" para uso comercial. Serie cargada desde 2005; publicar tras el correo. |

### Condiciones que impone AVEBIOM (autorización del 14 sep 2026)

Contestaron que sí a las tres condiciones que se les propusieron, con una precisión sobre la tercera:

1. **Citar AVEBIOM en cada gráfico y en cada tabla**, con enlace al portal que agrupa sus índices:
   `https://avebiom.org/actividades/indice-de-precios-biocombustibles-solidos/` (piden ese, no el PDF suelto).
2. **Fecha de la última actualización** y aviso de que los precios llevan el **21 % de IVA**.
3. **Sin modificar los datos.** Sobre la descarga preguntaron a qué se refería: entendían "formato no editable".
   Autorizan ofrecer **su PDF o una gráfica suya** siempre que lleven la cita del punto 1. No hay permiso explícito
   para republicar los datos en CSV, así que estas series se quedan con `redistributable=False` (sin CSV).

El correo de respuesta **es la autorización escrita** que exige su aviso legal: hay que conservarlo.

## 3. Lo que se descartó y por qué

| Candidato | Motivo del descarte |
|---|---|
| Gasóleo C en el Geoportal de gasolineras (MITECO) | En 2026 solo 11 gasolineras publican precio de gasóleo C (eran 122 en 2007). No representa nada: el gasóleo de calefacción se compra por cisterna, y ese canal es justo el que recoge el Boletín Petrolero europeo. |
| Informe mensual de carburantes del MITECO | No trae el precio del gasóleo C, solo automoción. |
| Bombona de propano de 11 kg | Su precio dejó de estar regulado en 2015: no existe fuente oficial. |
| API de ESIOS de Red Eléctrica | Requiere token por correo y no aporta nada que no dé la API abierta REData. Se documenta por si algún día hace falta el PVPC de Canarias o Baleares. |
| OMIE (mercado mayorista) | El mismo dato llega por REData. Se guarda como respaldo si REData falla. |
| Boletín de indicadores eléctricos de la CNMC | El precio medio final del consumidor solo existe como gráfico dentro de un PDF: no se puede automatizar. |
| Informes de precios del IDAE | Su aviso legal prohíbe reproducir sus tablas y el uso comercial. Los datos de fondo (BOE, Boletín Petrolero) ya los tenemos por otra vía. |
| Precio del acero europeo (MEPS, Eurofer, Platts) | De pago y no redistribuible. Sustituido por los índices oficiales de siderurgia y tubos del INE y Eurostat. |
| Litio | Sin fuente gratuita mensual (el USGS publica un precio al año en PDF) y con poca relevancia para el sector. |
| Derechos de emisión de CO2 (EU ETS) | Ninguna fuente gratuita con licencia clara: ICAP solo permite uso no comercial y con seis meses de retraso, Ember toma el dato de un proveedor comercial y los informes de subasta de EEX exigen licencia para publicarlos en una web. Queda descartado; si algún día EEX autoriza por escrito, se añade. |
| Propellet France, AIEL (Italia), DGEG (Portugal) para pellet | Publican cifras en artículos, gráficos o imágenes, sin serie numérica ni permiso de reutilización. |
| DEPI (Alemania) para pellet | Solo muestra los dos últimos años y su permiso es "para uso editorial". C.A.R.M.E.N. cubre lo mismo con histórico desde 2005. |
| Leña en Francia, Italia, Alemania y Portugal (índice propio) | En Francia y Alemania ya existen barómetros propios, y en Italia y Portugal el mercado online es local. Duplicarlo no aporta nada. |
| Leroy Merlin, Obramat, Carrefour y Amazon para el índice de leña | Prohíben expresamente la extracción automatizada en sus condiciones, y además bloquean por medios técnicos. No se tocan. |
| Precio de la luz por comunidad autónoma, o gasóleo por provincia | No existe fuente oficial y multiplicaría las páginas sin aportar valor. |

## 4. Detalle por fuente

### 4.1 Boletín Petrolero semanal de la Comisión Europea
Es la columna vertebral del gasóleo de calefacción. Cada Estado miembro comunica el precio medio de las entregas a
domicilio y la Comisión lo publica los jueves con los precios del lunes. España lo envía el MITECO y corresponde al
canal de reparto en cisterna (entregas de 2.000 a 5.000 litros), no a gasolineras.

- Un solo fichero Excel trae toda la serie desde el 3 de enero de 2005: 1.083 semanas por país.
- Unidad original: euros por 1.000 litros. El observatorio lo guarda en euros por litro.
- Se publican las dos variantes, con y sin impuestos, porque la diferencia entre países es sobre todo fiscal.
- La dirección del fichero cambia de vez en cuando, así que el recolector busca el enlace en la página del boletín
  en lugar de guardarlo fijo. Requiere identificarse con un agente de navegador.
- La propia Comisión advierte de que comparar precios entre países tiene validez limitada por diferencias de calidad
  del producto y de estructura de mercado. Ese aviso se reproduce en la web.

### 4.2 CNMC Data: butano y propano canalizado
El precio de la bombona de butano de entre 8 y 20 kilos está regulado y se revisa cada dos meses; el del propano por
tubería, cada mes. La CNMC publica la serie completa en CSV con el precio de venta al público ya calculado
(materia prima, comercialización, impuesto especial e IVA), desde enero de 1994. Es preferible al BOE porque el BOE
solo da el precio antes de impuestos y obliga a reconstruir la fiscalidad, que ha cambiado varias veces en 2026.

La licencia obliga a compartir los derivados con la misma licencia (CC BY-SA), así que el CSV descargable de estas
dos series lleva esa nota.

### 4.3 Eurostat: electricidad y gas de los hogares
Es la única serie que dice **lo que paga de verdad un hogar**, con energía, peajes, cargos e impuestos, y permite
comparar los seis países con el mismo criterio. Va por semestres y llega con cuatro o cinco meses de retraso, así
que no sirve para "el precio de hoy", pero es la referencia honesta para comparar con leña, pellet o gasóleo.

Bandas usadas: 2.500 a 5.000 kWh al año en electricidad y 20 a 200 GJ al año en gas, que son las de un hogar que se
calienta. Todos los impuestos incluidos.

### 4.4 Eurostat: índice de precios armonizado de la energía
Mide cuánto ha subido cada energía, no cuánto cuesta, y eso permite comparar países desde 1996 en una sola escala.
Incluye un subíndice de **leña y pellet** que existe para Francia, Italia, Alemania, Portugal y Austria.

**Hueco confirmado:** España no publica el subíndice de combustibles sólidos ni el de leña y pellet dentro del IPC
armonizado. Es la razón de fondo por la que el índice propio de leña tiene sentido.

Aviso técnico para el mantenimiento: en enero de 2026 Eurostat cambió de conjunto de datos (el antiguo se congeló en
diciembre de 2025) y renombró una dimensión. El recolector usa ya el nuevo.

### 4.5 Red Eléctrica (REData): PVPC y mercado mayorista
Es el dato vivo, diario. Dos series: la tarifa regulada PVPC (desde junio de 2021) y el precio del mercado mayorista
(desde enero de 2014), ambas promediadas por día.

Con una advertencia que la web deja clara: **el PVPC que publica Red Eléctrica es solo el término de energía**. No
incluye el término de potencia, ni el impuesto eléctrico, ni el IVA, ni el alquiler del contador. Presentarlo como
"lo que cuesta la luz" engañaría a la baja en un 40 o 50 %. Para "lo que cuesta la luz" está Eurostat.

El aviso legal de Red Eléctrica permite publicar sus datos en una web propia con fines informativos citando la
fuente y la fecha, pero **no** redistribuir el dato en bruto. Por eso estas dos series no tienen CSV descargable.

Límites de su API comprobados: solo admite agregación por horas y como máximo un mes por petición. La carga inicial
son unas 150 peticiones, espaciadas; después, una al día.

### 4.6 INE: IPC de la energía e índices de precios industriales
El INE da dos cosas distintas. Para el hogar, el IPC de electricidad, gas y combustibles líquidos (base 2021),
mensual desde 2002, que sirve para contrastar los índices de Eurostat. Para profesionales, el índice de precios
industriales por rama, que es lo que mide cuánto cobra la fábrica:

- vidrio plano y "otro vidrio, incluido el técnico" (la vitrocerámica entra aquí),
- siderurgia,
- estufas y cocinas no eléctricas, que es lo más cercano a "precio de fábrica de una estufa" que existe,
- radiadores y calderas de calefacción,
- aislantes y refractarios.

Aviso técnico: los códigos de serie del INE cambian cuando revisan la clasificación (pasó en 2026). Si una serie
deja de devolver datos, el sistema avisa y hay que actualizar el código.

### 4.7 Banco Mundial (Pink Sheet)
Cuatro materias primas que van por delante de los precios industriales: gas europeo (el mayor coste de fundir
vidrio), mineral de hierro (el del acero), Brent y cobre. Mensual desde 1960, en dólares. Se muestran como variación
interanual para que el tipo de cambio no ensucie la lectura.

### 4.8 proPellets Austria
Único índice de pellet de otro país con fichero descargable y histórico largo (desde 2006). Es un índice, no euros
por tonelada. Su permiso es "uso con cita" y revocable, así que se publica el índice citando la fuente pero sin CSV.

### 4.9 Índice propio de la leña (España)
No existe ninguna fuente oficial del precio de la leña en España, y el IPC armonizado tampoco lo cubre. Es lo más
diferenciador del observatorio y también lo más delicado.

**Cómo se construye.** Una pasada semanal a cinco tiendas online españolas que publican precio, kilos y condiciones
de envío sin necesidad de pasar por el carrito. De cada tienda se toma una referencia representativa; el índice es
la **mediana entre tiendas** (no entre referencias), para que una tienda con veinte productos no domine el dato. Se
publican dos series, que no se mezclan nunca:

- **Palet o saca de leña dura seca, 300 kg o más, con transporte a península incluido en el precio.** Es lo que
  compra una familia para la temporada.
- **Saco pequeño de 8 a 25 kg, precio de tienda sin portes.** Formato de conveniencia, mucho más caro por kilo.

**Reglas de la recogida.** Se respeta el fichero robots.txt de cada tienda en cada ejecución y se descarta cualquier
tienda que prohíba la extracción automatizada en sus condiciones. El agente se identifica con nombre y una dirección
de contacto. Una pasada por semana, con pausa entre peticiones. Donde la tienda ofrece una interfaz pública de
catálogo, se usa esa en vez de leer páginas. No se sortea ningún bloqueo: si una tienda responde que no, queda
fuera. No se crean carritos ni se simulan compras.

**Lo que no se publica.** Nunca una tabla con el precio actual de cada tienda con su nombre: eso sería un
comparador y podría perjudicar a quien nos da el dato. Se publica el agregado, el número de tiendas y de
referencias, y en la metodología se nombran los dominios de origen con una dirección para pedir la exclusión.

**Kilos.** Solo se usan los kilos **declarados por el vendedor**. Si una oferta está en litros o metros cúbicos y no
dice el peso, se descarta. Convertir volumen a peso tiene un margen de error de ±15 % según la especie y cómo se
apile, demasiado para un índice.

**Un detalle que importa en la serie temporal:** el IVA de la leña ha cambiado varias veces (21 %, luego 5 %, luego
10 %, otra vez 21 %, 10 % de marzo a mayo de 2026 y de nuevo 21 % desde junio de 2026). Un índice "con IVA" da un
salto del 10 % sin que la leña haya cambiado de precio. Por eso cada lectura guarda el tipo vigente y la nota
correspondiente aparece en la metodología. Las fechas exactas de esos cambios están tomadas de resúmenes
sectoriales, no del BOE: **pendiente de verificar** antes de publicar el aviso.

**Umbral de publicación.** El índice de palet necesita al menos tres tiendas válidas y el de saco, dos. Si no se
alcanzan, esa semana no se publica dato: se muestra el último con su fecha y llega un aviso. Nunca se rellena.

**Clasificación con ayuda de la API de Claude.** Interpretar "palet de 60 sacos de 15 kg de roble, humedad 18 %" a
partir del texto de una ficha con reglas fijas es frágil. Lo hace un modelo pequeño (Haiku) con una herramienta de
salida estructurada, y el resultado se guarda en caché por contenido: solo se paga cuando aparece un producto nuevo.
Coste estimado por debajo de 0,10 € al mes. Si no hay clave de API configurada, el sistema sigue funcionando con
reglas, reconociendo menos productos.

## 5. Marco legal del índice de leña (resumen)

- Una lista de precios de una tienda **no** suele ser una base de datos protegida: la inversión está en vender, no
  en recopilar datos. Así lo resolvió el Tribunal Supremo en el caso Ryanair contra Atrápalo (2012).
- Pero el Tribunal de Justicia de la Unión Europea (caso Ryanair contra PR Aviation, 2015) dejó claro que, cuando no
  hay base de datos protegida, el titular **sí puede prohibirlo por contrato**. Por eso quedan fuera las tiendas que
  lo prohíben en sus condiciones, aunque técnicamente se pudiera.
- La excepción de minería de textos y datos (directiva europea de 2019, incorporada en España en 2021) ampara
  reproducir una página para extraer datos de ella, **salvo que el titular se haya reservado ese uso**. Criterio del
  proyecto: se trata como reserva tanto el robots.txt como cualquier prohibición en el aviso legal.
- Competencia desleal: el riesgo es bajo porque quien publica el índice no vende leña y no compite con esas tiendas.
  Subiría si se publicara una tabla comparativa diaria por tienda, que es justo lo que no se hace.
- Protección de datos: los precios no son datos personales, pero varias tiendas son autónomos. Solo se guardan el
  nombre comercial y el dominio, nunca el nombre del titular ni teléfonos.
- Nada de saltarse CAPTCHAs ni protecciones: además de inútil, convierte una recogida tolerada en un acceso no
  autorizado.

## 6. Lo que no se pudo verificar

1. Las fechas exactas de los cambios del IVA de la leña (tomadas de resúmenes del sector, no del BOE).
2. Si el palet de una de las tiendas de leña incluye realmente el porte en el precio visible (su texto dice "envíos
   a toda la península" pero no lo afirma del precio).
3. Los datos italianos de gasóleo en la web del ministerio: su página necesita navegador y su interfaz responde
   con error de autorización. No hace falta: el mismo dato llega por el Boletín Petrolero.
4. El histórico del mercado mayorista español antes de 2014 y el de OMIE antes de 2018.
5. Si existe una serie central de precios de leña en Austria o Alemania (solo se encontraron informes regionales en
   PDF).
6. La serie mensual de pellet del CEEB francés dentro del portal de datos del ministerio: la búsqueda por interfaz
   automática no devolvió resultados. Merece un segundo intento navegando a mano.
