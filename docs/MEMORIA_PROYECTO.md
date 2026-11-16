# Memoria del Proyecto — GedeNaz App

> **Qué es este archivo**: una foto del estado actual del proyecto, escrita simple, para que cualquiera (persona o asistente IA) que retome el trabajo entienda rápido de qué se trata y en qué punto vamos, sin tener que leer todo el historial.
>
> **Cómo se mantiene**: este documento se **reescribe/actualiza en el sitio** cada vez que cambia algo importante (no se acumulan versiones viejas acá). El historial detallado de qué se hizo sesión a sesión vive en [`BITACORA.md`](BITACORA.md) — ese sí es un registro cronológico que solo crece.
>
> **Última actualización**: 2026-10-22.

## En una frase

GedeNaz App es una app de escritorio en Python + MySQL para que Gedalias y Nazareth gestionen inventario, registren ventas con boletas internas y consulten los productos más vendidos.

## El equipo (curso Taller Sistemas de Información, Grupo 6)

| Quién | Rol |
|---|---|
| Francisco Jara | Jefe de proyecto + Backend/Base de datos |
| Sebastian Perez | Interfaz de usuario (dueño del repo GitHub) |
| Cristóbal Sierra Porras | Documentación de informes |
| **Nicolas Silva** (`goost01` en GitHub, es con quien trabajo yo) | Interfaz de usuario + apoyo en pruebas |

## Funciones del sistema (alcance)

- **RF1 Crear**: registrar producto nuevo (nombre, categoría, precio, stock inicial).
- **RF2 Leer**: listar, buscar/filtrar por nombre o categoría, ver detalle.
- **RF3 Actualizar**: editar datos y ajustar stock (nunca negativo).
- **RF4 Eliminar**: dar de baja un producto, con confirmación antes de borrar.
- **RF5 Ventas**: vender productos del inventario por código, registrar la boleta interna y descontar stock.
- **RF6 Estadísticas**: consultar unidades vendidas por producto, ordenadas por demanda.
- Pagos, ventas online y documentos tributarios electrónicos quedan fuera del alcance.

Detalle completo con criterios de aceptación: [`specs/01-requisitos-funcionales.md`](specs/01-requisitos-funcionales.md).

## Cómo está armado (decisiones ya tomadas)

- **Interfaz gráfica**: Tkinter estándar (viene con Python, sin instalar nada extra). Decidido en equipo el 2026-09-09.
- **Arquitectura**: 3 capas — `ui/` (pantallas Tkinter) → `logic/` (reglas de negocio/validaciones) → `data/` (acceso a MySQL). `ui/` no habla directo con la base de datos.
- **Base de datos**: tablas `producto`, `venta` y `detalle_venta` (ver [`specs/02-modelo-de-datos.md`](specs/02-modelo-de-datos.md)).
- Todo el detalle de "por qué" está en [`specs/03-arquitectura.md`](specs/03-arquitectura.md).

## Estado actual (2026-10-22)

- ✅ Specs escritas en `docs/specs/` (visión, requisitos, modelo de datos, arquitectura, plan de trabajo, entorno).
- ✅ Repo Git local inicializado, con commit inicial + merge con el repo remoto del equipo.
- ✅ Entorno de desarrollo montado con Python, `mysql-connector-python`, `python-dotenv` y `pytest`.
- ✅ Implementadas las pantallas de inventario y ventas, registro de boletas internas, descuento de stock y estadísticas.
- ✅ Pruebas automatizadas: 21 pasan; una prueba de interfaz se omite cuando Tkinter no está disponible en el entorno de pruebas.
- ✅ Acceso a GitHub resuelto: Sebastián agregó a `goost01` como colaborador. Push hecho — todo lo anterior ya está en `https://github.com/sperezm-create/GedeNaz.git` (rama `main`), visible para el equipo.
La app requiere configurar MySQL en `.env` y ejecutar `src/gedenaz/data/schema.sql`; en bases existentes se deben crear las tablas nuevas de venta como se indica en el README.

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
