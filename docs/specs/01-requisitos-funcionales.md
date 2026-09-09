# 01 · Requisitos Funcionales — GedeNaz App

> Ver [00-vision-y-alcance.md](00-vision-y-alcance.md) para el contexto general. Los campos exactos de "Producto" listados aquí son una propuesta inicial basada en el informe (sección 6.2: nombre, precio, cantidad disponible, categoría); **deben validarse con Gedalias y Nazareth** antes o durante la implementación de RF1 (así lo marca el propio análisis de riesgos del informe). Cuando se confirmen o cambien, actualizar este documento primero.
>
> **Nota (2026-09-09)**: el cliente es una **app Android** que habla con una API (ver [03-arquitectura.md](03-arquitectura.md)), no una app de escritorio con acceso directo a la base. "Formulario"/"pantalla" abajo se refiere a la pantalla Android; las validaciones de campos se hacen tanto en la app (para feedback inmediato) como en la API (porque la app nunca debe ser la única barrera — cualquier llamado directo a la API también debe quedar protegido).

Usuario único del sistema: **administrador** (Gedalias / Nazareth), sin diferenciación de roles ni permisos.

---

## RF1 — Crear producto

**Como** administrador, **quiero** registrar un nuevo producto en el inventario **para** dejar de depender de anotaciones manuales.

**Entrada (formulario "Crear producto")**

| Campo | Tipo | Obligatorio | Regla |
|---|---|---|---|
| Nombre | texto | sí | no vacío |
| Categoría | texto o lista (anillo, collar, pulsera, aro, otro) | sí | no vacío |
| Precio | numérico (decimal, CLP) | sí | > 0 |
| Stock inicial | entero | sí | ≥ 0 |

**Criterios de aceptación**

- No se permite guardar el formulario si falta un campo obligatorio o el tipo de dato es inválido (ver Fase 1.6 de la Carta Gantt: "Validaciones del formulario — campos obligatorios y tipos de dato").
- Precio debe ser numérico positivo; stock inicial debe ser un entero ≥ 0.
- Al guardar exitosamente, el producto queda disponible inmediatamente en RF2 (listado/consulta).
- El usuario recibe confirmación visual de que el producto fue creado (o del error, si aplica).

---

## RF2 — Leer / consultar productos

**Como** administrador, **quiero** ver y buscar los productos del inventario **para** conocer la disponibilidad real sin ir a bodega.

**Funciones**

- Listado completo de productos (nombre, categoría, precio, stock).
- Búsqueda/filtro por **nombre** y por **categoría**.
- Vista de detalle de un producto individual.

**Criterios de aceptación**

- El listado refleja el estado actual de la base de datos (sin caché obsoleta) cada vez que se abre o refresca la pantalla.
- Buscar por un nombre parcial o por categoría reduce correctamente el listado (coincidencia insensible a mayúsculas/minúsculas).
- Si no hay resultados, se informa al usuario en vez de mostrar una lista vacía sin contexto.
- Si el teléfono no tiene conexión o la API no responde, se informa al usuario en vez de mostrar una lista vacía sin contexto (no se distingue de "sin resultados" ante el usuario final).

---

## RF3 — Actualizar producto

**Como** administrador, **quiero** editar los datos de un producto existente y ajustar su stock **para** mantener el inventario al día tras una venta o reposición.

**Funciones**

- Editar nombre, categoría, precio y/o stock de un producto existente.
- Ajuste de stock (incremento/decremento) como parte de la edición.

**Criterios de aceptación**

- El stock resultante nunca puede quedar en negativo (ver Fase 3.2 de la Carta Gantt: "Validaciones de actualización — stock no negativo, campos"); si una edición lo produciría, se rechaza con mensaje claro.
- Los mismos campos obligatorios y tipos de dato de RF1 aplican al editar.
- Tras guardar, los cambios son visibles de inmediato en RF2.

### RF3.1 — Reportes analíticos (fuera de alcance actual)

Generación de reportes de ventas o productos más rentables. Queda como **trabajo futuro**; no se implementa en esta versión (ver [00-vision-y-alcance.md](00-vision-y-alcance.md)). Se documenta aquí solo para trazabilidad con el informe y la Carta Gantt.

---

## RF4 — Eliminar producto

**Como** administrador, **quiero** dar de baja un producto que ya no forma parte del inventario **para** que no aparezca como disponible.

**Criterios de aceptación**

- La eliminación requiere una **confirmación explícita** del usuario antes de ejecutarse (diálogo de confirmación) — no debe haber borrado accidental de un solo clic.
- Tras confirmar, el producto deja de aparecer en el listado (RF2).
- Decisión a validar con el equipo: borrado físico (`DELETE`) vs. baja lógica (columna `activo`/`eliminado`). Ver nota en [02-modelo-de-datos.md](02-modelo-de-datos.md).

---

## Trazabilidad con la Carta Gantt

| Fase Gantt | RF asociado | Hito de entrega |
|---|---|---|
| Fase 1 · Avance #1 | RF1 (Crear) | H2 — Entrega Avance #1 |
| Fase 2 · Avance #2 | RF2 (Leer) | H3 — Entrega Avance #2 |
| Fase 3 · Avance #3 | RF3 + RF4 (Actualizar, Eliminar) | H4 — Avance #3, proyecto funcionalmente terminado |
| Fase 4 · Cierre | Pruebas de regresión, manual de usuario, video demo | H6 — Entrega Informe Final |

Ver detalle completo de fechas y responsables en [04-plan-de-trabajo.md](04-plan-de-trabajo.md).
