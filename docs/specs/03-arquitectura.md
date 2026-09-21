# 03 · Arquitectura y Stack Tecnológico — GedeNaz App

> **Corrección (2026-09-09)**: GedeNaz App es una **app Android**, no una app de escritorio. Este documento reemplaza la arquitectura de 3 capas locales (Tkinter en el mismo proceso) por una arquitectura cliente-servidor. Ver [00-vision-y-alcance.md](00-vision-y-alcance.md) y [BITACORA.md](../BITACORA.md) para el porqué del cambio.
>
> **Decisión pendiente**: el framework de la app Android (Kotlin nativo / Flutter / Python+Kivy, etc.) todavía no está definido por el equipo. Este documento cubre lo que **sí** está decidido: se mantiene MySQL, y por seguridad la app no lo toca directo, sino a través de una API. Esa API es lo único que este repositorio implementa por ahora.

## Por qué una API en el medio (y no la app conectada directo a MySQL)

Una app Android no debe guardar credenciales de base de datos: cualquiera puede descompilar un APK y sacarlas, y además el puerto de MySQL tendría que quedar abierto a internet. La forma estándar y segura de "usar MySQL desde una app móvil" es meter una API entre medio:

```
┌──────────────────────┐
│   App Android         │  Gedalias y Nazareth (administradores) — cliente,
│   (framework a definir)│  fuera de este repositorio por ahora
└──────────┬─────────────┘
           │  HTTP/REST (JSON) — único canal permitido
┌──────────▼─────────────┐
│   API (backend)         │  Python + Flask — src/gedenaz/api/
│   + Lógica de negocio    │  Python — src/gedenaz/logic/
└──────────┬─────────────┘
           │  mysql-connector-python (solo la API tiene credenciales)
┌──────────▼─────────────┐
│   Base de datos          │  MySQL Server — src/gedenaz/data/
└──────────────────────────┘
```

La app nunca ve una contraseña de MySQL; solo llama endpoints HTTP (`GET /productos`, `POST /productos`, etc.) y la API es la única con acceso a la base.

## Stack tecnológico

| Elemento | Elección | Motivo |
|---|---|---|
| App móvil | **Android** — framework por definir | Decisión de equipo 2026-09-09 (corrige "escritorio" del informe) |
| Backend / API | **Python + Flask** | Mantiene "Python" del informe; Flask es simple, liviano y tiene mejor soporte gratuito (ver hosting) que alternativas ASGI |
| Base de datos | MySQL Server | Definido en informe, confirmado por el equipo tras evaluar alternativas (2026-09-09) |
| Administración BD | MySQL Workbench | Definido en informe |
| Conector Python↔MySQL | `mysql-connector-python` (conector oficial) | Solo lo usa la API, nunca la app |
| Hosting de MySQL | **Aiven** (plan Free: 1GB, sin tarjeta) | PythonAnywhere se descartó (2026-09-16): desde enero 2026 MySQL solo está en sus planes pagos, y sus cuentas gratuitas ni siquiera pueden conectarse a una base externa. Ver bitácora. |
| Hosting del backend (Flask) | **Render** (free tier: 750h/mes, sin tarjeta) — ✅ desplegado: `https://gedenaz-api.onrender.com` (ver [05-entorno-desarrollo.md § 9](05-entorno-desarrollo.md)) | Se descartó Render solo-Postgres como base de datos, pero sí sirve para alojar el Flask conectado a Aiven por fuera. Desplegado vía "Public Git Repository" (no vía GitHub conectado, ver spec de entorno) — **sin auto-deploy**, cada push a producción necesita "Manual Deploy" |
| Servidor WSGI (producción) | `gunicorn` | El dev server de Flask (`app.run()`) no es apto para producción; Render lo corre con `gunicorn "gedenaz.app:create_app()"` |
| IDE (backend) | Visual Studio Code | Definido en informe |
| IDE (app Android) | Por definir junto con el framework | Android Studio si es Kotlin nativo; distinto si es Flutter/Kivy |
| Control de versiones | Git / GitHub | Definido en informe |
| Gestión de tareas | Jira (Kanban) | Definido en informe |
| Pruebas (backend) | `pytest` | Sin costo, estándar en Python |
| Config / secretos | Variables de entorno vía `.env` (no versionado) | Evita credenciales de MySQL en el repo |

Presupuesto de herramientas: **$0**, confirmado tras revisar alternativas de hosting con costo asociado (PlanetScale, Railway) — se descartaron por no ser gratis de forma sostenida.

## Estructura del repositorio

