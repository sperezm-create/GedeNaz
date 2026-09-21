# 02 · Modelo de Datos — GedeNaz App

> Propuesta inicial de esquema MySQL a partir del informe (sección 6.2 y RF1, [01-requisitos-funcionales.md](01-requisitos-funcionales.md)). A validar/ajustar con la empresa y con quien implemente la capa de datos (Fase 1.2, Carta Gantt).
>
> **Nota (2026-09-09)**: el esquema no cambia por el paso a app Android (ver [00-vision-y-alcance.md](00-vision-y-alcance.md)) — MySQL sigue siendo la base de datos, solo que ahora la toca únicamente la API (ver [03-arquitectura.md](03-arquitectura.md)), nunca la app directamente.

> **Nota (2026-09-20)**: se agregan las entidades `venta` y `detalle_venta` (RF5 y RF3.1, ver [00-vision-y-alcance.md](00-vision-y-alcance.md)). `producto` no cambia. Las tres viven en `schema.sql` / `schema_cloud.sql`.

## Entidad: `producto`

Entidad central del inventario (RF1–RF4). No hay entidad "usuario" en base de datos: el sistema tiene un único tipo de usuario (administrador) y no se especificó autenticación en el informe — se documenta como pregunta abierta más abajo.

| Columna | Tipo MySQL | Restricciones | Notas |
|---|---|---|---|
| `id` | `INT` | `PRIMARY KEY AUTO_INCREMENT` | identificador interno |
| `nombre` | `VARCHAR(120)` | `NOT NULL` | |
| `categoria` | `VARCHAR(60)` | `NOT NULL` | anillo, collar, pulsera, aro, otro (ver RF1) |
| `precio` | `DECIMAL(10,2)` | `NOT NULL`, `CHECK (precio > 0)` | CLP, sin decimales de moneda extranjera |
| `stock` | `INT` | `NOT NULL`, `CHECK (stock >= 0)` | ajustado por RF3 |
| `activo` | `TINYINT(1)` | `NOT NULL DEFAULT 1` | soporta baja lógica (RF4) — ver decisión abajo |
| `fecha_creacion` | `DATETIME` | `NOT NULL DEFAULT CURRENT_TIMESTAMP` | auditoría básica |
| `fecha_actualizacion` | `DATETIME` | `NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP` | auditoría básica |

### DDL propuesto

```sql
CREATE DATABASE IF NOT EXISTS gedenaz
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE gedenaz;

CREATE TABLE IF NOT EXISTS producto (
    id                   INT AUTO_INCREMENT PRIMARY KEY,
    nombre               VARCHAR(120) NOT NULL,
    categoria            VARCHAR(60)  NOT NULL,
    precio               DECIMAL(10,2) NOT NULL,
    stock                INT NOT NULL,
    activo               TINYINT(1) NOT NULL DEFAULT 1,
    fecha_creacion       DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_actualizacion  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT chk_precio_positivo CHECK (precio > 0),
    CONSTRAINT chk_stock_no_negativo CHECK (stock >= 0),
    INDEX idx_producto_nombre (nombre),
    INDEX idx_producto_categoria (categoria)
) DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

Cada tabla declara `DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci` de forma **explícita** (ver decisión 10). Este script vive en `src/gedenaz/data/schema.sql` (Fase 1.2 de la Carta Gantt, responsable: Francisco Jara). Los índices están declarados **dentro** del `CREATE TABLE` (no como `CREATE INDEX` aparte) a propósito: MySQL no soporta `CREATE INDEX IF NOT EXISTS`, y así el archivo completo se puede volver a ejecutar sin error para sumar tablas nuevas a una base que ya existe.

## Entidades: `venta` y `detalle_venta` (RF5, RF3.1)

Modelo **cabecera / detalle**, igual que una boleta real: `venta` es la boleta (una fila por venta, con su fecha) y `detalle_venta` son sus líneas (una fila por cada producto distinto vendido en esa boleta).

```
producto 1 ────< detalle_venta >──── 1 venta
```

Un `producto` puede aparecer en muchas líneas a lo largo del tiempo; una `venta` tiene una o más líneas.

**`venta`**

| Columna | Tipo MySQL | Restricciones | Notas |
|---|---|---|---|
| `id` | `INT` | `PRIMARY KEY AUTO_INCREMENT` | |
| `fecha_venta` | `DATETIME` | `NOT NULL DEFAULT CURRENT_TIMESTAMP`, indexada | momento del registro (ver decisión de zona horaria abajo) |

**`detalle_venta`**

| Columna | Tipo MySQL | Restricciones | Notas |
|---|---|---|---|
| `id` | `INT` | `PRIMARY KEY AUTO_INCREMENT` | |
| `venta_id` | `INT` | `NOT NULL`, `FOREIGN KEY → venta(id)` | |
| `producto_id` | `INT` | `NOT NULL`, `FOREIGN KEY → producto(id)` | |
| `cantidad` | `INT` | `NOT NULL`, `CHECK (cantidad > 0)` | unidades vendidas de esa línea |
| `precio_unitario` | `DECIMAL(10,2)` | `NOT NULL` | **foto** del `producto.precio` al instante de la venta (ver decisión 4) |

### DDL

```sql
CREATE TABLE IF NOT EXISTS venta (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    fecha_venta  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_venta_fecha (fecha_venta)
) DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS detalle_venta (
    id               INT AUTO_INCREMENT PRIMARY KEY,
    venta_id         INT NOT NULL,
    producto_id      INT NOT NULL,
    cantidad         INT NOT NULL,
    precio_unitario  DECIMAL(10,2) NOT NULL,
    CONSTRAINT fk_detalle_venta FOREIGN KEY (venta_id) REFERENCES venta (id),
    CONSTRAINT fk_detalle_producto FOREIGN KEY (producto_id) REFERENCES producto (id),
    CONSTRAINT chk_cantidad_positiva CHECK (cantidad > 0)
) DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

