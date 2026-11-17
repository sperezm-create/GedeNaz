# GedeNaz App

Aplicación de escritorio (Python + MySQL) y cliente Android en desarrollo (Kivy + API FastAPI) para la gestión de inventario de joyas de la empresa GedeNaz. Proyecto del curso Taller de Sistemas de Información (INFB8082), Grupo N°6.

Incluye registro de ventas desde el inventario, boletas internas, descuento de stock, planes de cuotas sin interés con abonos parciales, calendario con historial por fecha y hora e indicadores de productos más vendidos. Los productos registran material y talla; cada línea de venta conserva si fue para hombre o mujer.

## Memoria y bitácora

- [`docs/MEMORIA_PROYECTO.md`](docs/MEMORIA_PROYECTO.md) — foto del estado actual del proyecto (léelo primero si vuelves después de un tiempo).
- [`docs/BITACORA.md`](docs/BITACORA.md) — registro cronológico de qué se hizo en cada sesión de trabajo.
- [`docs/planificacion/requerimientos-y-horas-hombre.md`](docs/planificacion/requerimientos-y-horas-hombre.md) — requerimientos consolidados y estimación de esfuerzo para los cuatro integrantes.

## Especificaciones (spec-first)

Este proyecto se desarrolla en modalidad **spec-first**: antes de programar un cambio de alcance, requisito o modelo de datos, se actualiza el documento correspondiente en [`docs/specs/`](docs/specs/):

1. [00-vision-y-alcance.md](docs/specs/00-vision-y-alcance.md) — resumen, problema, objetivos, alcance.
2. [01-requisitos-funcionales.md](docs/specs/01-requisitos-funcionales.md) — RF1–RF7 con criterios de aceptación.
3. [02-modelo-de-datos.md](docs/specs/02-modelo-de-datos.md) — productos, ventas y esquema MySQL.
4. [03-arquitectura.md](docs/specs/03-arquitectura.md) — arquitectura de 3 capas y stack tecnológico.
5. [04-plan-de-trabajo.md](docs/specs/04-plan-de-trabajo.md) — fases, hitos y roles (Carta Gantt).
6. [05-entorno-desarrollo.md](docs/specs/05-entorno-desarrollo.md) — cómo levantar el entorno de desarrollo.

## Quickstart

```bash
python -m venv venv
# Windows: .\venv\Scripts\Activate.ps1   |   macOS/Linux: source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # y completar credenciales de MySQL
pytest
# Windows PowerShell, desde la raíz del proyecto:
$env:PYTHONPATH = "src"; python -m gedenaz.main
```

Detalle completo en [05-entorno-desarrollo.md](docs/specs/05-entorno-desarrollo.md).

## Cliente Android (en desarrollo)

La app de escritorio permanece en `src/gedenaz/ui/`. El cliente Kivy de Android está en `mobile/` y se conecta únicamente a la API; las credenciales de MySQL permanecen en el servidor.

1. En `.env`, configura `API_ADMIN_USERNAME` y `API_ADMIN_PASSWORD` con credenciales propias.
2. En TiDB Cloud Starter/Essential, descarga el certificado CA desde **Connect** y configura `DB_HOST`, `DB_PORT=4000`, `DB_USER`, `DB_PASSWORD`, `DB_NAME` y `DB_SSL_CA` en el entorno donde se ejecute la API.
3. Inicia la API desde la raíz del proyecto: `python -m gedenaz.api` con `PYTHONPATH=src` configurado.
4. En Android, ingresa la URL de la API. Para producción, publica la API detrás de HTTPS y no expongas MySQL a internet.
5. Para generar un APK de prueba, usa Linux o WSL2, instala Buildozer allí y, desde `mobile/`, ejecuta `buildozer android debug`.

El cliente móvil de este avance incluye inicio de sesión e inventario de consulta. Los endpoints del servidor ya contemplan ventas, cuotas y estadísticas; sus pantallas móviles aún requieren migración. La guía de desarrollo está en [docs/specs/05-entorno-desarrollo.md](docs/specs/05-entorno-desarrollo.md).

