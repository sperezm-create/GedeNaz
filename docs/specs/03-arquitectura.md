# 03 · Arquitectura y Stack Tecnológico — GedeNaz App

> Basado en la sección 8.3 del informe y en la diapositiva "Metodología y Pila Tecnológica" de la presentación (arquitectura de 3 capas). Decisión de librería GUI (Tkinter estándar) tomada en sesión de trabajo del 2026-09-09.

## Arquitectura

El diagrama siguiente corresponde al cliente de escritorio existente. El cliente Android usa Kivy y accede al mismo dominio a través de `src/gedenaz/api.py`; la tablet no se conecta directamente a MySQL.

```
┌─────────────────────────┐
│   Capa de Usuario        │  Gedalias y Nazareth (administradores) — único tipo de usuario
└────────────┬─────────────┘
             │
┌────────────▼─────────────┐
│ Capa de Presentación y    │  Python + Tkinter (src/gedenaz/ui)
│ Lógica                    │  Python — reglas de negocio, validaciones (src/gedenaz/logic)
└────────────┬─────────────┘
             │  mysql-connector-python
┌────────────▼─────────────┐
│   Capa de Datos           │  MySQL Server (src/gedenaz/data)
└───────────────────────────┘
```

## Stack tecnológico

| Elemento | Elección | Motivo |
|---|---|---|
| Lenguaje | Python (última versión estable) | Definido en informe |
| Interfaz gráfica | **Tkinter** (`tkinter` + `tkinter.ttk`, librería estándar) | Cero dependencias externas, cero costo, currícula del curso; decisión de equipo 2026-09-09 |
| Interfaz Android | **Kivy** | Cliente móvil empaquetable como APK mediante Buildozer |
| API | **FastAPI + Uvicorn** | Expone los casos de uso al cliente Android sin entregar credenciales de la base de datos |
| Base de datos | MySQL Server | Definido en informe |
| Administración BD | MySQL Workbench | Definido en informe |
| Conector Python↔MySQL | `mysql-connector-python` (conector oficial) | "Conector estándar de Python para MySQL" (informe 8.3) |
| IDE | Visual Studio Code | Definido en informe |
| Control de versiones | Git / GitHub | Definido en informe |
| Gestión de tareas | Jira (tablero Kanban: Por hacer / En curso / Terminado) | Definido en informe |
| Pruebas | `pytest` | Estándar de facto en Python, sin costo |
| Config / secretos | Variables de entorno vía `.env` (no versionado) | Evita credenciales de MySQL en el repo |

El usuario y contraseña de la API se configuran mediante `API_ADMIN_USERNAME` y `API_ADMIN_PASSWORD`. La autenticación HTTP Basic debe transportarse por HTTPS en cualquier despliegue no local.

Presupuesto de herramientas: **$0** (todo open source o de licencia gratuita).

## Estructura del repositorio

```
Proyecto/
├── docs/
│   └── specs/                  # Especificaciones (spec-first) — este directorio
├── src/
│   └── gedenaz/
│       ├── __init__.py
│       ├── main.py             # Punto de entrada de la app de escritorio
│       ├── api.py              # API para clientes remotos
│       ├── config.py           # Carga de configuración/.env
│       ├── ui/                 # Pantallas Tkinter (crear, listar, actualizar, eliminar)
│       ├── logic/              # Reglas de negocio y validaciones (independiente de la UI)
│       └── data/               # Acceso a datos MySQL (repositorio de Producto) + schema.sql
├── mobile/                     # Cliente Kivy y configuración Buildozer
├── tests/                      # Pruebas con pytest
├── .env.example                # Plantilla de variables de entorno (sin credenciales reales)
├── .gitignore
├── requirements.txt
├── README.md
└── venv/                       # Entorno virtual local (no versionado)
```

## Principio de separación de capas

- `ui/` **no** contiene lógica de negocio ni SQL: solo arma la interfaz y llama a `logic/`.
- `logic/` contiene las validaciones de [01-requisitos-funcionales.md](01-requisitos-funcionales.md) (campos obligatorios, tipos de dato, stock no negativo, etc.) y orquesta llamadas a `data/`. No importa nada de `tkinter`.
- `data/` es la única capa que habla con MySQL (usa `mysql-connector-python`); expone repositorios que reflejan el esquema de [02-modelo-de-datos.md](02-modelo-de-datos.md).
- `api.py` valida las solicitudes HTTP y orquesta los servicios existentes. `mobile/` contiene el cliente Kivy y no incluye credenciales de MySQL.

Esta separación permite, si más adelante se requiere, cambiar la librería de UI sin tocar la lógica de negocio ni el acceso a datos.
