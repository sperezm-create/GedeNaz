# 02 · Modelo de Datos — GedeNaz App

> Propuesta inicial de esquema MySQL a partir del informe (sección 6.2 y RF1, [01-requisitos-funcionales.md](01-requisitos-funcionales.md)). A validar/ajustar con la empresa y con quien implemente la capa de datos (Fase 1.2, Carta Gantt).

## Entidad: `producto`

Única entidad requerida por el alcance actual (RF1–RF4). No hay entidad "usuario" en base de datos: el sistema tiene un único tipo de usuario (administrador) y no se especificó autenticación en el informe — se documenta como pregunta abierta más abajo.

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
    CONSTRAINT chk_stock_no_negativo CHECK (stock >= 0)
);

CREATE INDEX idx_producto_nombre ON producto (nombre);
CREATE INDEX idx_producto_categoria ON producto (categoria);
```

Este script vivirá en `src/gedenaz/data/schema.sql` (Fase 1.2 de la Carta Gantt, responsable: Francisco Jara).

## Decisiones de diseño a confirmar con el equipo/empresa

1. **Baja lógica vs. física en RF4**: se propone `activo` (baja lógica) para no perder historial y evitar el riesgo de "Análisis de Riesgos" del informe (pérdida de datos por mala configuración de BD). RF2 (listar) debe filtrar por `activo = 1` por defecto.
2. **Autenticación**: el informe no pide login (un único tipo de usuario, sin roles). Se asume que la app no implementa autenticación en esta versión. Si el equipo decide agregarla, documentar aquí primero.
3. **Categorías**: el informe menciona anillos, collares, pulseras, aros "y otros accesorios" como ejemplos, no como lista cerrada. Se modela `categoria` como texto libre en vez de tabla/catálogo aparte, para mantener el alcance simple; revisar si el equipo prefiere una tabla `categoria` normalizada.
