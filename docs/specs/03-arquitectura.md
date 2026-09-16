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
| Hosting del backend (Flask) | **Render** (free tier: 750h/mes, sin tarjeta) — pendiente de desplegar | Se descartó Render solo-Postgres como base de datos, pero sí sirve para alojar el Flask conectado a Aiven por fuera |
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
│       ├── api/                # Endpoints HTTP (Flask) — reemplaza lo que antes era ui/
│       ├── logic/               # Reglas de negocio y validaciones (independiente de Flask)
│       └── data/                 # Acceso a datos MySQL (repositorio de Producto) + schema.sql
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
- `data/` es la única capa que habla con MySQL (usa `mysql-connector-python`); expone funciones tipo repositorio (`crear_producto`, `listar_productos`, `actualizar_producto`, `eliminar_producto`) que reflejan el esquema de [02-modelo-de-datos.md](02-modelo-de-datos.md). **Estado** (2026-09-16): `data/db.py` (conexión, con SSL para Aiven) y `data/productos.py::crear_producto` ya implementados y probados contra Aiven (RF1). `listar_productos`, `actualizar_producto`, `eliminar_producto` quedan para RF2-RF4 (tareas 2.2, 3.1, 3.4).

Esta separación es la misma que ya existía en la versión de escritorio, solo que `ui/` (Tkinter) se reemplazó por `api/` (Flask) — `logic/` y `data/` no cambiaron de lugar ni de responsabilidad.
