-- Variante de schema.sql para pegar en la consola MySQL de PythonAnywhere.
-- Fuente de verdad: docs/specs/02-modelo-de-datos.md (actualizar ahi primero).
--
-- Diferencia con schema.sql: en el plan gratis de PythonAnywhere la base de
-- datos NO se crea con CREATE DATABASE por SQL -- se crea desde el boton
-- "New database" del panel (pestana Databases), y su nombre queda prefijado
-- con tu usuario (ej. "tuusuario$gedenaz"). Este archivo asume que esa base
-- ya existe y que la consola MySQL ya esta "parada" adentro de ella (asi
-- abre por defecto la consola de PythonAnywhere), por eso no lleva
-- CREATE DATABASE ni USE.
--
-- Ver docs/specs/05-entorno-desarrollo.md, seccion "Desplegar la base de
-- datos en PythonAnywhere" para el paso a paso completo.

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
