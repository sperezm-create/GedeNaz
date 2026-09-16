-- Variante de schema.sql para hosts MySQL gestionados donde la base ya
-- viene creada (o se crea desde la consola web del proveedor, no por SQL).
-- Fuente de verdad: docs/specs/02-modelo-de-datos.md (actualizar ahi primero).
--
-- Usar este archivo con: Aiven (crear la base "gedenaz" desde Console >
-- Databases > Create database, o usar la base por defecto "defaultdb" que
-- ya viene creada). No lleva CREATE DATABASE ni USE -- pegar esto ya parado
-- adentro de la base correspondiente.
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
    CONSTRAINT chk_stock_no_negativo CHECK (stock >= 0)
);

CREATE INDEX idx_producto_nombre ON producto (nombre);
CREATE INDEX idx_producto_categoria ON producto (categoria);
