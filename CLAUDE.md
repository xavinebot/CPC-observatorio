# CLAUDE.md — Observatorio de precios de calefacción (CPC-observatorio)

Proyecto de **cristalesparachimeneas.es**: una sección de la tienda que publica **datos de precios** (combustibles de
calefacción por país en €/kWh, índices industriales para profesionales) con series históricas largas, fuente y fecha
visibles. Publicamos datos, no opiniones. Objetivo de negocio: enlaces y autoridad, visibilidad de marca, tráfico a la
tienda.

Contexto del negocio: `F:\Xavi\Projectes NO G-Drive\CPC-plugins\NEGOCIO.md` (y su `CLAUDE.md`). El hub de documentación
del usuario está en `F:\Xavi\Projectes G-Drive\NBS\Web CPC\Claude\` (fichero de estado de este proyecto: `OBSERVATORIO.md`).

## Reglas de trabajo (no negociables)

- **El usuario no es programador.** Explicar el qué y el porqué; recomendaciones, no listas de opciones.
- **Nada en producción.** Todo se prueba en local y en `staging.cristalesparachimeneas.es`. Hasta febrero de 2027 no hay
  cambios estructurales en producción.
- **Nunca se inventan ni rellenan datos.** Si una fuente falla, la serie queda "pendiente"; jamás datos simulados.
- **Secretos fuera del repositorio**: se leen de variables de entorno o del fichero `C:\Users\Xavi\cpc-observatorio.env`
  (local). En GitHub, de *Secrets*. Nunca en el código ni en los .md.
- **Respetar términos de uso y robots.txt** de cada fuente; citar siempre la procedencia. Lo que no se pueda
  redistribuir, no se publica.
- **Pocas piezas**: Python estándar + pocas dependencias; datos en CSV/JSON dentro del repo; sin base de datos.
- **SEO**: pocas URLs y mucho valor. No crear páginas por fecha, provincia ni combustible suelto.
- El plugin de WordPress **no toca** precios, checkout, geolocalización ni UniCPO. Solo lee JSON y pinta.

## Dónde está cada cosa

| Pieza | Ruta |
|---|---|
| Recolectores, validación, cuarentena, avisos, publicación | `observatorio/` (paquete Python) |
| Definición de series (id, unidad, fuente, licencia, frecuencia esperada) | `observatorio/catalog.py` |
| Datos guardados (una serie = un CSV `fecha,valor`) | `data/series/` |
| Datos en cuarentena (pendientes de aprobar) | `data/quarantine/` |
| Estado de ejecuciones (última buena, fallos seguidos) | `data/state.json` |
| JSON que lee la web (uno por país + índice) | `data/published/` |
| Tests | `tests/` (`python -m pytest`) |
| Ejecución programada | `.github/workflows/observatorio.yml` |
| Plugin WordPress | monorepo `CPC-plugins/plugins/cpc-observatorio/` |
| Documentación de entrega | `FUENTES.md`, `DECISIONES.md`, `GITHUB_SETUP.md`, `INFORME.md` |

## Comandos

- Todo en local: `run.cmd` (equivale a `python -m observatorio run`).
- Una sola fuente: `python -m observatorio run --only wob_heating_oil`.
- Estado: `python -m observatorio status`. Cuarentena: `python -m observatorio approve <id>` / `discard <id>`.
- Aviso de prueba: `python -m observatorio test-alert`. Resumen semanal: `python -m observatorio summary`.
- Tests: `python -m pytest -q`.

## Cómo añadir una fuente

1. Definir la serie en `catalog.py` (unidad, país, frecuencia esperada, rango lógico, variación máxima, licencia, cita).
2. Crear `observatorio/collectors/<nombre>.py` con una clase que herede de `Collector` y devuelva puntos `(fecha, valor)`.
3. Registrarla en `observatorio/collectors/__init__.py`.
4. Añadir un test con una muestra real de la respuesta de la fuente en `tests/fixtures/`.
5. Documentarla en `FUENTES.md` (formato, licencia, cómo citar).

## Al terminar una sesión

Actualizar `OBSERVATORIO.md` en el hub (`Web CPC\Claude\`): qué se hizo, con fecha, qué queda y qué se decidió.
Añadir, nunca reescribir.
