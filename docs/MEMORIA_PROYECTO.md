# Memoria del Proyecto — GedeNaz App

> **Qué es este archivo**: una foto del estado actual del proyecto, escrita simple, para que cualquiera (persona o asistente IA) que retome el trabajo entienda rápido de qué se trata y en qué punto vamos, sin tener que leer todo el historial.
>
> **Cómo se mantiene**: este documento se **reescribe/actualiza en el sitio** cada vez que cambia algo importante (no se acumulan versiones viejas acá). El historial detallado de qué se hizo sesión a sesión vive en [`BITACORA.md`](BITACORA.md) — ese sí es un registro cronológico que solo crece.
>
> **Última actualización**: 2026-09-09.

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
- **Hosting gratuito sugerido**: PythonAnywhere (API + MySQL juntos, sin costo, sin tarjeta). Alternativas si hace falta: Aiven, db4free.net. Se evitan PlanetScale/Railway por no ser gratis de forma sostenida.
- **Base de datos**: una sola tabla relevante por ahora, `producto` (ver [`specs/02-modelo-de-datos.md`](specs/02-modelo-de-datos.md)) — el esquema no cambió por el paso a Android.

## Estado actual (2026-09-09)

- ✅ Specs escritas en `docs/specs/` (visión, requisitos, modelo de datos, arquitectura, plan de trabajo, entorno).
- ✅ Repo Git local inicializado, con commit inicial + merge con el repo remoto del equipo. Acceso a GitHub resuelto (Sebastián agregó a `goost01`), todo subido a `https://github.com/sperezm-create/GedeNaz.git` (rama `main`).
- ✅ Entorno de desarrollo del **backend** montado: `venv/` con Python 3.14.5, dependencias instaladas (`Flask`, `mysql-connector-python`, `python-dotenv`, `pytest`), tests de humo pasando.
- ⚠️ **Corrección de alcance**: el equipo definió que la app es **Android**, no de escritorio (el informe entregado hoy decía "escritorio" — ver nota arriba). Se sacó todo el código de Tkinter (`src/gedenaz/ui/`, `main.py` viejo) y se armó en su lugar el esqueleto de una API Flask (`src/gedenaz/api/`, `app.py`) que es lo que la futura app Android va a consumir. Detalle completo en [`BITACORA.md`](BITACORA.md).
- ⏳ **Pendiente y bloqueante para el resto del equipo**: elegir el framework de la app Android (ver `mobile/README.md`).
- ⏳ Nada de código de los endpoints CRUD reales todavía (solo un `/health` de prueba) — eso empieza en la Fase 1 (tarea 1.2 en adelante, ver plan de trabajo).

## Próximos pasos

1. **Decidir el framework de la app Android** (todo el equipo) — ver `mobile/README.md`.
2. Tarea 1.2 (Francisco): instalar MySQL (local o en el hosting gratuito elegido), crear BD `gedenaz` con `src/gedenaz/data/schema.sql`.
3. Tarea 1.3 (Francisco): capa de conexión Python–MySQL dentro de la API.
4. Tarea 1.4 (Sebastian): primera pantalla Android "Crear producto" (depende del punto 1).

Cronograma completo con fechas: [`specs/04-plan-de-trabajo.md`](specs/04-plan-de-trabajo.md).

## Mapa del repo

```
docs/
  MEMORIA_PROYECTO.md   ← este archivo (estado actual, se reescribe)
  BITACORA.md           ← registro cronológico de sesiones (solo crece)
  specs/                ← especificaciones spec-first (00 a 05)
mobile/                  ← app Android (framework pendiente de decisión)
src/gedenaz/             ← backend / API (api / logic / data)
tests/                   ← pruebas pytest
requirements.txt, .env.example, .gitignore, README.md
```
