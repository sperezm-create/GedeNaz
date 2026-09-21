-- Esquema MySQL de GedeNaz App (para un MySQL propio, con permisos para
-- crear bases de datos -- ej. MySQL local o un servidor donde uno mismo
-- administra la base).
--
-- Si van a usar un host MySQL gestionado en la nube (Aiven, hosting gratis
-- recomendado -- ver docs/specs/05-entorno-desarrollo.md), usen
-- schema_cloud.sql en su lugar: ahi la base se crea desde la consola web
-- del proveedor y no se puede correr CREATE DATABASE por SQL.
--
-- Fuente de verdad: docs/specs/02-modelo-de-datos.md (actualizar ahi primero).
-- Mantener sincronizado con schema_cloud.sql (mismas tablas).
-- Tarea 1.2 de la Carta Gantt (responsable: Francisco Jara).

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
