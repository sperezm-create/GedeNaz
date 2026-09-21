# GedeNaz App — Cliente Android

Este directorio va a contener la app Android que consume la API en `src/gedenaz/` (ver [docs/specs/03-arquitectura.md](../docs/specs/03-arquitectura.md)).

**El backend está completo** (inventario RF1–RF4, ventas RF5 y reporte de producto más vendido RF3.1): `https://gedenaz-api.onrender.com`. *(Ventas y reportes están en el código y en el contrato, pero llegan a esa URL con el próximo "Manual Deploy" en Render — hasta entonces producción solo tiene inventario.)* El contrato HTTP completo (endpoints, formato de cada request/response, formato de errores) está en [docs/specs/06-referencia-api.md](../docs/specs/06-referencia-api.md) — léanlo antes de empezar a programar el networking de la app, sea cual sea el framework elegido.

## Pendiente

- [ ] Elegir el framework: Kotlin nativo (Android Studio), Flutter (Dart) o Python (Kivy/BeeWare). Ver la comparación en la bitácora del proyecto (2026-09-09).
- [ ] Documentar la decisión y el porqué en `docs/specs/03-arquitectura.md`.
- [ ] Agregar aquí la guía de entorno específica (SDK, IDE, cómo correr la app en un emulador o dispositivo).
- [x] URL de la API ya definida: `https://gedenaz-api.onrender.com` en producción (para pruebas con el equipo/la empresa), o `http://127.0.0.1:5000`/la IP de tu red local durante desarrollo — ver [docs/specs/06-referencia-api.md](../docs/specs/06-referencia-api.md).

Hasta que esto se defina, el trabajo del equipo se concentra en la API (`src/gedenaz/`), cuyo esquema de datos y contrato HTTP no dependen del framework que se elija para la app.
