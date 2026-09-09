# GedeNaz App — Cliente Android

Este directorio va a contener la app Android que consume la API en `src/gedenaz/` (ver [docs/specs/03-arquitectura.md](../docs/specs/03-arquitectura.md)).

## Pendiente

- [ ] Elegir el framework: Kotlin nativo (Android Studio), Flutter (Dart) o Python (Kivy/BeeWare). Ver la comparación en la bitácora del proyecto (2026-09-09).
- [ ] Documentar la decisión y el porqué en `docs/specs/03-arquitectura.md`.
- [ ] Agregar aquí la guía de entorno específica (SDK, IDE, cómo correr la app en un emulador o dispositivo).
- [ ] Definir cómo la app apunta a la API: URL local (`http://127.0.0.1:5000` o la IP de la red local) durante desarrollo, URL del hosting gratuito para pruebas con el equipo/la empresa.

Hasta que esto se defina, el trabajo del equipo se concentra en la API (`src/gedenaz/`), cuyo esquema de datos y contrato HTTP no dependen del framework que se elija para la app.
