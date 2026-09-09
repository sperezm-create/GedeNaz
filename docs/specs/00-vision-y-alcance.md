# 00 · Visión y Alcance — GedeNaz App

> Fuente: `Informe propuesta Proyecto GedeNaz.docx` (Grupo N°6, Taller Sistemas de Información INFB8082, 09-09-2026).
> Este documento y los siguientes en `docs/specs/` son la fuente de verdad técnica del proyecto. Cualquier cambio de alcance o requisitos se discute y refleja primero aquí, antes de tocar código (spec-first).
>
> **⚠️ Corrección de alcance (2026-09-09, posterior a la entrega del informe)**: el equipo decidió que GedeNaz App **no es una aplicación de escritorio, es una aplicación móvil para Android**. El informe ya entregado dice "aplicación de escritorio" — ese texto queda desactualizado a partir de esta decisión; ver [BITACORA.md](../BITACORA.md) para el detalle de cuándo y por qué se corrigió. Se mantiene **Python + MySQL** como pidió el equipo, pero MySQL ahora vive detrás de una API (ver [03-arquitectura.md](03-arquitectura.md)) en vez de ser accedido directo por la app, porque un cliente móvil no debe guardar credenciales de base de datos.

## Resumen

GedeNaz App es una **aplicación móvil para Android**, con un backend en **Python** y **MySQL** como base de datos, para la empresa GedeNaz (comercialización de joyas y accesorios). Permite a sus dos administradores, **Gedalias** y **Nazareth**, gestionar el inventario mediante las cuatro operaciones CRUD (crear, leer, actualizar, eliminar) sobre una base de datos centralizada, reemplazando los registros manuales (cuadernos/planillas) actualmente en uso. La centralización es el punto clave: ambos administradores deben ver el mismo inventario en tiempo real desde sus propios teléfonos, por eso los datos no viven solo en el dispositivo (ver [El problema](#el-problema)).

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

Desarrollar una aplicación móvil para Android para GedeNaz, con backend en Python y MySQL, que permita a sus administradores gestionar de manera eficiente el inventario de joyas mediante creación, consulta, actualización y eliminación de productos.

## Objetivos específicos

1. Analizar el proceso actual de registro y control de inventario para identificar falencias y requerimientos funcionales.
2. Diseñar la arquitectura de la solución (app Android + API en Python + modelo de datos en MySQL) que soporte las cuatro operaciones CRUD.
3. Implementar y validar mediante pruebas funcionales las cuatro operaciones, asegurando el correcto funcionamiento antes de la entrega final.

## Alcance — dentro (ver detalle en [01-requisitos-funcionales.md](01-requisitos-funcionales.md))

| ID | Operación | Descripción breve |
|----|-----------|--------------------|
| RF1 | Crear | Registrar nuevos productos (nombre, precio, stock inicial, categoría) |
| RF2 | Leer | Listar, buscar/filtrar por nombre o categoría, ver detalle |
| RF3 | Actualizar | Editar datos de un producto y ajustar stock |
| RF3.1 | Reportes | Reportes analíticos de ventas/productos más rentables — **trabajo futuro, fuera del alcance actual** |
| RF4 | Eliminar | Dar de baja productos, con confirmación |

## Alcance — fuera

- Venta o comercialización en línea (e-commerce).
- Pasarelas o integración de métodos de pago.
- Catálogo público para clientes finales.
- Gestión de pedidos, despacho o seguimiento de compras.
- Multiusuario con roles diferenciados (solo existe el rol "administrador").
- Reportes analíticos (RF3.1) en esta primera versión.

El alcance se acotó deliberadamente a las 4 operaciones CRUD, considerando el tiempo disponible del semestre y que GedeNaz es administrada por solo dos personas: se prioriza una solución simple, mantenible y realmente utilizable por el negocio.

## Consecuencias esperadas del sistema

- Elimina los registros manuales del inventario, reduciendo errores de digitación y descuadres entre lo registrado y el stock real.
- Gedalias y Nazareth consultan y actualizan el mismo inventario centralizado en MySQL desde sus propios teléfonos, sin depender de comunicarse para confirmar disponibilidad.
- Mejora la eficiencia operativa (menos tiempo buscando/verificando en bodega) y la confiabilidad de los datos para decisiones diarias.
- Deja una base ordenada para incorporar a futuro reportes de ventas o de productos más rentables (RF3.1).

## Documentos relacionados

- [01-requisitos-funcionales.md](01-requisitos-funcionales.md) — detalle y criterios de aceptación de RF1–RF4.
- [02-modelo-de-datos.md](02-modelo-de-datos.md) — entidad Producto y esquema MySQL.
- [03-arquitectura.md](03-arquitectura.md) — arquitectura de capas, stack tecnológico, estructura del repo.
- [04-plan-de-trabajo.md](04-plan-de-trabajo.md) — fases, hitos y roles (derivado de la Carta Gantt).
- [05-entorno-desarrollo.md](05-entorno-desarrollo.md) — cómo levantar el entorno de desarrollo (entorno virtual, dependencias, MySQL).
