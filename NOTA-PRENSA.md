# Nota de prensa y correo a periodistas

> **Preparado el 14 de septiembre de 2026. NO enviar todavía.** La sección está en staging; hasta que no esté en
> producción no hay enlace que dar. La ventana buena para enviarlo es la **segunda quincena de octubre y la primera
> de noviembre**, que es cuando se escriben los artículos de "cuánto te va a costar la calefacción este invierno"
> (razonamiento en `SEO.md`, apartado 26.5).
>
> **Antes de enviar, actualizar los números.** Al final de este documento está la orden exacta para sacarlos.

---

## 1. La nota (media página)

**El gasóleo de calefacción cuesta un 56 % más que hace un año al empezar la temporada**

El gasóleo de calefacción se paga en España a **1,3962 euros por litro** (dato del 7 de septiembre de 2026, el
último del Boletín Petrolero semanal de la Comisión Europea). Hace justo un año, el 8 de septiembre de 2025, estaba
a **0,8939 euros**. Es una subida del **56,2 % en doce meses**, y **seis de cada diez céntimos de esa subida son
de los últimos tres meses**: el 8 de junio el litro estaba todavía a 1,0915 euros.

El movimiento lo confirma una segunda fuente independiente: el índice armonizado de precios de consumo de los
combustibles líquidos, que elaboran el INE y Eurostat, sube un **31,5 % interanual** en julio de 2026.

Para poner la cifra en contexto: el máximo de la serie, que arranca en 2005, es de **1,5937 euros** en junio de
2022. El precio de hoy sigue un 12 % por debajo de aquel récord.

**Qué significa para una casa.** Convertido a euros por kilovatio hora de **calor útil** —es decir, teniendo en
cuenta la energía que lleva cada combustible y el rendimiento real del aparato que lo quema— el gasóleo sale hoy a
**0,155 €/kWh**. Calentar una vivienda que necesite 10.000 kWh de calor al año costaría unos **1.550 euros** de
gasóleo, frente a unos 1.260 de butano, 1.040 de gas natural, 900 de pellet en saco, 890 con una bomba de calor y
640 de hueso de aceituna. Un radiador eléctrico, la forma más cara, se iría a unos 2.670.

**De dónde salen los datos.** Todas las series son públicas y de fuentes oficiales: el Boletín Petrolero semanal de
la Comisión Europea, Eurostat, la CNMC, el INE y el Índice de Precios de Biocombustibles Sólidos de AVEBIOM. Se
publican con la fecha del último dato, la licencia de cada fuente y el histórico completo —el gasóleo desde 2005, el
butano desde 1994— y se pueden descargar en CSV.

**Observatorio de precios de la calefacción**
`https://cristalesparachimeneas.es/observatorio-precios-calefaccion/`
Actualizado cada día. Datos, sin opiniones ni previsiones.

---

## 2. El correo (lo que se manda de verdad)

Un periodista no abre una nota de prensa adjunta. Abre un correo de cinco líneas con un número. Asunto y cuerpo:

**Asunto:** El gasóleo de calefacción, un 56 % más caro que hace un año (dato oficial, con la serie desde 2005)

> Buenos días:
>
> Por si le sirve para la temporada: el gasóleo de calefacción está a 1,3962 €/l, frente a 0,8939 hace justo un
> año. Un **+56,2 % en doce meses**. Es el dato del Boletín Petrolero semanal de la Comisión Europea del 7 de
> septiembre, y el índice del INE para combustibles líquidos apunta en la misma dirección (+31,5 % interanual).
>
> Tenemos la serie completa desde 2005 y la comparación de todos los combustibles en euros por kWh de calor útil,
> con la fuente y la fecha de cada dato: [enlace]
>
> Si le viene bien, **la serie entera se descarga en CSV** desde esa misma página, lista para su gráfico. Y si
> necesita otra cosa —el butano desde 1994, el pellet, la electricidad—, dígamelo y se lo mando.
>
> Un saludo,
> Xavier Nebot · Cristales para Chimeneas

**Reglas al escribir:**

- **Un solo número** en el asunto. Si el correo lleva tres cifras, no se cita ninguna.
- **No se manda "la sección"**, se manda el dato y el sitio donde comprobarlo. Lo que se le ahorra al periodista es
  la tarde de buscar la fuente y montar el gráfico.
- **Nada de previsiones.** Ni "seguirá subiendo" ni "el invierno será caro". En cuanto aparece una opinión, el dato
  deja de ser dato y el correo pasa a ser publicidad.
- **Sin adjuntos.** Enlace y CSV.

---

## 3. Orden de envío (del más fácil al más difícil)

1. **`datos.gob.es`** — admite conjuntos de datos con licencia abierta y las series son CC BY. No hay que convencer
   a nadie. Y comprobar que las páginas salen en **Google Dataset Search**: el marcado ya está puesto.
2. **Las fuentes y las asociaciones del sector** — AVEBIOM (que ya autorizó el uso de su índice) y proPellets
   Austria, cuyo índice se publica citándoles en la página alemana. Una asociación enlaza de buena gana a quien la
   cita bien.
3. **Periodistas de consumo y energía**, en la ventana de octubre-noviembre. Este correo.
4. **Blogs de calefacción, estufas y biomasa** — a estos no les interesa el número, les interesa el gráfico
   incrustable (pendiente de montar, ver abajo).
5. **Foros** — no dan enlaces que cuenten para Google, pero traen visitas y son donde te descubre quien luego sí
   enlaza. Contestando preguntas con el dato, no soltando el enlace.

**Wikipedia, no.** Sus normas prohíben añadir enlaces al sitio de uno mismo. Si el observatorio llega a ser una
referencia, ya lo enlazará alguien.

---

## 4. Lo que falta por montar antes del punto 4 de esa lista

El **gráfico incrustable**: un recuadro debajo de cada gráfico con el código listo para copiar, de forma que un blog
pueda pegarlo y le salga la imagen actualizada con un enlace de vuelta. Hace falta servir cada gráfico como imagen
SVG con sus estilos dentro (hoy el color y el grosor de las líneas vienen de la hoja de estilos de la página, y una
imagen suelta no la lee). Es trabajo de plugin, media tarde, y no corre prisa hasta que la sección esté publicada.

---

## 5. Cómo actualizar los números antes de enviar

Desde la carpeta del repositorio de datos:

```
python -m observatorio prensa
```

Saca el último dato del gasóleo y el de hace doce meses con la variación, cuánto de esa subida es de los últimos
tres meses, el máximo y el mínimo de todo el histórico, el contraste con el índice del INE/Eurostat y las otras
cuatro series principales, por si en octubre la historia es otra.

Lo que **no** saca, a propósito, es la comparación en euros por kWh de calor útil ni el coste anual de 10.000 kWh:
el rendimiento de cada aparato está definido en el plugin y tenerlo también en el lado de los datos sería la mejor
forma de que un día los dos números no coincidan. Esas cifras se leen de la propia página, en la tabla de portada y
en el desplegable "¿cuánto cuesta calentar una casa al año?", que es además lo que verá el periodista.

**Y la regla de siempre: si al actualizar el número la historia cambia, se cambia la nota.** Si en octubre el
gasóleo ha bajado, el titular es que ha bajado. No se envía un número viejo porque sea mejor.
