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
pip install -e .
```

El segundo comando instala el propio paquete `gedenaz` (carpeta `src/gedenaz/`) en modo editable — sin esto, `python src/gedenaz/main.py` falla con `ModuleNotFoundError: No module named 'gedenaz'` (problema clásico de la estructura `src/`; se probó y se confirmó en la sesión del 2026-09-16, ver bitácora).

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

Una vez que tu `.env` apunte a una base real (sección 8 más abajo), también existe `GET /health/db`, que intenta conectarse a MySQL y confirma si la conexión (incluyendo SSL) está funcionando.

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

**Importante — inactividad**: el plan gratis de Aiven **apaga el servicio automáticamente tras un período de inactividad** (avisan antes por correo). No hace falta que pasen semanas: **el 2026-09-20 se encontró apagado tras solo ~4 días sin uso** (feriado de fiestas patrias). Los datos **no se pierden**; hay que encenderlo a mano: consola de Aiven → servicio `mysql-gedenaz-bd` → **"Power on"** (tarda un par de minutos en volver a "Running").

**Cómo reconocer que está apagado**: `GET /health/db` de la API responde `503` con un `detail` como `Can't connect to MySQL server ... (Errno -2: Name or service not known)`, y localmente `mysql.connector` falla con `Unknown MySQL server host` (el nombre de host deja de resolver mientras el servicio está apagado). `GET /health` (sin base) sigue en `200`. **Antes de cualquier demo o entrega, conviene revisar `/health/db` y encender el servicio si hace falta.**

**Actualizar el esquema de una base que ya existe** (ej. al sumar tablas nuevas como `venta`/`detalle_venta`): `schema_cloud.sql` es idempotente, así que basta volver a correr `python scripts/apply_schema.py src/gedenaz/data/schema_cloud.sql` — crea solo lo que falta y no toca los datos.

**Error común — "Invalid ssl-mode"**: si al conectar (Workbench o `mysql-connector-python`) sale `Invalid ssl-mode, value should be either 'verify_ca' or 'verify_identity' when any of 'ssl-ca'... are provided`, es porque diste un certificado CA sin pedirle al cliente que lo use para verificar. Arreglo:
- **MySQL Workbench**: en la conexión → pestaña **SSL** → cambiar "Use SSL" de "If available" a **"Require and Verify CA"**.
- **mysql-connector-python**: pasar `ssl_verify_cert=True` junto con `ssl_ca` al conectar (ver comentario en `config.py`, campo `ssl_ca`).

## 9. Desplegar el backend en Render

> ✅ **Ya desplegado** (2026-09-16): `https://gedenaz-api.onrender.com`. Esta sección queda como referencia para quien necesite repetir el proceso (ej. un segundo servicio, o si el actual se borra).

> La base en Aiven ya queda accesible desde internet, pero mientras desarrollan la API Flask solo corre en la máquina de cada uno (`python src/gedenaz/main.py`). Para que Gedalias y Nazareth la usen sin que alguien tenga el computador prendido, se despliega en **Render** (free tier, 750h/mes, sin tarjeta — se descartó como hosting de MySQL porque no lo soporta, pero sí sirve para alojar el backend, ver [03-arquitectura.md](03-arquitectura.md)).

Como el dev server de Flask (`app.run()`) **no es apto para producción** (lo dice la propia advertencia que tira al arrancar), en Render se usa **Gunicorn** en su lugar — ya está en `requirements.txt`.

**Importante — el repo no tiene por qué ser tuyo**: quien haga este despliegue probablemente no es el dueño del repo en GitHub (acá lo hizo Nicolas, dueño es Sebastian). Conectar Render directo a GitHub pide instalar su app con permisos de administrador sobre el repo, que un colaborador normal no necesariamente tiene. Como `sperezm-create/GedeNaz` es **público**, se evita todo esto usando la opción **"Public Git Repository"** (pegar la URL del repo, sin conectar ninguna cuenta de GitHub) en vez de "conectar GitHub". **Trade-off aceptado**: con este método **no hay auto-deploy** — después de cada push a `main` que quieran llevar a producción, hay que entrar al panel de Render y apretar **"Manual Deploy"** a mano. Si en algún momento el dueño del repo quiere auto-deploy, puede conectar su propia cuenta de GitHub (él sí tiene permisos de administrador sobre su propio repo).

1. Crear una cuenta en [render.com](https://render.com) (no hace falta que sea con GitHub si van a usar "Public Git Repository" — ver nota arriba).
2. Dashboard → **New +** → **Web Service** → buscar la opción **"Public Git Repository"** (junto al selector de repos conectados) → pegar `https://github.com/sperezm-create/GedeNaz`.
3. Configurar el servicio:
   - **Name**: `gedenaz-api` (o lo que prefieran — define la URL pública, `<name>.onrender.com`)
   - **Region**: cualquiera (no hay región en Sudamérica; Oregon u otra por defecto está bien para un proyecto de curso)
   - **Branch**: `main`
   - **Root Directory**: dejar vacío
   - **Runtime**: `Python 3`
   - **Build Command**:
     ```
     pip install -r requirements.txt && pip install -e .
     ```
   - **Start Command**:
     ```
     gunicorn "gedenaz.app:create_app()"
     ```
   - **Instance Type**: **Free**
4. **Variables de entorno** (pestaña "Environment" → "Environment Variables"): agregar `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME` con los mismos valores que tu `.env` local de Aiven.
5. **Certificado CA** (mismo tab, sección **"Secret Files"** — para archivos que no van al repo, distinto de las variables de arriba): crear un secret file, pegar ahí el contenido de `secrets/aiven-ca.pem`. Render va a mostrar la ruta donde lo monta dentro del servicio (normalmente algo como `/etc/secrets/<nombre_del_archivo>`) — copiar esa ruta exacta.
6. Volver a "Environment Variables" y agregar `DB_SSL_CA` con esa ruta (la de Render, **no** `secrets/aiven-ca.pem` que es la ruta local).
7. **Create Web Service** → Render clona el repo (completo -- no hay forma de clonar solo una carpeta con una URL de git simple; no es un problema porque nada de lo demás queda expuesto por HTTP, Flask solo sirve las rutas que define), corre el build y arranca. Revisar la pestaña "Logs" si algo falla.
8. Una vez desplegado, probar con la URL pública que da Render:
   ```bash
   curl https://<name>.onrender.com/health
   curl https://<name>.onrender.com/health/db
   ```

**Recordatorios**:
- El free tier de Render "duerme" el servicio tras 15 minutos sin tráfico (la primera petición después tarda ~1 min en responder mientras despierta) — normal, no es un error.
- Sin auto-deploy (ver nota de "Public Git Repository" arriba): cada push a `main` que quieran en producción necesita un "Manual Deploy" desde el panel de Render.

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
