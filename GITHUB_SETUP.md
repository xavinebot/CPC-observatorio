# GITHUB_SETUP.md — poner el observatorio en marcha en GitHub

Escrito para hacerlo sin saber programar. Son cuatro pasos y unos quince minutos. Hasta que hagas esto, el
observatorio funciona en tu ordenador (con `run.cmd`) pero no se actualiza solo.

Ya tienes experiencia con esto: es el mismo procedimiento que usaste con el repositorio de los plugins, salvo que
aquí el repositorio va a ser **público**.

---

## Paso 1. Subir la carpeta a GitHub con GitHub Desktop

**Los ficheros ya están confirmados (hay dos commits hechos), así que aquí NO tienes que hacer ningún commit.**
Cuando abras el repositorio verás **"0 changed files"** y el botón de commit apagado: es lo correcto, significa que
no queda nada pendiente. Lo único que falta es publicarlo.

1. Abre **GitHub Desktop**.
2. Menú **File** → **Add local repository**.
3. Pulsa **Choose...** y selecciona la carpeta `F:\Xavi\Projectes NO G-Drive\CPC-observatorio`. Pulsa
   **Add repository**.
4. Menú **Repository** → **Publish repository…** (atajo Ctrl+P). También hay un botón azul *Publish repository*
   arriba a la derecha, pero si la ventana es estrecha queda cortado; por el menú funciona siempre.
5. En la ventana que sale:
   - Nombre: `CPC-observatorio` (déjalo como está).
   - **Desmarca la casilla "Keep this code private".** Esto es importante: el repositorio tiene que ser público
     para que la web pueda leer los datos sin ninguna clave.
   - Pulsa **Publish repository**.

Con esto los datos ya están publicados en internet. Puedes comprobarlo abriendo
`https://github.com/TU-USUARIO/CPC-observatorio` en el navegador.

## Paso 2. Guardar los dos secretos en GitHub

Los tokens no están ni pueden estar en el código. GitHub los guarda cifrados.

1. En el navegador, entra en tu repositorio `CPC-observatorio`.
2. Pestaña **Settings** (arriba, a la derecha).
3. En la columna izquierda: **Secrets and variables** → **Actions**.
4. Botón verde **New repository secret**. Añade estos tres, uno a uno (nombre exacto, respetando mayúsculas):

   | Name | Secret (valor) |
   |---|---|
   | `TELEGRAM_BOT_TOKEN` | el token del bot, el mismo que está en `C:\Users\Xavi\cpc-observatorio.env` |
   | `TELEGRAM_CHAT_ID` | el número que hay en ese mismo fichero |
   | `ANTHROPIC_API_KEY` | la clave de la API, también en ese fichero |

   Para cada uno: escribe el nombre, pega el valor y pulsa **Add secret**.

Abre el fichero `C:\Users\Xavi\cpc-observatorio.env` con el Bloc de notas para copiar los valores. Copia solo lo que
va **después** del signo igual, sin espacios.

## Paso 3. Dar permiso de escritura a la tarea programada

La tarea necesita poder guardar en el repositorio los datos nuevos que descarga.

1. En el repositorio: **Settings** → **Actions** → **General**.
2. Baja hasta **Workflow permissions**.
3. Marca **Read and write permissions** y pulsa **Save**.

## Paso 4. Probar que funciona

1. En el repositorio, pestaña **Actions**. Si sale un aviso de que los workflows están deshabilitados, pulsa el
   botón verde para habilitarlos.
2. En la columna izquierda verás **Observatorio: recogida diaria**. Pulsa en él.
3. A la derecha, botón **Run workflow** → **Run workflow**.
4. Espera dos o tres minutos y refresca. Debería aparecer con un **círculo verde**.
5. Si todo ha ido bien, en Telegram **no** recibirás nada (solo se avisa cuando hay problemas). Para comprobar que el
   aviso funciona, en la pestaña Actions lanza a mano **Observatorio: resumen semanal**: te llegará un mensaje de
   "todo va bien" con las cifras.

Ya está. A partir de ahora:

- **Cada día a las 5:40** se descargan los datos nuevos y se publican.
- **Los lunes a las 6:10** se leen las tiendas de leña y te llega el resumen semanal.
- Si algo falla, te llega un mensaje por Telegram **y** un correo de GitHub.

---

## Qué hacer cuando llegue un aviso

| El mensaje dice | Qué significa | Qué haces |
|---|---|---|
| **Datos en cuarentena** con botones | Un dato nuevo se sale de lo esperado (cambio brusco, valor raro). No se ha publicado; la web sigue con el último dato bueno. | Mira la cifra. Si el precio ha subido de verdad (lo confirmas en la web de la fuente, que viene enlazada), pulsa **Aprobar**. Si es un error de lectura, pulsa **Descartar**. La decisión se aplica en la siguiente ejecución, unas horas después. |
| **Fallos de descarga** | Una fuente no ha respondido o ha cambiado de formato. | Si es un día suelto, no hagas nada: al día siguiente se reintenta. Si se repite tres días, la fuente ha cambiado algo y hay que tocar el código. |
| **Series sin datos nuevos** | Una fuente lleva más tiempo del normal sin publicar. | Normalmente es la fuente, que va con retraso. Si una serie semanal lleva un mes parada, conviene mirar su web. |
| **Contraste entre fuentes** | El mismo dato sale distinto en dos sitios (por ejemplo el gasóleo francés en la Comisión Europea y en el ministerio francés). | Es la señal más valiosa: significa que uno de los dos se está leyendo mal. Merece revisión. |
| **Resumen semanal** (lunes) | Todo va bien. | Nada. Si un lunes **no** llega, es que el sistema ha dejado de ejecutarse: entra en la pestaña Actions a mirar. |

## Cómo revisar el estado sin Telegram

En tu ordenador, doble clic en `run.cmd` lo ejecuta todo una vez. Para ver solo el estado, abre una ventana de
comandos en la carpeta del proyecto y escribe:

```bash
python -m observatorio status
```

Te lista cada serie, su último dato y si hay algo en cuarentena.

## Si algún día quieres parar todo

En la pestaña **Actions** del repositorio, entra en cada tarea y pulsa **Disable workflow**. La web seguirá mostrando
los últimos datos descargados, sin actualizarse. Nada se rompe.
