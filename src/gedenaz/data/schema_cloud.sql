-- Variante de schema.sql para hosts MySQL gestionados donde la base ya
-- viene creada (o se crea desde la consola web del proveedor, no por SQL).
-- Fuente de verdad: docs/specs/02-modelo-de-datos.md (actualizar ahi primero).
--
-- Usar este archivo con: Aiven (crear la base "gedenaz" desde Console >
-- Databases > Create database, o usar la base por defecto "defaultdb" que
-- ya viene creada). No lleva CREATE DATABASE ni USE -- pegar esto ya parado
-- adentro de la base correspondiente.
--
-- Es idempotente: se puede volver a ejecutar sobre una base que ya tiene
-- tablas (CREATE TABLE IF NOT EXISTS, indices declarados dentro de la
-- tabla) y solo crea lo que falta. Asi se agregaron venta y detalle_venta
-- a la base existente sin tocar producto.
--
-- Ver docs/specs/05-entorno-desarrollo.md, seccion "Desplegar la base de
-- datos en Aiven" para el paso a paso completo.

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
);

CREATE TABLE IF NOT EXISTS venta (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    fecha_venta  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_venta_fecha (fecha_venta)
);

CREATE TABLE IF NOT EXISTS detalle_venta (
    id               INT AUTO_INCREMENT PRIMARY KEY,
    venta_id         INT NOT NULL,
    producto_id      INT NOT NULL,
    cantidad         INT NOT NULL,
    precio_unitario  DECIMAL(10,2) NOT NULL,
    CONSTRAINT fk_detalle_venta FOREIGN KEY (venta_id) REFERENCES venta (id),
    CONSTRAINT fk_detalle_producto FOREIGN KEY (producto_id) REFERENCES producto (id),
    CONSTRAINT chk_cantidad_positiva CHECK (cantidad > 0)
);
