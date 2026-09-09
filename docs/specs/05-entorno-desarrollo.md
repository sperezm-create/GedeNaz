# 05 · Entorno de Desarrollo — GedeNaz App

> Cubre la tarea **1.1 — "Configurar entorno de desarrollo"** de la Carta Gantt (responsable: Nicolas Silva). Esta guía monta el entorno del **backend (API Python + MySQL)** — ver [03-arquitectura.md](03-arquitectura.md). El entorno de la **app Android** se documenta aparte en `mobile/README.md` en cuanto el equipo defina el framework.

## Requisitos previos

- **Python 3.11+** instalado (usado en esta configuración: 3.14.5). Verificar con `python --version`.
- **VS Code** instalado, con la extensión oficial "Python" (Microsoft).
- **Git** instalado y configurado (`git config --global user.name/user.email`).
- **MySQL Server** y **MySQL Workbench** (se instalan en la tarea 1.2, a cargo de Francisco Jara — no bloquea esta tarea). En producción, MySQL puede vivir en un proveedor gratuito (PythonAnywhere, Aiven) en vez de instalarse localmente — ver [03-arquitectura.md](03-arquitectura.md).

## 1. Ubicarse en el repositorio

```bash
cd "Proyecto"
```

## 2. Crear y activar el entorno virtual

Windows (PowerShell):

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

macOS / Linux (bash):

```bash
python3 -m venv venv
source venv/bin/activate
```

> El entorno virtual **no se versiona** (está en `.gitignore`). Cada integrante lo crea localmente con estos mismos comandos.

## 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

Dependencias del proyecto ([03-arquitectura.md](03-arquitectura.md)):

| Paquete | Uso |
|---|---|
| `Flask` | Framework de la API que consume la app Android |
| `mysql-connector-python` | Conector oficial Python↔MySQL (capa `data/`), usado solo por la API |
| `python-dotenv` | Carga de variables de entorno desde `.env` |
| `pytest` | Pruebas funcionales del backend (RF1–RF4) |

## 4. Configurar variables de entorno

```bash
cp .env.example .env      # Windows: copy .env.example .env
```

Completar `.env` con las credenciales locales de MySQL (host, usuario, contraseña, nombre de base de datos). **Nunca** commitear `.env` (ya está en `.gitignore`).

## 5. Configurar VS Code

1. Abrir la carpeta del repositorio en VS Code.
2. `Ctrl+Shift+P` → "Python: Select Interpreter" → elegir el intérprete de `venv/` (`venv\Scripts\python.exe` en Windows).
3. Confirmar que la barra inferior de VS Code muestra el intérprete de `venv`.

## 6. Verificar la instalación

```bash
python -c "import flask, mysql.connector, dotenv, pytest; print('entorno OK')"
pytest --version
```

## 7. Correr la API localmente

```bash
python src/gedenaz/main.py
```

Debería levantar un servidor Flask local (por defecto en `http://127.0.0.1:5000`). Probar con:

```bash
curl http://127.0.0.1:5000/health
```

## Entorno del cliente móvil (Android) — pendiente

El equipo confirmó que la app es para Android pero **todavía no eligió el framework** (Kotlin nativo, Flutter, Python+Kivy, etc.). Cuando se decida:

1. Documentar la elección y el porqué en `03-arquitectura.md`.
2. Agregar una guía de entorno específica en `mobile/README.md` (Android Studio / Flutter SDK / lo que corresponda).
3. Definir cómo la app apunta a la API (URL local para desarrollo vs. URL del hosting gratuito para pruebas con el equipo/la empresa).

## Convenciones del repositorio

- Código del backend en `src/gedenaz/` (ver estructura en [03-arquitectura.md](03-arquitectura.md)).
- Pruebas en `tests/`, en espejo de `src/gedenaz/` (ej. `tests/logic/test_productos.py`).
- Specs en `docs/specs/` — **se actualizan antes** de implementar un cambio de alcance o de modelo de datos (spec-first).
- Commits en español, descriptivos, referenciando el RF o la tarea de la Carta Gantt cuando aplique (ej. `RF1: agrega validación de stock no negativo`).
- Nomenclatura de código en `snake_case` para variables/funciones y `PascalCase` para clases, siguiendo PEP 8 (mencionado en informe 8.3: "convenciones estándar de nomenclatura y organización de código").