MySQL crea solo los índices de las dos claves foráneas, así que no se declaran a mano.

## Decisiones de diseño a confirmar con el equipo/empresa

1. **Baja lógica vs. física en RF4**: se propone `activo` (baja lógica) para no perder historial y evitar el riesgo de "Análisis de Riesgos" del informe (pérdida de datos por mala configuración de BD). RF2 (listar) debe filtrar por `activo = 1` por defecto.
2. **Autenticación**: el informe no pide login (un único tipo de usuario, sin roles). Se asume que la app no implementa autenticación en esta versión. **Ojo**: al ser ahora una API expuesta en internet (no un programa de escritorio en la red local de la tienda), esto pesa más de lo pensado originalmente — cualquiera que encuentre la URL de la API podría leer/modificar el inventario sin login. Como mínimo se recomienda una clave compartida simple (API key) entre la app y la API; si el equipo decide agregar algo más, documentar aquí primero.
3. **Categorías**: el informe menciona anillos, collares, pulseras, aros "y otros accesorios" como ejemplos, no como lista cerrada. Se modela `categoria` como texto libre en vez de tabla/catálogo aparte, para mantener el alcance simple; revisar si el equipo prefiere una tabla `categoria` normalizada.

### Decisiones sobre ventas (adoptadas 2026-09-20)

4. **`precio_unitario` es una foto, no una referencia.** Cada línea copia el precio vigente en el instante de la venta. Si solo se guardara `producto_id` y el precio se leyera de `producto.precio` al generar un reporte, cada cambio de precio reescribiría retroactivamente todo el historial (un reporte de "ingresos de la semana pasada" daría un número distinto según el día en que se consulte).
5. **Cabecera/detalle en vez de una lista de ids.** Se descartó un campo tipo `id_productos = "3,7,12"`: rompe la primera forma normal, no permite `FOREIGN KEY`, no hay dónde guardar cantidad y precio por producto, y los reportes tendrían que parsear texto en vez de usar `GROUP BY`/`SUM`.
6. **`fecha_venta` vive solo en `venta`.** Los reportes por fecha hacen `JOIN` con `venta`; no se duplica en `detalle_venta` (evita datos redundantes que puedan quedar inconsistentes; el volumen de una joyería no justifica desnormalizar).
7. **Las ventas son inmutables** (sin `UPDATE`/`DELETE` en esta versión) y ningún `DELETE` físico de `producto` es posible si tiene ventas (la `FOREIGN KEY` lo impide) — coherente con la baja lógica de la decisión 1: un producto dado de baja conserva su historial de ventas.
8. **Registrar una venta es una sola transacción** que bloquea las filas de los productos involucrados (`SELECT ... FOR UPDATE`, siempre en orden de `id` para evitar bloqueos cruzados): valida existencia y stock, inserta la cabecera y las líneas, y descuenta el stock. Si algo falla, no queda nada guardado. El bloqueo evita que dos ventas simultáneas del mismo producto vendan más stock del que hay.
9. **Las fechas se guardan en hora de Chile, no en UTC.** Aiven trabaja en UTC por defecto, y con eso una venta a las 21:30 hora local quedaría registrada "al día siguiente", desajustando los reportes filtrados por día (RF3.1). Cada conexión fija la zona de la sesión (`DB_TIMEZONE`, por defecto `America/Santiago`; ver [03-arquitectura.md](03-arquitectura.md)), así `CURRENT_TIMESTAMP`/`NOW()` ya producen hora local. Las filas anteriores al 2026-09-20 (los productos de prueba sembrados) conservan timestamps en UTC; ninguna regla de negocio depende de ellos.
10. **La collation se declara explícita en cada tabla** (`utf8mb4_unicode_ci`, no distingue mayúsculas ni tildes). RF2 exige búsqueda "insensible a mayúsculas/minúsculas" y eso lo decide la collation de la columna, no nuestro código. Antes dependía de lo que trajera la base por defecto: Aiven (MySQL 8.4) usa `utf8mb4_0900_ai_ci`, que funciona, pero TiDB usa `utf8mb4_bin`, que **sí distingue mayúsculas** y rompía la búsqueda (detectado el 2026-09-20 al probar TiDB Cloud). Declararla explícita hace el esquema portable entre proveedores. Las tablas que ya existen en Aiven no cambian (`CREATE TABLE IF NOT EXISTS` las omite) y siguen siendo insensibles.
