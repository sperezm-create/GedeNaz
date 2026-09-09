# GedeNaz App

Aplicación **Android** (framework por definir) + backend API en **Python** con **MySQL**, para la gestión de inventario de joyas de la empresa GedeNaz. Proyecto del curso Taller de Sistemas de Información (INFB8082), Grupo N°6.

Este repositorio, por ahora, implementa el **backend**: la app Android en sí vive en [`mobile/`](mobile/) a la espera de que el equipo defina su framework.

## Memoria y bitácora

- [`docs/MEMORIA_PROYECTO.md`](docs/MEMORIA_PROYECTO.md) — foto del estado actual del proyecto (léelo primero si vuelves después de un tiempo).
- [`docs/BITACORA.md`](docs/BITACORA.md) — registro cronológico de qué se hizo en cada sesión de trabajo.

## Especificaciones (spec-first)

Este proyecto se desarrolla en modalidad **spec-first**: antes de programar un cambio de alcance, requisito o modelo de datos, se actualiza el documento correspondiente en [`docs/specs/`](docs/specs/):

1. [00-vision-y-alcance.md](docs/specs/00-vision-y-alcance.md) — resumen, problema, objetivos, alcance.
2. [01-requisitos-funcionales.md](docs/specs/01-requisitos-funcionales.md) — RF1–RF4 con criterios de aceptación.
3. [02-modelo-de-datos.md](docs/specs/02-modelo-de-datos.md) — entidad Producto y esquema MySQL.
4. [03-arquitectura.md](docs/specs/03-arquitectura.md) — arquitectura cliente-servidor (app Android → API → MySQL) y stack tecnológico.
5. [04-plan-de-trabajo.md](docs/specs/04-plan-de-trabajo.md) — fases, hitos y roles (Carta Gantt).
6. [05-entorno-desarrollo.md](docs/specs/05-entorno-desarrollo.md) — cómo levantar el entorno de desarrollo.

## Quickstart

```bash
python -m venv venv
# Windows: .\venv\Scripts\Activate.ps1   |   macOS/Linux: source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # y completar credenciales de MySQL
pytest
python src/gedenaz/main.py   # levanta la API Flask en http://127.0.0.1:5000
```

Detalle completo en [05-entorno-desarrollo.md](docs/specs/05-entorno-desarrollo.md). Para la app Android, ver [`mobile/README.md`](mobile/README.md) (framework aún por definir).

## Stack

Android (framework por definir) · Python 3.11+ · Flask · MySQL · `mysql-connector-python` · pytest · VS Code · Git/GitHub · Jira (Kanban).

## Equipo

Sebastián Pérez · Francisco Jara (jefe de proyecto) · Cristóbal Sierra Porras · Nicolas Silva.
