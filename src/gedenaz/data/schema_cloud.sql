-- Esquema para hosts MySQL gestionados (TiDB Cloud, Aiven): la base ya viene
-- creada desde la consola o por scripts/apply_schema.py, asi que no lleva
-- CREATE DATABASE ni USE. Fuente de verdad: schema.sql (mantener sincronizados).
--
-- Es idempotente: se puede volver a ejecutar y solo crea lo que falta
-- (los indices van dentro de CREATE TABLE porque MySQL no soporta
-- CREATE INDEX IF NOT EXISTS). La collation es explicita porque TiDB usa
-- utf8mb4_bin por defecto, que distingue mayusculas.
--
-- Aplicar con:  python scripts/apply_schema.py
-- ATENCION: en TiDB hay que activar los CHECK una vez por cluster:
--   SET GLOBAL tidb_enable_check_constraint = ON;

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
    CONSTRAINT chk_stock_no_negativo CHECK (stock >= 0),
    INDEX idx_producto_nombre (nombre),
    INDEX idx_producto_categoria (categoria)
) DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS venta (
    id       INT AUTO_INCREMENT PRIMARY KEY,
    fecha    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    total    DECIMAL(12,2) NOT NULL,
    anulada  TINYINT(1) NOT NULL DEFAULT 0,
    CONSTRAINT chk_venta_total_no_negativo CHECK (total >= 0),
    INDEX idx_venta_fecha (fecha)
) DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

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
    CONSTRAINT chk_detalle_cantidad_positiva CHECK (cantidad > 0),
    INDEX idx_detalle_venta_producto (producto_id)
) DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS plan_pago (
    id                 INT AUTO_INCREMENT PRIMARY KEY,
    venta_id           INT NOT NULL UNIQUE,
    cantidad_cuotas    INT NOT NULL,
    frecuencia         VARCHAR(20) NOT NULL,
    monto_total        DECIMAL(12,2) NOT NULL,
    primer_vencimiento DATE NOT NULL,
    fecha_creacion     DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_plan_pago_venta FOREIGN KEY (venta_id) REFERENCES venta (id),
    CONSTRAINT chk_plan_cuotas CHECK (cantidad_cuotas BETWEEN 2 AND 120),
    CONSTRAINT chk_plan_total CHECK (monto_total > 0)
) DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS cuota (
    id                INT AUTO_INCREMENT PRIMARY KEY,
    plan_pago_id      INT NOT NULL,
    numero            INT NOT NULL,
    monto             DECIMAL(12,2) NOT NULL,
    fecha_vencimiento DATE NOT NULL,
    CONSTRAINT fk_cuota_plan FOREIGN KEY (plan_pago_id) REFERENCES plan_pago (id),
    CONSTRAINT uq_cuota_plan_numero UNIQUE (plan_pago_id, numero),
    CONSTRAINT chk_cuota_numero CHECK (numero > 0),
    CONSTRAINT chk_cuota_monto CHECK (monto > 0)
) DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS abono (
    id         INT AUTO_INCREMENT PRIMARY KEY,
    cuota_id   INT NOT NULL,
    monto      DECIMAL(12,2) NOT NULL,
    fecha_pago DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_abono_cuota FOREIGN KEY (cuota_id) REFERENCES cuota (id),
    CONSTRAINT chk_abono_monto CHECK (monto > 0)
) DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
