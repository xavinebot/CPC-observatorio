# DECISIONES.md — qué proponía el concepto, qué se eligió y por qué

Cada punto dice: **lo que proponía la idea inicial**, **qué alternativas se miraron** y **qué se hizo**. En lenguaje
normal, sin jerga. Fecha: 11 y 12 de septiembre de 2026.

---

## 1. ¿Dónde vive el proyecto?

**El concepto decía:** recolectores en Python, datos en el propio repositorio, un plugin ligero de WordPress.

**Alternativas:** meterlo todo en el monorepo de plugins que ya existe; o al revés, hacer una web aparte.

**Decisión:** se parte en dos.

- Los recolectores y los datos van en un repositorio nuevo, `CPC-observatorio`, fuera de Google Drive (git y Drive
  se pelean y ya hubo problemas antes).
- El plugin de WordPress va **dentro** del monorepo `CPC-plugins`, en `plugins/cpc-observatorio`, porque así se
  despliega a staging con el circuito que ya funciona (empujar los cambios y el despliegue a staging es automático,
  producción solo con botón).

**Por qué:** los datos cambian cada día y el código del plugin casi nunca. Mezclarlos haría que cada dato nuevo
disparase un despliegue a la web. Separados, la web solo lee un fichero y el plugin se toca cuando hay que cambiar
el diseño.

## 2. ¿Base de datos o ficheros?

**El concepto decía:** CSV/JSON en el repositorio, sin base de datos. **Se mantiene.**

Una serie es un fichero de texto con dos columnas, fecha y valor. Con 96 series y datos desde 1960, todo junto pesa
unos pocos megas. Ventajas concretas: cada cambio queda en el historial de git (se ve qué dato cambió y cuándo, y se
puede volver atrás), no hay nada que administrar ni que pueda corromperse, y el usuario puede abrir cualquier fichero
con el Bloc de notas o Excel. Una base de datos sería una pieza más que mantener sin ganar nada.

## 3. ¿Cómo lee la web los datos?

**El concepto decía:** un plugin que lee los datos, los cachea y muestra gráficos y tablas.

**Alternativas:** (a) que el plugin lea los ficheros del repositorio por internet; (b) subir los datos al servidor
por el mismo despliegue; (c) meter los datos en la base de datos de WordPress.

**Decisión:** (a). El repositorio de datos es **público**, y el plugin descarga un fichero JSON por país y lo guarda
en caché seis horas. Si GitHub no responde, el plugin sigue mostrando la última copia buena que guardó.

**Por qué:** la web no necesita permisos ni claves para leer un repositorio público, el servidor no tiene que
guardar nada y la página no depende de que un despliegue haya ido bien. Además hace el proyecto transparente, que es
la mitad del valor de un observatorio.

## 4. Comparar combustibles: la decisión más importante del contenido

**El concepto decía:** combustibles comparables en la misma unidad, €/kWh.

**Problema:** €/kWh a secas no es comparable. Un kilo de pellet tiene 4,8 kWh, pero una estufa de pellets aprovecha
el 88 %; una chimenea abierta de leña aprovecha el 15 %. Y un kWh de electricidad en un radiador rinde el 100 %,
pero con una bomba de calor rinde el 300 %.

**Decisión:** se compara en **euros por kWh de calor útil**: el precio dividido por los kWh que de verdad llegan a la
habitación con un aparato típico. La tabla de rendimientos y poderes caloríficos está publicada en la página de
metodología, con su fuente, y se puede cambiar en un sitio único. La electricidad aparece dos veces: con radiador y
con bomba de calor, porque la diferencia es enorme y omitirla sería engañoso.