```
Proyecto/
├── docs/
│   └── specs/                  # Especificaciones (spec-first) — este directorio
├── mobile/                     # App Android — framework pendiente de decisión del equipo
│   └── README.md               # Placeholder: qué falta decidir antes de empezar acá
├── scripts/                    # Utilidades de desarrollo (ej. apply_schema.py)
├── src/
│   └── gedenaz/                # Backend (API) — lo único que este repo implementa hoy
│       ├── __init__.py
│       ├── main.py             # Punto de entrada del backend (arranca la API Flask)
│       ├── app.py              # Fábrica de la app Flask (create_app)
│       ├── config.py           # Carga de configuración/.env
│       ├── api/                # Endpoints HTTP (Flask): productos.py, ventas.py, reportes.py, respuestas.py (sobre de error)
│       ├── logic/               # Reglas de negocio y validaciones (independiente de Flask): productos, ventas, reportes, filtros, errores
│       └── data/                 # Acceso a datos MySQL: db.py, productos.py, ventas.py, reportes.py + schema.sql / schema_cloud.sql
├── tests/                      # Pruebas con pytest, en espejo de src/gedenaz
├── .env.example                # Plantilla de variables de entorno (sin credenciales reales)
├── .gitignore
├── pyproject.toml              # Declara el paquete gedenaz para poder instalarlo con `pip install -e .`
├── requirements.txt
├── README.md
└── venv/                       # Entorno virtual local (no versionado)
```

## Principio de separación de capas

- `api/` solo traduce HTTP↔Python: recibe la request, llama a `logic/`, devuelve JSON. No contiene SQL ni reglas de negocio.
- `logic/` contiene las validaciones de [01-requisitos-funcionales.md](01-requisitos-funcionales.md) (campos obligatorios, tipos de dato, stock no negativo, etc.) y orquesta llamadas a `data/`. No importa nada de `flask` — se puede probar con `pytest` sin levantar un servidor HTTP.
- `data/` es la única capa que habla con MySQL (usa `mysql-connector-python`); expone funciones tipo repositorio (`crear_producto`, `listar_productos`, `obtener_producto`, `actualizar_producto`, `actualizar_producto_parcial`, `eliminar_producto`) que reflejan el esquema de [02-modelo-de-datos.md](02-modelo-de-datos.md). **Estado** (2026-09-16): ✅ **CRUD completo implementado** (`data/db.py` + `data/productos.py`) y probado contra Aiven en producción (RF1-RF4). `listar_productos`/`obtener_producto` filtran siempre por `activo = 1`; `eliminar_producto` es baja lógica (`UPDATE activo = 0`, nunca `DELETE`).
  - **Ventas y reportes** (2026-09-20, RF5 y RF3.1): `data/ventas.py` (`registrar_venta`, `obtener_venta`, `listar_ventas`) y `data/reportes.py` (`productos_mas_vendidos`). `registrar_venta` es **una sola transacción** con `SELECT ... FOR UPDATE` sobre los productos (en orden de `id`), y lanza excepciones propias de la capa de datos (`ProductoNoDisponibleError`, `StockInsuficienteError`) que `logic/ventas.py` traduce a `ValidationError` (400) / `ConflictError` (409) — `data/` nunca importa de `logic/`. Las excepciones de negocio compartidas viven en `logic/errores.py`.
  - **Zona horaria**: `data/db.py` abre cada conexión con la sesión en hora de Chile (`DB_TIMEZONE`, por defecto `America/Santiago`). Se pasa a MySQL como **desfase numérico** (`-03:00`), calculado con `zoneinfo` en cada conexión (respeta el horario de verano), y no como nombre de zona: un nombre exige que el servidor tenga cargadas las tablas de zonas horarias, cosa que un MySQL local en Windows normalmente no tiene. Por eso `tzdata` está en `requirements.txt` (Windows no trae base de zonas horarias).
  - **Detalle importante de MySQL**: ninguna función usa `cursor.rowcount` para decidir "el producto no existe" — por defecto, MySQL reporta filas *cambiadas*, no filas que matchearon el `WHERE` (si mandas el mismo valor que ya había, `rowcount` da 0 aunque el producto exista). `actualizar_producto`/`actualizar_producto_parcial` confirman la existencia con un `SELECT` aparte después del `UPDATE`, nunca con `rowcount`. (Bug real encontrado y corregido el 2026-09-16 — ver bitácora.)

> Los archivos `schema.sql` y `schema_cloud.sql` tienen las mismas tres tablas (`producto`, `venta`, `detalle_venta`) y hay que **mantenerlos sincronizados**. `schema_cloud.sql` es idempotente: se puede re-ejecutar (`python scripts/apply_schema.py src/gedenaz/data/schema_cloud.sql`) para sumar tablas nuevas a una base que ya existe.

Esta separación es la misma que ya existía en la versión de escritorio, solo que `ui/` (Tkinter) se reemplazó por `api/` (Flask) — `logic/` y `data/` no cambiaron de lugar ni de responsabilidad.
