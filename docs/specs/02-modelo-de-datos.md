# 02 · Modelo de Datos — GedeNaz App

> Esquema vigente para los requisitos RF1–RF7 definidos en [01-requisitos-funcionales.md](01-requisitos-funcionales.md).

## Entidad: `producto`

El sistema gestiona productos, ventas y líneas de venta (RF1–RF7). No hay entidad "usuario" en base de datos: el sistema tiene un único tipo de usuario (administrador).

| Columna | Tipo MySQL | Restricciones | Notas |
|---|---|---|---|
| `id` | `INT` | `PRIMARY KEY AUTO_INCREMENT` | identificador interno |
| `nombre` | `VARCHAR(120)` | `NOT NULL` | |
| `categoria` | `VARCHAR(60)` | `NOT NULL` | anillo, collar, pulsera, aro, otro (ver RF1) |
| `material` | `VARCHAR(60)` | `NOT NULL` | material declarado para la variante del producto |
| `talla` | `VARCHAR(30)` | `NOT NULL` | talla o medida; "Única" cuando no corresponda |
| `precio` | `DECIMAL(10,2)` | `NOT NULL`, `CHECK (precio > 0)` | CLP, sin decimales de moneda extranjera |
| `stock` | `INT` | `NOT NULL`, `CHECK (stock >= 0)` | ajustado por RF3 |
| `activo` | `TINYINT(1)` | `NOT NULL DEFAULT 1` | soporta baja lógica (RF4) — ver decisión abajo |
| `fecha_creacion` | `DATETIME` | `NOT NULL DEFAULT CURRENT_TIMESTAMP` | auditoría básica |
| `fecha_actualizacion` | `DATETIME` | `NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP` | auditoría básica |
| `fecha_ultimo_ingreso` | `DATETIME` | `NOT NULL DEFAULT CURRENT_TIMESTAMP` | fecha del último alta o reposición de stock |

### DDL propuesto

```sql
CREATE DATABASE IF NOT EXISTS gedenaz
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE gedenaz;

CREATE TABLE IF NOT EXISTS producto (
    id                   INT AUTO_INCREMENT PRIMARY KEY,
    nombre               VARCHAR(120) NOT NULL,
    categoria            VARCHAR(60)  NOT NULL,
    material             VARCHAR(60)  NOT NULL DEFAULT 'Sin especificar',
    talla                VARCHAR(30)  NOT NULL DEFAULT 'Única',
    precio               DECIMAL(10,2) NOT NULL,
    stock                INT NOT NULL,
    activo               TINYINT(1) NOT NULL DEFAULT 1,
    fecha_creacion       DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_actualizacion  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    fecha_ultimo_ingreso DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_precio_positivo CHECK (precio > 0),
    CONSTRAINT chk_stock_no_negativo CHECK (stock >= 0)
);

CREATE INDEX idx_producto_nombre ON producto (nombre);
CREATE INDEX idx_producto_categoria ON producto (categoria);

CREATE TABLE IF NOT EXISTS venta (
    id       INT AUTO_INCREMENT PRIMARY KEY,
    fecha    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    total    DECIMAL(12,2) NOT NULL,
    anulada  TINYINT(1) NOT NULL DEFAULT 0,
    CONSTRAINT chk_venta_total_no_negativo CHECK (total >= 0)
);

CREATE TABLE IF NOT EXISTS detalle_venta (
    id                INT AUTO_INCREMENT PRIMARY KEY,
    venta_id          INT NOT NULL,
    producto_id       INT NOT NULL,
    codigo_producto   VARCHAR(20) NOT NULL,
    nombre_producto   VARCHAR(120) NOT NULL,
    categoria_producto VARCHAR(60) NOT NULL,
    material_producto VARCHAR(60) NOT NULL DEFAULT 'Sin especificar',
    talla_producto    VARCHAR(30) NOT NULL DEFAULT 'Única',
    genero_destino    VARCHAR(20) NOT NULL DEFAULT 'No especificado',
    precio_unitario   DECIMAL(10,2) NOT NULL,
    cantidad          INT NOT NULL,
    subtotal          DECIMAL(12,2) NOT NULL,
    CONSTRAINT fk_detalle_venta_venta FOREIGN KEY (venta_id)
        REFERENCES venta (id),
    CONSTRAINT fk_detalle_venta_producto FOREIGN KEY (producto_id)
        REFERENCES producto (id),
    CONSTRAINT chk_detalle_cantidad_positiva CHECK (cantidad > 0)
);

CREATE INDEX idx_detalle_venta_producto ON detalle_venta (producto_id);
CREATE INDEX idx_venta_fecha ON venta (fecha);

CREATE TABLE IF NOT EXISTS plan_pago (
    id                INT AUTO_INCREMENT PRIMARY KEY,
    venta_id          INT NOT NULL UNIQUE,
    cantidad_cuotas   INT NOT NULL,
    frecuencia        VARCHAR(20) NOT NULL,
    monto_total       DECIMAL(12,2) NOT NULL,
    primer_vencimiento DATE NOT NULL,
    fecha_creacion    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_plan_pago_venta FOREIGN KEY (venta_id) REFERENCES venta (id),
    CONSTRAINT chk_plan_cuotas CHECK (cantidad_cuotas BETWEEN 2 AND 120),
    CONSTRAINT chk_plan_total CHECK (monto_total > 0)
);

CREATE TABLE IF NOT EXISTS cuota (
    id                 INT AUTO_INCREMENT PRIMARY KEY,
    plan_pago_id       INT NOT NULL,
    numero             INT NOT NULL,
    monto              DECIMAL(12,2) NOT NULL,
    fecha_vencimiento  DATE NOT NULL,
    CONSTRAINT fk_cuota_plan FOREIGN KEY (plan_pago_id) REFERENCES plan_pago (id),
    CONSTRAINT uq_cuota_plan_numero UNIQUE (plan_pago_id, numero),
    CONSTRAINT chk_cuota_numero CHECK (numero > 0),
    CONSTRAINT chk_cuota_monto CHECK (monto > 0)
);

CREATE TABLE IF NOT EXISTS abono (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    cuota_id    INT NOT NULL,
    monto       DECIMAL(12,2) NOT NULL,
    fecha_pago  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_abono_cuota FOREIGN KEY (cuota_id) REFERENCES cuota (id),
    CONSTRAINT chk_abono_monto CHECK (monto > 0)
);
```

