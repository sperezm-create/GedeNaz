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

## 8. Desplegar la base de datos en PythonAnywhere

> Decisión de equipo (2026-09-16): hosting gratuito para MySQL + backend, ver [03-arquitectura.md](03-arquitectura.md). Esta sección la ejecuta cada quien con **su propia cuenta** (no se comparte una sola cuenta de PythonAnywhere entre el equipo, salvo que decidan lo contrario) — son pasos manuales en su web, no se pueden automatizar desde acá.

1. Crear una cuenta gratuita en [pythonanywhere.com](https://www.pythonanywhere.com) — plan **"Beginner"** (gratis, sin tarjeta).
2. En el dashboard, ir a la pestaña **Databases**. La primera vez va a pedir definir una **contraseña de MySQL** — esa contraseña es la de la base, guárdala (va a tu `.env`, nunca al repo).
3. En esa misma pestaña, en **"Create a database"**, escribir `gedenaz`. PythonAnywhere la crea como `<tu_usuario>$gedenaz` (el plan gratis solo permite **una** base de datos por cuenta, y siempre queda prefijada con tu usuario — no hay forma de evitarlo).
4. Abrir la **consola MySQL** que aparece en esa misma página (o una "Bash console" y correr `mysql -u <tu_usuario> -h <tu_usuario>.mysql.pythonanywhere-services.com '<tu_usuario>$gedenaz' -p`). Ya vas a estar parado dentro de tu base.
5. Pegar el contenido de [`src/gedenaz/data/schema_pythonanywhere.sql`](../../src/gedenaz/data/schema_pythonanywhere.sql) (esta variante, **no** `schema.sql` — no lleva `CREATE DATABASE`/`USE` porque la base ya existe y tiene nombre prefijado).
6. Completar tu `.env` local con los datos que te dio PythonAnywhere:

   ```env
   DB_HOST=<tu_usuario>.mysql.pythonanywhere-services.com
   DB_PORT=3306
   DB_USER=<tu_usuario>
   DB_PASSWORD=<la contraseña que definiste en el paso 2>
   DB_NAME=<tu_usuario>$gedenaz
   ```

7. Verificar la conexión corriendo la API local apuntando a la base en la nube:

   ```bash
   python src/gedenaz/main.py
   ```

   Si `main.py` ya tiene un endpoint que consulta la base (ej. `GET /productos`), probarlo con `curl` o el navegador. Si todavía no existe ese endpoint, alcanza con que la app no tire error de conexión al arrancar.

**Nota**: esto deja la base accesible en la nube, pero el *backend* (la API Flask) todavía puede seguir corriendo en tu máquina mientras desarrollan (apuntando a esta base remota). Desplegar también la API Flask **dentro** de PythonAnywhere (para que Gedalias y Nazareth la usen sin que alguien tenga el compu prendido) es un paso aparte, pendiente de agendar en el plan de trabajo.

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
