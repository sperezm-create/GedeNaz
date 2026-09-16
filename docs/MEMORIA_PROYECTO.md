# Memoria del Proyecto — GedeNaz App

> **Qué es este archivo**: una foto del estado actual del proyecto, escrita simple, para que cualquiera (persona o asistente IA) que retome el trabajo entienda rápido de qué se trata y en qué punto vamos, sin tener que leer todo el historial.
>
> **Cómo se mantiene**: este documento se **reescribe/actualiza en el sitio** cada vez que cambia algo importante (no se acumulan versiones viejas acá). El historial detallado de qué se hizo sesión a sesión vive en [`BITACORA.md`](BITACORA.md) — ese sí es un registro cronológico que solo crece.
>
> **Última actualización**: 2026-09-16.

## En una frase

GedeNaz App es una app **Android** (backend en Python + MySQL) para que Gedalias y Nazareth (dueños de una joyería) manejen su inventario (crear, ver, editar, eliminar productos) desde sus teléfonos, viendo siempre el mismo stock, sin cuadernos ni planillas sueltas.

> ⚠️ El informe entregado el 2026-09-09 dice "aplicación de escritorio" — eso quedó corregido el mismo día, antes de empezar a programar nada más allá del entorno base. Ver "Estado actual" abajo.

## El equipo (curso Taller Sistemas de Información, Grupo 6)

| Quién | Rol |
|---|---|
| Francisco Jara | Jefe de proyecto + Backend/Base de datos |
| Sebastian Perez | Interfaz de usuario (dueño del repo GitHub) |
| Cristóbal Sierra Porras | Documentación de informes |
| **Nicolas Silva** (`goost01` en GitHub, es con quien trabajo yo) | Interfaz de usuario + apoyo en pruebas |

## Las 4 funciones del sistema (alcance)

- **RF1 Crear**: registrar producto nuevo (nombre, categoría, precio, stock inicial).
- **RF2 Leer**: listar, buscar/filtrar por nombre o categoría, ver detalle.
- **RF3 Actualizar**: editar datos y ajustar stock (nunca negativo).
- **RF4 Eliminar**: dar de baja un producto, con confirmación antes de borrar.
- Todo lo demás (venta online, pagos, reportes de ventas) queda **fuera de alcance** por ahora.

Detalle completo con criterios de aceptación: [`specs/01-requisitos-funcionales.md`](specs/01-requisitos-funcionales.md).

## Cómo está armado (decisiones ya tomadas)