El código visible de cada producto es `GN-` seguido de su ID con seis dígitos; el ID autoincremental existente asegura que no se repita y no requiere una migración para los productos actuales. La boleta interna usa `BOL-` seguido del ID de venta. `venta.fecha` registra la fecha/hora completa; sus partes año, mes, día y hora se filtran desde el calendario. `detalle_venta` conserva el código, nombre, categoría, material, talla, destinatario y precio aplicados al momento de vender, incluso si el producto cambia posteriormente. Estos datos históricos permiten agrupar la demanda por categoría y precio.

`plan_pago` existe solo para una venta en cuotas; `cuota` guarda el monto y vencimiento de cada cuota; `abono` registra cada pago parcial con su fecha. Para pagos completos no se crea un plan. Los montos son sin interés y se guardan como `DECIMAL(12,2)`; cualquier diferencia de división se agrega a la última cuota. Para impedir inconsistencias, una venta con abonos no puede anularse desde la aplicación.

La aplicación ofrece frecuencias semanal (cada 7 días), quincenal (cada 15 días) y mensual. En vencimientos mensuales se conserva el día del mes cuando existe; si no existe (por ejemplo, día 31 en febrero), se usa el último día de ese mes. La suma de los abonos nunca puede superar el monto de su cuota; el estado se deriva de la suma: pendiente, parcial o pagada.

En instalaciones existentes, ejecutar las sentencias `CREATE TABLE venta` y `CREATE TABLE detalle_venta` de `schema.sql` después de seleccionar la base `gedenaz`. No volver a ejecutar las sentencias `CREATE INDEX` anteriores, pues los índices del inventario ya estarán creados.

Si `detalle_venta` ya existe, añadir la categoría histórica una sola vez y completar las ventas existentes con la categoría actual del producto:

```sql
ALTER TABLE detalle_venta
  ADD COLUMN categoria_producto VARCHAR(60) NOT NULL DEFAULT '';

UPDATE detalle_venta AS dv
INNER JOIN producto AS p ON p.id = dv.producto_id
SET dv.categoria_producto = p.categoria
WHERE dv.categoria_producto = '';
```

Para ventas antiguas, esa categoría es una aproximación basada en la categoría actual del producto; las nuevas ventas guardan la categoría al momento de la venta.

Si la tabla `venta` ya existe, agregar una sola vez el campo para conservar las boletas anuladas en el historial:

```sql
ALTER TABLE venta
  ADD COLUMN anulada TINYINT(1) NOT NULL DEFAULT 0;
```

