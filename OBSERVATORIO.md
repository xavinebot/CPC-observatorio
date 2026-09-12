
## 8. Puesta en marcha completada (12 sep 2026, mismo día)

- Repositorio publicado: **`github.com/xavinebot/CPC-observatorio`** (público), con los tres secretos guardados y
  permiso de escritura para las tareas.
- **Las dos tareas programadas han corrido en verde**: la recogida diaria y la semanal. El resumen de "todo va
  bien" llegó por Telegram.
- **Staging ya lee los datos de GitHub**, no del servidor: es exactamente el camino que usará producción. La
  carpeta temporal `wp-content/uploads/observatorio/` se ha borrado.
- Comprobado después del cambio: la página española sigue completa (9 gráficos, 21 tablas, 16 bloques Dataset,
  fecha de actualización correcta) y los **24 smoke tests en verde**.
- **Arreglo de AVEBIOM** (primer aviso real del sistema, y funcionó): habían cambiado la dirección de su página del
  índice. El recolector ahora prueba las dos direcciones y, si la página no responde igual, tantea las direcciones
  previsibles de los PDF. Además se añadió la marca de "fuente opcional": como su dato no se publica, un fallo suyo
  se anota en el resumen semanal pero no manda aviso de incidencia.
- **Rutina cuando GitHub y el ordenador han cambiado los dos** (pasará cada vez que la tarea guarde datos y además
  se toque algo en local): en GitHub Desktop, **Fetch → Pull → Push**. No es un error.

**Pendiente solo de Xavier:** el correo a AVEBIOM (redactado en `INFORME.md`, punto 8) y dejar correr el sistema dos
semanas antes de dar por bueno el índice de la leña.
