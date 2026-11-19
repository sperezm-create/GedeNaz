# 00 · Visión y Alcance — GedeNaz App

> Fuente: `Informe propuesta Proyecto GedeNaz.docx` (Grupo N°6, Taller Sistemas de Información INFB8082, 09-09-2026).
> Este documento y los siguientes en `docs/specs/` son la fuente de verdad técnica del proyecto. Cualquier cambio de alcance o requisitos se discute y refleja primero aquí, antes de tocar código (spec-first).

## Resumen

GedeNaz App es una **aplicación de escritorio** construida en **Python**, con **MySQL** como base de datos, para la empresa GedeNaz (comercialización de joyas y accesorios). Permite a sus dos administradores, **Gedalias** y **Nazareth**, gestionar el inventario mediante las cuatro operaciones CRUD (crear, leer, actualizar, eliminar) sobre una base de datos centralizada, reemplazando los registros manuales (cuadernos/planillas) actualmente en uso.

## La empresa

- **GedeNaz**: pyme dedicada a la comercialización directa de joyas y accesorios (anillos, collares, pulseras, aros, otros).
- **Estructura**: administrada exclusivamente por sus dos propietarios, sin personal adicional dedicado a tareas administrativas.
- **Tipos de usuario del sistema**: uno solo — *administrador* (Gedalias y Nazareth comparten el mismo rol y acceso).

## El problema

Hoy el inventario se controla en cuadernos/planillas no centralizadas ni sincronizadas entre ambos administradores:

- Dependencia de la memoria para actualizar registros.
- Errores de digitación y duplicidad de registros.
- Descuadres de stock que exigen verificación física constante en bodega.
- Gedalias y Nazareth pueden manejar información distinta sobre un mismo producto.
- No existe forma de detectar qué productos tienen mayor rotación.

Flujo actual: `ingreso de producto → registro escrito → venta/ajuste de stock → actualización manual (si se recuerda) → verificación física en bodega ante dudas`.

## Objetivo general

Desarrollar una aplicación de escritorio para GedeNaz, usando Python y MySQL, que permita a sus administradores gestionar el inventario, registrar ventas con boletas internas y consultar los productos más vendidos.

## Objetivos específicos

1. Analizar el proceso actual de registro y control de inventario para identificar falencias y requerimientos funcionales.
2. Diseñar la arquitectura de la solución (interfaz en Python + modelo de datos en MySQL) para inventario, ventas y estadísticas.
3. Implementar y validar mediante pruebas funcionales la gestión de productos y ventas.

## Alcance — dentro (ver detalle en [01-requisitos-funcionales.md](01-requisitos-funcionales.md))

| ID | Operación | Descripción breve |
|----|-----------|--------------------|
| RF1 | Crear | Registrar nuevos productos (nombre, precio, stock inicial, categoría) |
| RF2 | Leer | Listar, buscar/filtrar por nombre o categoría, ver detalle |
| RF3 | Actualizar | Editar datos de un producto y ajustar stock |
| RF4 | Eliminar | Dar de baja productos, con confirmación |
| RF5 | Ventas | Registrar ventas desde el inventario, emitir una boleta interna y descontar stock |
| RF6 | Estadísticas | Consultar productos más vendidos a partir de las ventas registradas |

## Alcance — fuera

- Venta o comercialización en línea (e-commerce).
- Pasarelas o integración de métodos de pago.
- Catálogo público para clientes finales.
- Gestión de pedidos, despacho o seguimiento de compras.
- Multiusuario con roles diferenciados (solo existe el rol "administrador").
- Emisión de documentos tributarios electrónicos. La boleta de esta versión es un comprobante interno de la app.
- Reportes de rentabilidad avanzados; las estadísticas de unidades vendidas de RF6 sí están incluidas.

El alcance prioriza una solución simple, mantenible y realmente utilizable por el negocio: inventario, registro interno de ventas y estadísticas de unidades vendidas.

## Consecuencias esperadas del sistema

- Elimina los registros manuales del inventario, reduciendo errores de digitación y descuadres entre lo registrado y el stock real.
- Gedalias y Nazareth consultan y actualizan el mismo inventario centralizado en MySQL, sin depender de comunicarse para confirmar disponibilidad.
- Mejora la eficiencia operativa (menos tiempo buscando/verificando en bodega) y la confiabilidad de los datos para decisiones diarias.
- Permite identificar los productos con mayor demanda a partir de las ventas registradas; análisis de rentabilidad queda para una etapa futura.

## Documentos relacionados

- [01-requisitos-funcionales.md](01-requisitos-funcionales.md) — detalle y criterios de aceptación de RF1–RF6.
- [02-modelo-de-datos.md](02-modelo-de-datos.md) — productos, ventas y esquema MySQL.
- [03-arquitectura.md](03-arquitectura.md) — arquitectura de capas, stack tecnológico, estructura del repo.
- [04-plan-de-trabajo.md](04-plan-de-trabajo.md) — fases, hitos y roles (derivado de la Carta Gantt).
- [05-entorno-desarrollo.md](05-entorno-desarrollo.md) — cómo levantar el entorno de desarrollo (entorno virtual, dependencias, MySQL).