**Por qué:** es el número que responde a la pregunta que se hace el lector ("¿con qué me sale más barato calentar la
casa?") y a la vez es honesto, porque se ve de dónde sale cada factor.

## 5. El precio de la luz: dos series, no una

**El concepto decía:** electricidad vía la API de ESIOS de Red Eléctrica, que necesita token.

**Alternativas miradas:** ESIOS (token por correo), la API abierta REData de Red Eléctrica (sin token), OMIE, la
CNMC y Eurostat.

**Decisión:** ninguna sola sirve, así que se publican dos cosas distintas y bien etiquetadas:

- **Lo que paga de verdad un hogar**, con impuestos y peajes: Eurostat, semestral, desde 2007, para los seis países.
  Es la serie que entra en la comparativa de combustibles.
- **El dato vivo diario**: la tarifa regulada PVPC y el mercado mayorista, de la API abierta de Red Eléctrica, con la
  advertencia de que es solo el término de energía.

**Por qué no ESIOS:** habría que pedir un token por correo y esperar días, y no aporta nada que la API abierta no dé.
Se documenta por si algún día se necesita el precio de Canarias o Baleares.

**Por qué no mostrar solo el precio mayorista:** es menos de la mitad de lo que se paga. Publicarlo como "el precio
de la luz" sería el error típico de los medios y restaría credibilidad.

## 6. Pellet: recogido pero no publicado

**El concepto decía:** índice trimestral de AVEBIOM, publicado en PDF; y en la conversación previa se propuso
rasparlo, incluso con ayuda de la API de Claude si cambiaba el diseño del PDF.

**Lo que se encontró:** el PDF se lee bien y trae el histórico completo (pellet desde 2012, hueso y astilla desde
2014), pero **el aviso legal de AVEBIOM exige autorización escrita previa** para reproducir sus contenidos.

**Alternativas:** publicar igualmente citando la fuente (lo hacen varios medios); usar otra fuente; no publicarlo.

**Decisión:** se construye el recolector y se carga el histórico, pero la serie queda **marcada como no publicable**:
en la web aparece como "pendiente" y no se ofrece descarga. Hay que escribir a AVEBIOM pidiendo permiso. Con un sí
por escrito, se activa cambiando una palabra en la configuración.

**Por qué:** que otros lo hagan no es una autorización, y el proyecto va a pedir enlaces y credibilidad a gente del
sector. Empezar incumpliendo el aviso legal de la asociación de la biomasa española sería un mal negocio.

**Desenlace (14 de septiembre de 2026): AVEBIOM dijo que sí.** Contestaron al correo aceptando las tres condiciones
que se les proponían, y las diez series ya están publicadas. Piden que el enlace vaya a su portal de índices y no al
PDF, y no se ofrece CSV de sus datos. Detalle en FUENTES.md. La apuesta de pedir permiso en vez de copiar salió
bien y además deja una relación abierta con la asociación del sector, que era la mitad del motivo.

El mismo criterio se aplica al pellet alemán de C.A.R.M.E.N. (piden "consulta previa" para uso comercial). El índice
austriaco de proPellets sí se publica, porque su aviso permite el uso citando la fuente, pero sin CSV descargable.

## 7. Leña: sí al índice propio, pero con límites estrictos

**El concepto decía:** índice propio raspando tiendas y normalizando a €/kg con transporte incluido, usando la API
de Claude. Y pedía evaluar viabilidad técnica y legal antes de construirlo.

**Lo que se comprobó, tienda por tienda:** de una veintena de tiendas españolas, cinco publican precio, kilos y
condiciones de envío de forma utilizable y no prohíben la extracción. Las grandes superficies quedan fuera: Amazon y
Leroy Merlin lo prohíben expresamente en sus condiciones, y además bloquean por medios técnicos.

**Decisión:** se construye, con estas reglas (detalle en FUENTES.md):

- Dos series separadas que no se mezclan: palet entregado y saco pequeño sin portes.
- Mediana **entre tiendas**, no entre productos.
- Solo kilos declarados por el vendedor. Nada de convertir litros o metros cúbicos: el error sería del ±15 %.
- Se publica el agregado con el número de tiendas; **nunca** una tabla de precios por tienda con nombre.
- Si una semana no hay tiendas suficientes, no se publica dato y llega un aviso. Nunca se rellena.
- Se respeta robots.txt en cada ejecución y no se sortea ningún bloqueo.

**Sobre la API de Claude:** sí se usa, pero solo para lo que hace falta, interpretar el texto de la ficha ("palet de
60 sacos de 15 kg de roble al 18 % de humedad"). Con reglas fijas esto se rompe cada vez que una tienda cambia una
palabra. El resultado se guarda en caché, así que solo se paga por producto nuevo: menos de 0,10 € al mes. Si no hay
clave configurada, el sistema sigue con reglas y lo dice.

**Lo que se descartó:** hacer el índice también en Francia, Italia, Alemania y Portugal. En Francia y Alemania ya
existen barómetros propios y en Italia y Portugal el mercado online es local. No aporta nada.

## 8. Materias primas para profesionales

**El concepto decía:** índices industriales del INE y Eurostat, y materias primas como el litio, "comprobar si hay
fuente libre; si no, descartarlo y documentarlo".

**Decisión:** siete índices del INE para España (vidrio plano, vidrio técnico, vidrio, siderurgia, estufas y
cocinas, radiadores y calderas, aislantes y refractarios), los mismos de Eurostat para Francia, Italia y Alemania
(para poder decir "las estufas alemanas se encarecen más que las españolas"), y cuatro materias primas del Banco
Mundial que van por delante: gas europeo, mineral de hierro, Brent y cobre.

**Descartados con su motivo:** el litio (sin fuente mensual gratuita y casi irrelevante para el sector), el precio
del acero europeo (de pago; cubierto por los índices oficiales de siderurgia) y los derechos de emisión de CO2
(ninguna fuente gratuita con licencia clara para publicarlos).

## 9. ¿Cuántas páginas? La decisión de SEO

**El concepto decía:** pocas páginas y mucho valor, por ejemplo una por país o idioma más una de metodología.

**Alternativas:** una página por combustible (más palabras clave, más riesgo de páginas flojas); una página por
provincia o por fecha (descartado de entrada, no hay datos y sería basura).

**Decisión:** **siete páginas en total**: una principal por idioma (cinco), una de metodología y una para
profesionales. La página principal de cada idioma lleva la comparativa, todas las series de combustibles de ese
país, las tablas y las descargas.

**Por qué:** la web ya tiene miles de páginas sin indexar; añadir cuarenta páginas de datos empeoraría eso. Y el
valor está en tener todo junto y bien presentado, que es exactamente lo que busca quien enlaza.

## 10. Gráficos: dibujados en el servidor, no con una librería

**El concepto decía:** gráficos rápidos, datos también en tabla HTML y no solo en gráficos de JavaScript.

**Alternativas:** una librería de gráficos (Chart.js, ApexCharts) o dibujar en el servidor.

**Decisión:** el servidor dibuja el gráfico como imagen vectorial (SVG) dentro del propio HTML, y un fichero de
JavaScript propio de 6 KB añade solo dos cosas: la etiqueta al pasar el ratón y los botones de rango. Sin ninguna
librería externa.

**Por qué:** Google ve el gráfico y la tabla sin ejecutar nada; la página carga sin esperar a ningún script; y no
hay una dependencia de terceros que actualizar cada año. Además el CSS y el JS solo se cargan en las páginas del
observatorio, así que el resto de la tienda no se entera. Esto último era un requisito.

## 11. Avisos: Telegram, y uno solo por ejecución

**El concepto decía:** bot de Telegram, valorando alternativas.

**Alternativas:** correo (lo más simple, pero se pierde entre el resto), Telegram (llega al móvil, gratis, y permite
botones), o las notificaciones que GitHub ya manda cuando algo falla.

**Decisión:** Telegram con botones de "aprobar" y "descartar" directamente en el mensaje, más el correo automático de
GitHub como segunda red por si el propio aviso fallara.

**Corrección aplicada durante el desarrollo:** la primera versión mandaba un mensaje por cada serie en cuarentena y
en la carga inicial llegaron decenas de golpe. Ahora se manda **un solo mensaje por ejecución** con todas las series
afectadas y sus botones.

## 12. La cuarentena y la carga del histórico

**El concepto decía:** validar antes de guardar, incluida una variación máxima respecto al dato anterior.

**Problema que apareció:** al cargar veinte años de historia, la regla de "no más de un 30 % de golpe" marcaba como
sospechosos los saltos **reales** de la crisis energética de 2022.

**Decisión:** la regla de variación máxima se aplica en las ejecuciones normales, que es cuando protege de un error
de lectura, pero **no** al cargar el histórico oficial de una fuente. El resto de comprobaciones (formato, rango
lógico, fecha no futura, volumen mínimo de registros) se aplican siempre.

**Por qué:** en la carga inicial no hay ningún "último valor bueno" que proteger y los datos vienen del fichero
oficial completo. Mantener la regla ahí solo generaba ruido y enseñaba al usuario a ignorar los avisos, que es lo
peor que le puede pasar a un sistema de alertas.

## 13. Ejecución programada: GitHub Actions

**El concepto decía:** GitHub Actions. **Se mantiene**, con dos frecuencias:

- **Cada día** a las 5:40 (hora peninsular): todo lo que puede cambiar a diario o casi.
- **Los lunes**: la pasada de tiendas de leña (la leña no cambia de precio a diario) y el resumen semanal de "todo
  va bien", que es lo que avisa de que el sistema ha dejado de ejecutarse.

**Por qué GitHub Actions y no el servidor:** el hosting es compartido y ya va justo de CPU; meterle ahí un proceso
diario que descarga ficheros de varios megas sería empeorar un problema que ya existe. En GitHub es gratis para este
volumen, funciona con el ordenador apagado y avisa por correo si falla.

**Aviso conocido:** GitHub desactiva las tareas programadas de un repositorio si pasan 60 días sin actividad. El
resumen semanal escribe en el repositorio cada lunes, así que la actividad nunca se detiene sola.

## 14. Lo que NO hace el plugin, a propósito

No toca precios, ni carrito, ni checkout, ni geolocalización, ni el configurador de medidas. No añade nada al resto
de páginas de la tienda: su CSS y su JavaScript solo se cargan donde está el shortcode. No escribe en la base de
datos más que su propia caché y sus ajustes. Y no interfiere con la caché de página: es contenido que cambia una vez
al día como mucho.

## 15. Enlaces hacia la tienda

**El concepto decía:** enlazado hacia la tienda, natural y útil; y los enlaces desde páginas existentes, propuestos
por escrito pero no aplicados.

**Decisión:** las páginas nuevas llevan un bloque al final con el enlace a la tienda, redactado como lo que es: si
tienes chimenea y el cristal está roto o ahumado, aquí se corta a medida. Los enlaces **desde** páginas existentes
están propuestos en INFORME.md y **no se han aplicado**, porque tocar las páginas que se están midiendo rompería la
medición de octubre.

## 16. Una serie de otro país dentro de una página (Austria en la alemana)

**El problema:** Alemania no tiene ninguna serie de precio del pellet que se pueda reutilizar. La de C.A.R.M.E.N.
e.V. pide consulta previa para uso comercial y sigue **recogida pero sin publicar**. Y el pellet es, después de la
leña, lo que más busca un lector alemán.

**Decisión (14 sep 2026): sí se publica una serie de otro país, pero diciéndolo.** En la página alemana aparece el
índice de proPellets Austria, con tres condiciones que no se negocian:

1. **Dicho en el propio texto** que es austriaco y que **no es un precio alemán**, con el motivo (los dos países
   compran en buena medida en el mismo mercado) y la metodología (más de 50 distribuidores, pellet ENplus A1 a
   granel, pedidos de 6 t, base enero de 2006).
2. **Sin descarga.** proPellets autoriza el uso citando la fuente, no la redistribución: la serie va con
   `redistributable=False`, así que no genera CSV ni declara descarga en el marcado de datos. Hay un test que lo
   comprueba en cada despliegue.
3. **En el marcado de datos, su país es Austria**, no Alemania. Quien lea el conjunto de datos ve lo mismo que
   quien lee la página.

**Lo que NO se hace:** dar el número austriaco como alemán, ni mezclarlo en la misma línea del gráfico con datos
alemanes, ni meterlo en la comparativa de euros por kWh útil de Alemania. Un dato de otro país sirve de referencia;
no sirve para responder "cuánto cuesta calentar mi casa aquí".

**Regla general que queda:** una serie de un país puede aparecer en la página de otro **solo** si se dice de dónde
es, por qué está ahí y qué no se puede concluir de ella.

## 17. España no aparece en la comparación europea de la leña, y se dice por qué

Eurostat no publica para España la subclase de leña y pellet del índice armonizado; el INE no la desglosa. La
tentación es no mencionar a España y que nadie se pregunte nada. **Decisión: nombrarlo.** La nota de la tabla dice
que España falta y por qué, y aprovecha para decir que para España hay algo mejor, precios en euros por kilo del
índice de AVEBIOM. Un hueco explicado da más confianza que una tabla que disimula.

## 18. Quién es "el vecino" lo decide la página, no el catálogo

La página de profesionales existía solo para España y, dentro de ella, había una familia llamada "los mismos
índices en Francia, Italia y Alemania". Esa etiqueta estaba escrita en el catálogo, serie por serie: el índice del
vidrio francés era, para siempre, una serie de comparación.

Al montar la página para los cinco países eso deja de funcionar: **el índice del vidrio francés es el dato propio
de la página francesa y la comparación en la española**. Es la misma serie y tiene que salir en dos sitios
distintos según quién la mire.

**Decisión (15 sep 2026): cada serie lleva en el catálogo su familia natural** —el vidrio con el vidrio, el acero y
las estufas con lo que compra un fabricante, la energía con la energía— y **es la página la que marca como "vecina"
todo lo que no es de su país** al cargar los datos. Las materias primas del vitrocerámico son de comercio exterior
de la Unión Europea, así que cuentan como propias en los cinco.

**El bloque de comparación pasa a ser un gráfico por rama**, no uno con cuarenta líneas: el vidrio con el vidrio de
los otros cuatro países, el acero con el acero. Mezclar ramas en un eje no compara nada. Una rama con una sola
serie no sale: una línea suelta no es una comparación. Y esos gráficos van sin tabla y con seis años en vez de
diez, porque son una docena en la misma página y los números de cada serie están en la página de su país y en su
CSV.

**Lo que NO se hace:** inventar el dato que un país no publica. Portugal solo da el vidrio, así que la página
portuguesa tiene una sección propia corta y un bloque de comparación largo. Se ve el hueco, que es la verdad.

## 19. Cuando un mes tiene dos precios, vale el que está en vigor

El precio regulado del butano se revisa cada dos meses, pero algunos meses cambia **dos veces**: el fichero de la
CNMC trae entonces dos filas con la misma fecha y distinta "Entrada en vigor". Se guardaban las dos y se quedaba
una u otra según el orden del fichero, así que unos meses llevaban el precio de principios de mes y otros el de
mediados. En septiembre de 2026 eso hizo que la web enseñara **1,4362 €/kg cuando desde el día 15 el precio era
1,5073**: un 5 % de diferencia en el dato más consultado de la página española.

**Decisión (17 sep 2026): de cada mes se guarda la última revisión que entró en vigor.** Es la que responde a la
pregunta que trae al lector, que es cuánto cuesta ahora, no cuánto costaba el día 1. Corrige también marzo de
2026, que llevaba el precio del día 17 cuando el del día 22 lo había sustituido.

**Lo que NO se hace:** quedarse con el primero por comodidad, ni promediar los dos. Un promedio no es un precio
que nadie haya pagado nunca, y el histórico dejaría de ser comparable con el de la CNMC.

## 20. Un aviso falso repetido enseña a ignorar los avisos

El contraste entre el IPC del INE y el índice armonizado de Eurostat comparaba **el último punto de cada serie**.
El INE publica antes que Eurostat, así que se estaba comparando la variación interanual de agosto con la de julio.
En una serie movida como los combustibles líquidos, dos meses seguidos se llevan quince puntos sin que pase nada,
y el aviso saltó tres días seguidos diciendo que había una discrepancia de 14,9 puntos.

**No la había.** Comparando el mismo mes, el INE y Eurostat coinciden al decimal: 0,0 puntos de diferencia en
combustibles líquidos y en electricidad, y menos de 3,1 en gas.

**Decisión (17 sep 2026): el contraste compara siempre el último mes que está en las dos series.** El daño de un
aviso falso que se repite no es el rato que se pierde mirándolo: es que enseña a no mirar los avisos, y entonces
el día que salta uno de verdad tampoco se mira.

## 21. Dos valores para la misma fecha: ante la duda, no se publica

Después de lo del butano (§19) se auditaron **los catorce recolectores** preguntándoles los datos y mirando el
lote antes de validarlo. Apareció un segundo caso: el fichero del ministerio francés apila **tres tablas en la
misma hoja** —las lecturas semanales, debajo "MOYENNES MENSUELLES" y al final las anuales— y se leían todas, así
que la serie mezclaba lecturas semanales con medias mensuales. En las once semanas que cayeron en día 1 salían
dos valores distintos para la misma fecha. Esa serie no se publica (solo sirve para contrastar el Boletín
Petrolero), pero el contraste estaba comparando peras con manzanas.

**Decisión (17 sep 2026): la validación rechaza las fechas que llegan dos veces con valores distintos.** No se
elige una, no se promedian: **las dos van a cuarentena y salta el aviso**, y se arregla el recolector para que
diga cuál vale. Elegir por el orden del fichero es decidir el dato a cara o cruz.

Es la misma regla que ya regía para todo lo demás —un hueco explicado vale más que un número inventado—, solo que
ahora también cubre el caso de la fuente que dice dos cosas a la vez. Dos pruebas lo fijan, y la auditoría de los
catorce recolectores sale limpia.

## 22. Enseñar un dato no es entregarlo: la serie "solo vista"

C.A.R.M.E.N. e.V. autorizó publicar su precio del pellet alemán desde 2005 **con una condición**: que de la
gráfica no se puedan sacar los valores numéricos. Antes de aceptarla había que comprobar si era cierta, y **no lo
era**: nuestros gráficos llevan los puntos como JSON dentro de la página y enseñan la cifra exacta al pasar el
ratón. Escribirles «de una gráfica no se copian números» y publicar así habría sido faltar a la palabra dada, con
la única fuente que existe para el pellet alemán.

**Decisión (23 sep 2026): una serie puede marcarse `solo_vista`.** Cuando lo está:

- el gráfico se dibuja **sin los datos dentro** y sin la etiqueta del ratón (el JavaScript se aparta solo al no
  encontrarlos, así que tampoco salen los botones de rango);
- se dibuja **entero**, porque sin botones el lector no podría pedir «Todo» y ese sería el único recorrido que
  vería nunca;
- la tabla se queda en **el último dato y el anterior**, que es lo que publica la propia fuente;
- **no hay tabla de medias anuales**: veintiún años en filas son un CSV con otra ropa;
- no hay descarga ni gráfico incrustable, que ya venían de `redistributable=False`.

**Lo que NO se hace:** publicar los números redondeados para que «no sean exactos». Eso sería publicar un dato
alterado, que es peor que no publicarlo.

**La promesa vive en un test**, no en la memoria de nadie: comprueba las ocho cosas en cada despliegue. Una
condición que una fuente pone por escrito tiene que poder romperse solo con un test en rojo.

**Y una regla de orden, aprendida a la mala el mismo día:** los datos llegan a producción por GitHub y el plugin
por despliegue. Si los datos viajan primero, la web enseña la serie con las reglas viejas. **Primero el plugin,
después los datos.** Pasó, se revirtió en minutos y no llegó a verse, pero es la segunda vez que este orden
muerde.
