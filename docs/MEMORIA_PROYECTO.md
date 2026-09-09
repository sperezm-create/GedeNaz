# Memoria del Proyecto — GedeNaz App

> **Qué es este archivo**: una foto del estado actual del proyecto, escrita simple, para que cualquiera (persona o asistente IA) que retome el trabajo entienda rápido de qué se trata y en qué punto vamos, sin tener que leer todo el historial.
>
> **Cómo se mantiene**: este documento se **reescribe/actualiza en el sitio** cada vez que cambia algo importante (no se acumulan versiones viejas acá). El historial detallado de qué se hizo sesión a sesión vive en [`BITACORA.md`](BITACORA.md) — ese sí es un registro cronológico que solo crece.
>
> **Última actualización**: 2026-09-09.

## En una frase

GedeNaz App es una app de escritorio en Python + MySQL para que Gedalias y Nazareth (dueños de una joyería) manejen su inventario (crear, ver, editar, eliminar productos) sin cuadernos ni planillas sueltas.

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

- **Interfaz gráfica**: Tkinter estándar (viene con Python, sin instalar nada extra). Decidido en equipo el 2026-09-09.
- **Arquitectura**: 3 capas — `ui/` (pantallas Tkinter) → `logic/` (reglas de negocio/validaciones) → `data/` (acceso a MySQL). `ui/` no habla directo con la base de datos.
- **Base de datos**: una sola tabla relevante por ahora, `producto` (ver [`specs/02-modelo-de-datos.md`](specs/02-modelo-de-datos.md)).
- Todo el detalle de "por qué" está en [`specs/03-arquitectura.md`](specs/03-arquitectura.md).

## Estado actual (2026-09-09)

- ✅ Specs escritas en `docs/specs/` (visión, requisitos, modelo de datos, arquitectura, plan de trabajo, entorno).
- ✅ Repo Git local inicializado, con commit inicial + merge con el repo remoto del equipo.
- ✅ Entorno de desarrollo montado: `venv/` con Python 3.14.5, dependencias instaladas (`mysql-connector-python`, `python-dotenv`, `pytest`), tests de humo pasando, ventana Tkinter probada y funcionando.
- ⏳ **Bloqueado**: el push a `https://github.com/sperezm-create/GedeNaz.git` falló con 403 — el usuario de GitHub `goost01` (Nicolas) todavía no tiene permiso de escritura en el repo. Nicolas ya pidió acceso a Sebastián (dueño del repo). El commit está listo en local (`git push -u origin main`) para cuando llegue el acceso.
- ⏳ Nada de código de las pantallas CRUD todavía — eso empieza en la Fase 1 (tarea 1.2 en adelante, ver plan de trabajo). Lo que existe en `src/gedenaz/` es solo el esqueleto + una ventana placeholder que confirma que el entorno funciona.

## Próximos pasos

1. Confirmar acceso de Nicolas al repo GitHub y hacer `git push`.
2. Tarea 1.2 (Francisco): instalar MySQL, crear BD `gedenaz` con `src/gedenaz/data/schema.sql`.
3. Tarea 1.3 (Francisco): capa de conexión Python–MySQL.
4. Tarea 1.4 (Sebastian): pantalla "Crear producto".

Cronograma completo con fechas: [`specs/04-plan-de-trabajo.md`](specs/04-plan-de-trabajo.md).

## Mapa del repo

```
docs/
  MEMORIA_PROYECTO.md   ← este archivo (estado actual, se reescribe)
  BITACORA.md           ← registro cronológico de sesiones (solo crece)
  specs/                ← especificaciones spec-first (00 a 05)
src/gedenaz/             ← código de la app (ui / logic / data)
tests/                   ← pruebas pytest
requirements.txt, .env.example, .gitignore, README.md
```
