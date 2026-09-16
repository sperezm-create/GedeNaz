# 05 · Entorno de Desarrollo — GedeNaz App

> Cubre la tarea **1.1 — "Configurar entorno de desarrollo"** de la Carta Gantt (responsable: Nicolas Silva). Esta guía monta el entorno del **backend (API Python + MySQL)** — ver [03-arquitectura.md](03-arquitectura.md). El entorno de la **app Android** se documenta aparte en `mobile/README.md` en cuanto el equipo defina el framework.

## Requisitos previos

- **Python 3.11+** instalado (usado en esta configuración: 3.14.5). Verificar con `python --version`.
- **VS Code** instalado, con la extensión oficial "Python" (Microsoft).
- **Git** instalado y configurado (`git config --global user.name/user.email`).
- **MySQL Server** y **MySQL Workbench** (se instalan en la tarea 1.2, a cargo de Francisco Jara — no bloquea esta tarea) para desarrollo local. En producción, MySQL vive en **Aiven** (gratis, en la nube) en vez de instalarse localmente — ver sección 8 más abajo y [03-arquitectura.md](03-arquitectura.md).

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

## 8. Desplegar la base de datos en Aiven

> **Corrección (2026-09-16)**: se había documentado PythonAnywhere como hosting único (API + MySQL juntos), pero PythonAnywhere movió el acceso a MySQL a sus planes pagos en enero de 2026, y además sus cuentas gratuitas **no pueden conectarse a ninguna base de datos externa** (solo HTTP/HTTPS a una lista blanca de sitios) — así que tampoco sirve como "solo hosting del backend" apuntando a una base en otro lado. Se reemplaza por **Aiven** (MySQL, gratis, sin tarjeta) + **Render** (hosting del backend Flask, gratis, sin tarjeta) como dos servicios separados. Ver [BITACORA.md](../BITACORA.md) para el detalle de la investigación.

Esta sección la ejecuta cada quien con **su propia cuenta** — son pasos manuales en la web de Aiven, no se pueden automatizar desde acá.

1. Crear una cuenta gratuita en [aiven.io](https://aiven.io) (sin tarjeta).
2. Crear un nuevo servicio **MySQL**, plan **"Free"** (1GB RAM / 1GB almacenamiento, un solo nodo).
3. En la página del servicio (pestaña **Overview**), anotar: `Host`, `Port`, `User` (normalmente `avnadmin`), `Password` y descargar el **certificado CA** (Aiven exige conexión SSL) — el botón para descargarlo está en esa misma página.
4. Aiven crea automáticamente una base llamada `defaultdb`. Se puede usar esa directamente, o crear una llamada `gedenaz` desde la pestaña **Databases** del servicio → **Create database**.
5. Conectarse (desde tu máquina, con el cliente `mysql` o MySQL Workbench) usando esos datos, y correr el contenido de [`src/gedenaz/data/schema_cloud.sql`](../../src/gedenaz/data/schema_cloud.sql) (esta variante, **no** `schema.sql` — no lleva `CREATE DATABASE`/`USE`).
6. Guardar el certificado CA descargado en un lugar del proyecto que **no se suba a Git** (ej. `secrets/aiven-ca.pem` — agregar `secrets/` a `.gitignore` si no está) y completar tu `.env` local:

   ```env
   DB_HOST=<algo>.aivencloud.com
   DB_PORT=<el puerto que te dio Aiven>
   DB_USER=avnadmin
   DB_PASSWORD=<la contraseña de tu servicio>
   DB_NAME=defaultdb        # o "gedenaz" si creaste una aparte
   DB_SSL_CA=secrets/aiven-ca.pem
   ```

7. Verificar la conexión corriendo la API local apuntando a la base en la nube: `python src/gedenaz/main.py`.

**Importante — inactividad**: el plan gratis de Aiven **apaga el servicio automáticamente tras un período de inactividad** (avisan antes por correo). Si lo dejan quieto varias semanas (ej. entre avances de la Carta Gantt), puede que haya que volver a encenderlo manualmente desde la consola de Aiven antes de una demo o entrega.

**Error común — "Invalid ssl-mode"**: si al conectar (Workbench o `mysql-connector-python`) sale `Invalid ssl-mode, value should be either 'verify_ca' or 'verify_identity' when any of 'ssl-ca'... are provided`, es porque diste un certificado CA sin pedirle al cliente que lo use para verificar. Arreglo:
- **MySQL Workbench**: en la conexión → pestaña **SSL** → cambiar "Use SSL" de "If available" a **"Require and Verify CA"**.
- **mysql-connector-python**: pasar `ssl_verify_cert=True` junto con `ssl_ca` al conectar (ver comentario en `config.py`, campo `ssl_ca`).

### Backend (Flask) en Render — pendiente de ejecutar

La base ya queda accesible en la nube con lo anterior, pero eso no aloja la API Flask en ningún lado — mientras desarrollan, cada uno la sigue corriendo en su propia máquina apuntando a Aiven. Para que Gedalias y Nazareth puedan usarla sin que alguien tenga el computador prendido, falta desplegar la API en **Render** (free tier, 750h/mes, sin tarjeta — ver [03-arquitectura.md](03-arquitectura.md)). Queda pendiente de agendar en el plan de trabajo; cuando se haga, documentar acá los pasos igual que para Aiven.

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
