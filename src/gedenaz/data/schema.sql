-- Esquema MySQL de GedeNaz App (para un MySQL propio, con permisos para
-- crear bases de datos -- ej. MySQL local o un servidor donde uno mismo
-- administra la base).
--
-- Si van a usar PythonAnywhere (hosting gratis recomendado, ver
-- docs/specs/05-entorno-desarrollo.md), usen schema_pythonanywhere.sql en
-- su lugar: ahi el nombre de la base lo asigna PythonAnywhere y no se puede
-- correr CREATE DATABASE por SQL.
--
-- Fuente de verdad: docs/specs/02-modelo-de-datos.md (actualizar ahi primero).
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
    CONSTRAINT chk_stock_no_negativo CHECK (stock >= 0)
);

CREATE INDEX idx_producto_nombre ON producto (nombre);
CREATE INDEX idx_producto_categoria ON producto (categoria);