Para habilitar ventas en una base existente, seleccionar la base `gedenaz` en MySQL Workbench y ejecutar las sentencias `CREATE TABLE venta` y `CREATE TABLE detalle_venta` de `src/gedenaz/data/schema.sql` (sin repetir las sentencias `CREATE INDEX` del inventario). La boleta generada es un comprobante interno, no un documento tributario electrónico.

Si `venta` ya estaba creada, agrega la columna que permite anular boletas conservando su historial:

```sql
USE gedenaz;
ALTER TABLE venta
  ADD COLUMN anulada TINYINT(1) NOT NULL DEFAULT 0;
```

La anulación de una boleta repone todas las unidades de sus productos, la conserva en el historial marcada como anulada y la excluye de las estadísticas. Solo puede anularse una vez.

Para habilitar el porcentaje de ventas por categoría en una base que ya tenía `detalle_venta`, ejecuta una sola vez:

```sql
USE gedenaz;
ALTER TABLE detalle_venta
  ADD COLUMN categoria_producto VARCHAR(60) NOT NULL DEFAULT '';

UPDATE detalle_venta AS dv
INNER JOIN producto AS p ON p.id = dv.producto_id
SET dv.categoria_producto = p.categoria
WHERE dv.categoria_producto = '';
```

La pestaña Estadísticas muestra participación por unidades vendidas de cada categoría y precios unitarios agrupados por unidades, ordenados del más vendido al menos vendido. Las boletas anuladas no se incluyen.

Si al guardar un producto aparece `1054 (42S22): Unknown column 'fecha_ultimo_ingreso'`, actualizar la tabla existente una sola vez desde MySQL Workbench:

```sql
USE gedenaz;
ALTER TABLE producto
  ADD COLUMN fecha_ultimo_ingreso DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP;
```

`CREATE TABLE IF NOT EXISTS` no agrega columnas a tablas que ya existían; esta actualización conserva los productos y el stock actuales.

Para instalaciones existentes, habilitar material/talla y el historial de destinatario en MySQL Workbench ejecutando una sola vez (no repetir si las columnas ya existen):

```sql
USE gedenaz;
ALTER TABLE producto
  ADD COLUMN material VARCHAR(60) NOT NULL DEFAULT 'Sin especificar',
  ADD COLUMN talla VARCHAR(30) NOT NULL DEFAULT 'Única';

ALTER TABLE detalle_venta
  ADD COLUMN material_producto VARCHAR(60) NOT NULL DEFAULT 'Sin especificar',
  ADD COLUMN talla_producto VARCHAR(30) NOT NULL DEFAULT 'Única',
  ADD COLUMN genero_destino VARCHAR(20) NOT NULL DEFAULT 'No especificado';

CREATE INDEX idx_venta_fecha ON venta (fecha);
```

La columna `venta.fecha` ya registra la fecha/hora completa, así que el calendario no requiere alterar las ventas existentes. El detalle conserva los nuevos datos para las ventas futuras; las ventas antiguas muestran los valores predeterminados porque esos datos no estaban registrados.

Para habilitar los planes de cuotas sin interés en una base existente, ejecutar una sola vez el script `src/gedenaz/data/installment_migration.sql` en MySQL Workbench. La pestaña Ventas permite seleccionar entre 2 y 120 cuotas, frecuencia y primer vencimiento; luego, desde el historial, se registran abonos parciales contra una cuota y se consulta cuánto se pagó y cuánto queda pendiente. Una venta con abonos no se puede anular desde la aplicación, ya que las devoluciones de dinero aún no se registran.

## Stack

Python 3.11+ · Tkinter · MySQL · `mysql-connector-python` · pytest · VS Code · Git/GitHub · Jira (Kanban).

## Equipo

Sebastián Pérez · Francisco Jara (jefe de proyecto) · Cristóbal Sierra Porras · Nicolas Silva.