Si la tabla `producto` ya existía antes de agregar este campo, ejecutar una vez en MySQL Workbench (al ejecutar `CREATE TABLE IF NOT EXISTS`, MySQL no modifica la tabla preexistente):

```sql
ALTER TABLE producto
  ADD COLUMN fecha_ultimo_ingreso DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP;
```

Para actualizar una instalación existente que aún no tiene material ni talla en `producto`, ni los datos históricos de destinatario, material y talla en `detalle_venta`, ejecutar una sola vez:

```sql
ALTER TABLE producto
  ADD COLUMN material VARCHAR(60) NOT NULL DEFAULT 'Sin especificar',
  ADD COLUMN talla VARCHAR(30) NOT NULL DEFAULT 'Única';

ALTER TABLE detalle_venta
  ADD COLUMN material_producto VARCHAR(60) NOT NULL DEFAULT 'Sin especificar',
  ADD COLUMN talla_producto VARCHAR(30) NOT NULL DEFAULT 'Única',
  ADD COLUMN genero_destino VARCHAR(20) NOT NULL DEFAULT 'No especificado';

CREATE INDEX idx_venta_fecha ON venta (fecha);
```

Los valores por defecto conservan los registros actuales sin atribuirles datos que no fueron capturados originalmente. `venta.fecha` ya existe como `DATETIME`, por lo que no requiere migración para mostrar año, mes, día y hora.

Para habilitar planes de cuotas en una instalación existente, ejecutar una sola vez `src/gedenaz/data/installment_migration.sql` (no es necesario alterar las tablas actuales). El script crea estas tres tablas:

```sql
USE gedenaz;
CREATE TABLE IF NOT EXISTS plan_pago (
    id INT AUTO_INCREMENT PRIMARY KEY,
    venta_id INT NOT NULL UNIQUE,
    cantidad_cuotas INT NOT NULL,
    frecuencia VARCHAR(20) NOT NULL,
    monto_total DECIMAL(12,2) NOT NULL,
    primer_vencimiento DATE NOT NULL,
    fecha_creacion DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_plan_pago_venta FOREIGN KEY (venta_id) REFERENCES venta (id),
    CONSTRAINT chk_plan_cuotas CHECK (cantidad_cuotas BETWEEN 2 AND 120),
    CONSTRAINT chk_plan_total CHECK (monto_total > 0)
);

CREATE TABLE IF NOT EXISTS cuota (
    id INT AUTO_INCREMENT PRIMARY KEY,
    plan_pago_id INT NOT NULL,
    numero INT NOT NULL,
    monto DECIMAL(12,2) NOT NULL,
    fecha_vencimiento DATE NOT NULL,
    CONSTRAINT fk_cuota_plan FOREIGN KEY (plan_pago_id) REFERENCES plan_pago (id),
    CONSTRAINT uq_cuota_plan_numero UNIQUE (plan_pago_id, numero),
    CONSTRAINT chk_cuota_numero CHECK (numero > 0),
    CONSTRAINT chk_cuota_monto CHECK (monto > 0)
);

CREATE TABLE IF NOT EXISTS abono (
    id INT AUTO_INCREMENT PRIMARY KEY,
    cuota_id INT NOT NULL,
    monto DECIMAL(12,2) NOT NULL,
    fecha_pago DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_abono_cuota FOREIGN KEY (cuota_id) REFERENCES cuota (id),
    CONSTRAINT chk_abono_monto CHECK (monto > 0)
);
```

Este script vivirá en `src/gedenaz/data/schema.sql` (Fase 1.2 de la Carta Gantt, responsable: Francisco Jara).

## Decisiones de diseño a confirmar con el equipo/empresa

1. **Baja lógica vs. física en RF4**: se propone `activo` (baja lógica) para no perder historial y evitar el riesgo de "Análisis de Riesgos" del informe (pérdida de datos por mala configuración de BD). RF2 (listar) debe filtrar por `activo = 1` por defecto.
2. **Autenticación**: el informe no pide login (un único tipo de usuario, sin roles). Se asume que la app no implementa autenticación en esta versión. Si el equipo decide agregarla, documentar aquí primero.
3. **Categorías**: el informe menciona anillos, collares, pulseras, aros "y otros accesorios" como ejemplos, no como lista cerrada. Se modela `categoria` como texto libre en vez de tabla/catálogo aparte, para mantener el alcance simple; revisar si el equipo prefiere una tabla `categoria` normalizada.
