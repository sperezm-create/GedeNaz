# Guía para probar GedeNaz en tu computador (WSL / Ubuntu)

El proyecto ya trae tu `.env` (TiDB, usuario y clave) y `secrets/tidb-ca.pem`. La app usa la base **`gedenaz_final`** (la base `gedenaz` es del otro proyecto y tiene tablas distintas).

**Usuario y contraseña de la app:** los de `API_ADMIN_USERNAME` y `API_ADMIN_PASSWORD` del `.env`. Son los mismos en la app de escritorio, la app móvil y la API.

## 1. Instalar (una sola vez)

```bash
sudo apt update && sudo apt install -y python3-full python3-venv python3-tk
cd /mnt/c/Users/Infinite/Desktop/Programas/gedenaz/Finale/finalversion
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## 2. Crear las tablas (una sola vez)

```bash
python scripts/apply_schema.py
python scripts/check_db.py     # debe terminar en: OK: conexion y tablas correctas.
```

Si el SQL Editor de TiDB aún no tiene los CHECK activos, ejecuta allí una vez: `SET GLOBAL tidb_enable_check_constraint = ON;` (antes de crear las tablas).

## 3. Abrir la aplicación completa (escritorio)

```bash
source venv/bin/activate
PYTHONPATH=src python -m gedenaz.main
```

Se abre el login. Con usuario/contraseña incorrectos muestra un mensaje bajo los campos y puedes reintentar de inmediato. Una vez dentro tienes inventario, ventas, cuotas, calendario y estadísticas, guardados en TiDB.

## 4. API y app móvil (opcional)

Terminal 1:
```bash
python scripts/run_api.py          # http://127.0.0.1:8000  (documentación en /docs)
```
Terminal 2:
```bash
pip install -r mobile/requirements-desktop.txt
sudo apt install -y libgl1 libmtdev1 libsdl2-2.0-0
python mobile/main.py
```
Ingresa tu usuario y contraseña (el servidor ya viene como `http://127.0.0.1:8000`).

## 5. Pruebas automáticas
```bash
pytest
```

## Problemas frecuentes

| Síntoma | Solución |
|---|---|
| `Unknown database 'gedenaz_final'` | Ejecuta `python scripts/apply_schema.py` (la crea). |
| `Unknown column ...` | `DB_NAME` debe ser `gedenaz_final`, no `gedenaz`. |
| `Usuario o contraseña incorrectos` | Usa los de `API_ADMIN_USERNAME` / `API_ADMIN_PASSWORD` en `.env`. |
| `Invalid CA Certificate` | Debe existir `secrets/tidb-ca.pem`. |
| `No module named tkinter` | `sudo apt install -y python3-tk`. |
| No abre ninguna ventana | Falta WSLg: `wsl --update` en PowerShell de Windows y `wsl --shutdown`. |
| `.env` con la clave: no lo subas a GitHub | Ya está en `.gitignore`. |