- **Cliente**: app Android. **Framework todavía sin decidir** (Kotlin / Flutter / Python+Kivy) — el equipo lo está conversando.
- **Datos**: se mantiene **MySQL** (el equipo lo confirmó tras evaluar alternativas locales/SQLite), pero la app **nunca** se conecta directo a la base — no es seguro guardar credenciales de MySQL dentro de un APK.
- **Arquitectura**: por eso hay una API en el medio — `App Android → API (Flask) → MySQL`. Dentro de la API: `api/` (endpoints HTTP) → `logic/` (reglas de negocio/validaciones) → `data/` (acceso a MySQL). Ver [`specs/03-arquitectura.md`](specs/03-arquitectura.md) para el detalle y el porqué.
- **Hosting**: **Aiven** para MySQL + **Render** para el backend Flask (decisión confirmada 2026-09-16, corrigiendo a PythonAnywhere del mismo día — ver nota abajo). Ambos gratis, sin tarjeta. Se descartaron PythonAnywhere (MySQL pasó a ser de pago desde enero 2026, y sus cuentas gratis ni siquiera pueden conectarse a una base externa), PlanetScale y Railway (no son gratis de forma sostenida). Guía paso a paso para montar la base en Aiven: [`specs/05-entorno-desarrollo.md`](specs/05-entorno-desarrollo.md#8-desplegar-la-base-de-datos-en-aiven).
- **Base de datos**: una sola tabla relevante por ahora, `producto` (ver [`specs/02-modelo-de-datos.md`](specs/02-modelo-de-datos.md)) — el esquema no cambió por el paso a Android.

## Estado actual (2026-09-16)

- ✅ Specs escritas en `docs/specs/` (visión, requisitos, modelo de datos, arquitectura, plan de trabajo, entorno).
- ✅ Repo Git local inicializado, con commit inicial + merge con el repo remoto del equipo. Acceso a GitHub resuelto (Sebastián agregó a `goost01`), todo subido a `https://github.com/sperezm-create/GedeNaz.git` (rama `main`).
- ✅ Entorno de desarrollo del **backend** montado: `venv/` con Python 3.14.5, dependencias instaladas (`Flask`, `mysql-connector-python`, `python-dotenv`, `pytest`), tests de humo pasando.
- ⚠️ **Corrección de alcance**: el equipo definió que la app es **Android**, no de escritorio (el informe entregado hoy decía "escritorio" — ver nota arriba). Se sacó todo el código de Tkinter (`src/gedenaz/ui/`, `main.py` viejo) y se armó en su lugar el esqueleto de una API Flask (`src/gedenaz/api/`, `app.py`) que es lo que la futura app Android va a consumir. Detalle completo en [`BITACORA.md`](BITACORA.md).
- ⚠️ **Corrección de hosting (mismo día)**: se había documentado y recomendado PythonAnywhere, pero al intentar usarlo se confirmó que MySQL pasó a ser de pago ahí desde enero de 2026 (y sus cuentas gratis no pueden conectarse a bases externas tampoco). Se reemplazó por **Aiven** (MySQL) + **Render** (backend), verificado por web. Detalle en [`BITACORA.md`](BITACORA.md).
- ✅ Se dejó la guía paso a paso para Aiven y el esquema adaptado (`src/gedenaz/data/schema_cloud.sql`) listos para ejecutar. `config.py` ya soporta SSL (`DB_SSL_CA`), que Aiven exige.
- ⏳ **Pendiente y bloqueante para el resto del equipo**: elegir el framework de la app Android (ver `mobile/README.md`).
- ✅ **Base de datos en la nube lista**: servicio `mysql-gedenaz-bd` creado en Aiven, tabla `producto` aplicada y verificada (con `scripts/apply_schema.py`, útil porque MySQL Workbench se cuelga contra bases remotas — bug conocido). El `.env` de Nicolas ya está completo y probado end-to-end contra Aiven.
- ✅ **Tarea 1.3 avanzada**: capa de conexión Python–MySQL (`src/gedenaz/data/db.py`) + endpoint `GET /health/db`. Se encontró y arregló un bug real (`pyproject.toml` + `pip install -e .`, sin eso `python src/gedenaz/main.py` no corre).
- ✅ **CRUD completo en el backend, en producción** (RF1-RF4): `POST/GET/PUT/DELETE /productos` — crear, listar/filtrar/detalle, actualizar y eliminar (baja lógica). Probado con `pytest` (30 tests) y manualmente con `curl`, de punta a punta contra Aiven y contra `https://gedenaz-api.onrender.com`. Ver [`BITACORA.md`](BITACORA.md) para el detalle de las 3 capas.
- ✅ **Backend desplegado y funcionando en Render**: `https://gedenaz-api.onrender.com` — `/health`, `/health/db` y `POST /productos` probados en producción, responden bien. Como el repo no es de Nicolas (es de Sebastian) y es público, se usó "Public Git Repository" en vez de conectar GitHub (sin auto-deploy: hay que apretar "Manual Deploy" en Render después de cada push que quieran llevar a producción).
- ✅ **Documentación de la API lista**: [`specs/06-referencia-api.md`](specs/06-referencia-api.md) — contrato HTTP completo, verificado contra el servidor real. Se unificó el formato de errores (antes inconsistente entre `400` y `404`) antes de que alguien escribiera código Android dependiendo de la forma vieja.
- ✅ **`PATCH /productos/<id>`** agregado para actualizar un solo campo (ej. stock) sin reenviar todo el producto (`PUT` se mantiene para reemplazo completo). De paso se encontró y corrigió un **bug real ya en producción**: actualizar un producto con los mismos valores que ya tenía hacía que la API devolviera un `404` falso (por cómo MySQL cuenta filas "cambiadas" vs. "encontradas"). 41 tests en verde. Ver [`BITACORA.md`](BITACORA.md) para el detalle técnico.
- ✅ Base sembrada con 6 productos de prueba (2 anillos, 2 collares, 1 pulsera, 1 aro) en `https://gedenaz-api.onrender.com`.
- ⏳ El backend está funcionalmente completo. Lo único que falta para tener el sistema completo es la **app Android** (bloqueada por la decisión de framework). **Pendiente**: hacer "Manual Deploy" en Render para que el cambio de formato de errores llegue a producción.

## Próximos pasos

1. **Decidir el framework de la app Android** (todo el equipo) — ver `mobile/README.md`. Es el único bloqueante real que queda: el backend (RF1-RF4) ya está completo y en producción, esperando a que exista una app que lo consuma.
2. Avisarle al equipo (Francisco, Sebastian, Cristóbal) que las tareas 1.3, 1.5, 1.6 y todo el resto del CRUD (Fases 2 y 3 del plan) ya quedaron avanzadas y desplegadas — revisar `src/gedenaz/{data,logic,api}/` antes de seguir, para no duplicar trabajo.
3. Presentarle al equipo la propuesta de registro de ventas ([`propuestas/registro-de-ventas.md`](propuestas/registro-de-ventas.md)) si quieren discutirla.
4. **Recordatorio permanente**: el deploy en Render no es automático (repo público, sin conexión a GitHub) — después de cada push a `main` que quieran llevar a producción, hay que entrar al panel de Render y apretar "Manual Deploy".

Cronograma completo con fechas: [`specs/04-plan-de-trabajo.md`](specs/04-plan-de-trabajo.md).

## Mapa del repo

```
docs/
  MEMORIA_PROYECTO.md   ← este archivo (estado actual, se reescribe)
  BITACORA.md           ← registro cronológico de sesiones (solo crece)
  specs/                ← especificaciones spec-first (00 a 06)
  propuestas/            ← ideas discutidas pero no decididas (ej. registro de ventas)
mobile/                  ← app Android (framework pendiente de decisión)
scripts/                 ← utilidades (ej. apply_schema.py — correr un .sql contra la base del .env)
src/gedenaz/             ← backend / API (api / logic / data)
tests/                   ← pruebas pytest
requirements.txt, .env.example, .gitignore, README.md
```
