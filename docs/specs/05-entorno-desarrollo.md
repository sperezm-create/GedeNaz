# 05 · Entorno de Desarrollo — GedeNaz App

> Cubre la tarea **1.1 — "Configurar entorno de desarrollo (VS Code, Python, entorno virtual y librerías)"** de la Carta Gantt (responsable: Nicolas Silva, 2026-09-10 a 2026-09-12). Ejecutar esta guía deja el repositorio listo para que el resto del equipo empiece la Fase 1 (RF1).

## Requisitos previos

- **Python 3.11+** instalado (usado en esta configuración: 3.14.5). Verificar con `python --version`.
- **VS Code** instalado, con la extensión oficial "Python" (Microsoft).
- **Git** instalado y configurado (`git config --global user.name/user.email`).
- **MySQL Server** y **MySQL Workbench** (se instalan en la tarea 1.2, a cargo de Francisco Jara — no bloquea esta tarea).

## 1. Clonar / ubicarse en el repositorio

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
| `mysql-connector-python` | Conector oficial Python↔MySQL (capa `data/`) |
| `python-dotenv` | Carga de variables de entorno desde `.env` |
| `fastapi` y `uvicorn` | API HTTP y servidor para el cliente Android |
| `httpx` | Cliente de pruebas para la API |
| `requests` | Cliente HTTP del cliente móvil |
| `pytest` | Pruebas funcionales (inventario y ventas, RF1–RF6) |

## 4. Configurar variables de entorno

```bash
cp .env.example .env      # Windows: copy .env.example .env
```

Completar `.env` con las credenciales locales de MySQL (host, usuario, contraseña, nombre de base de datos). **Nunca** commitear `.env` (ya está en `.gitignore`).
Para iniciar la API, añadir también `API_ADMIN_USERNAME` y `API_ADMIN_PASSWORD` con credenciales propias; la API no acepta credenciales predeterminadas.

## 5. Configurar VS Code

1. Abrir la carpeta del repositorio en VS Code.
2. `Ctrl+Shift+P` → "Python: Select Interpreter" → elegir el intérprete de `venv/` (`venv\Scripts\python.exe` en Windows).
3. Confirmar que la barra inferior de VS Code muestra el intérprete de `venv`.

## 6. Verificar la instalación

```bash
python -c "import mysql.connector, dotenv, pytest; print('entorno OK')"
pytest --version
```

## API para el cliente Android

Desde Windows PowerShell, en la raíz del repositorio:

```powershell
$env:PYTHONPATH = "src"
python -m gedenaz.api
```

La API escucha en el puerto `8000`. Puedes revisar su documentación OpenAPI en `/docs`. En un servidor remoto, configura HTTPS antes de permitir conexiones con credenciales y restringe el acceso a MySQL para que solo lo use el servidor de la API.

## APK de prueba con Kivy

El proyecto Android está en `mobile/`. Buildozer requiere Linux; en Windows puede usarse WSL2 con una distribución Linux y las dependencias Android indicadas por la guía de instalación de Buildozer.

En WSL2, instala Buildozer en un entorno virtual Linux y, desde el directorio `mobile/`, ejecuta:

```bash
buildozer android debug
```

El APK de depuración se genera en `mobile/bin/`. Instálalo en la tablet con Android Debug Bridge (`adb install`) y conecta el cliente a una URL alcanzable de la API. No uses HTTP sin cifrar fuera de una red de desarrollo controlada.

## Convenciones del repositorio

- Código de la app en `src/gedenaz/` (ver estructura en [03-arquitectura.md](03-arquitectura.md)).
- Pruebas en `tests/`, en espejo de `src/gedenaz/` (ej. `tests/logic/test_productos.py`).
- Specs en `docs/specs/` — **se actualizan antes** de implementar un cambio de alcance o de modelo de datos (spec-first).
- Commits en español, descriptivos, referenciando el RF o la tarea de la Carta Gantt cuando aplique (ej. `RF1: agrega validación de stock no negativo`).
- Nomenclatura de código en `snake_case` para variables/funciones y `PascalCase` para clases, siguiendo PEP 8 (mencionado en informe 8.3: "convenciones estándar de nomenclatura y organización de código").
