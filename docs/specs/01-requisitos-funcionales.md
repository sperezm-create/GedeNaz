# 01 · Requisitos Funcionales — GedeNaz App

> Ver [00-vision-y-alcance.md](00-vision-y-alcance.md) para el contexto general. Los campos exactos de "Producto" listados aquí son una propuesta inicial basada en el informe (sección 6.2: nombre, precio, cantidad disponible, categoría); **deben validarse con Gedalias y Nazareth** antes o durante la implementación de RF1 (así lo marca el propio análisis de riesgos del informe). Cuando se confirmen o cambien, actualizar este documento primero.
>
> **Nota (2026-09-09)**: el cliente es una **app Android** que habla con una API (ver [03-arquitectura.md](03-arquitectura.md)), no una app de escritorio con acceso directo a la base. "Formulario"/"pantalla" abajo se refiere a la pantalla Android; las validaciones de campos se hacen tanto en la app (para feedback inmediato) como en la API (porque la app nunca debe ser la única barrera — cualquier llamado directo a la API también debe quedar protegido).
>
> **Contrato HTTP completo** (endpoints, formato exacto de cada request/response, formato de errores): [06-referencia-api.md](06-referencia-api.md).

Usuario único del sistema: **administrador** (Gedalias / Nazareth), sin diferenciación de roles ni permisos.

---

## RF1 — Crear producto

**Como** administrador, **quiero** registrar un nuevo producto en el inventario **para** dejar de depender de anotaciones manuales.

> ✅ **Backend implementado y en producción** (2026-09-16): `POST /productos` (`src/gedenaz/api/productos.py`), validaciones (`src/gedenaz/logic/productos.py`) y guardado en MySQL (`src/gedenaz/data/productos.py`), probado end-to-end contra Aiven, incluido en `https://gedenaz-api.onrender.com/productos`. Falta la pantalla Android (tarea 1.4, depende del framework — ver `mobile/README.md`).

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

> ✅ **Backend implementado y en producción** (2026-09-16): `GET /productos` (lista, con filtros opcionales `?nombre=` y `?categoria=`, coincidencia parcial insensible a mayúsculas) y `GET /productos/<id>` (detalle, `404` si no existe), en `src/gedenaz/api/productos.py`. Solo devuelve productos activos (baja lógica de RF4). Falta la pantalla Android (tarea 2.1/2.4, depende del framework).

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

> ✅ **Backend implementado y en producción** (2026-09-16): dos endpoints — `PUT /productos/<id>` (reemplazo completo, los 4 campos) y `PATCH /productos/<id>` (actualización parcial, solo los campos enviados — pensado para el caso más común: ajustar el stock sin reenviar todo el producto). Ambos reusan las mismas reglas de validación por campo que RF1 (`400` si son inválidas, `404` si el producto no existe/está inactivo). Detalle completo con ejemplos: [06-referencia-api.md](06-referencia-api.md). Falta la pantalla Android (tarea 2.5, depende del framework).

**Funciones**

- Editar nombre, categoría, precio y/o stock de un producto existente.
- Ajuste de stock (incremento/decremento) como parte de la edición.

**Criterios de aceptación**

- El stock resultante nunca puede quedar en negativo (ver Fase 3.2 de la Carta Gantt: "Validaciones de actualización — stock no negativo, campos"); si una edición lo produciría, se rechaza con mensaje claro.
- Los mismos campos obligatorios y tipos de dato de RF1 aplican al editar.
- Tras guardar, los cambios son visibles de inmediato en RF2.

### RF3.1 — Producto más vendido (reporte)

> **Dentro del alcance desde 2026-09-20.** El informe lo listaba como "trabajo futuro", pero el equipo aclaró que es un requerimiento **pedido por el cliente** (ver [00-vision-y-alcance.md](00-vision-y-alcance.md)). Depende de RF5 (sin ventas registradas no hay qué reportar).

**Como** administrador, **quiero** saber qué producto se vende más **para** decidir qué reponer y detectar los de mayor rotación (el problema que hoy no se puede resolver con cuadernos).

> ✅ **Backend implementado** (2026-09-20): `GET /reportes/productos-mas-vendidos` (`src/gedenaz/api/reportes.py`), con `desde`, `hasta`, `orden` (`unidades` | `ingresos`) y `limite` (1–100, por defecto 10). Contrato con ejemplos en [06-referencia-api.md](06-referencia-api.md). Falta la pantalla Android. Pendiente de llevar a producción con "Manual Deploy" en Render.

**Funciones**

- Ranking de productos por **unidades vendidas** (de mayor a menor), calculado sobre las ventas registradas (RF5).
- Filtro opcional por **rango de fechas** (`desde` / `hasta`, ambos inclusive, por día).
- Cada fila del ranking incluye: producto, categoría, unidades vendidas e ingresos generados.
- Orden alternativo por **ingresos** — la aproximación de "productos más rentables" del informe: no se registra el costo de los productos, así que no se puede calcular ganancia real.

**Criterios de aceptación**

- El primer elemento del ranking es el producto más vendido del período consultado; ante un empate en unidades, desempata el nombre (orden alfabético, para que el resultado sea estable).
- Los productos **dados de baja** que tuvieron ventas siguen apareciendo (es historia de ventas, no inventario actual).
- Los ingresos usan el **precio al momento de cada venta**, no el precio actual del producto (ver RF5 y [02-modelo-de-datos.md](02-modelo-de-datos.md)).
- Sin ventas en el período, el resultado es una lista vacía (no un error). La app debe mostrar "sin ventas en este período".
- Un rango inválido (fecha mal escrita, o `desde` posterior a `hasta`) se rechaza con un error de validación.

---

## RF5 — Registrar venta

> **Requisito de apoyo de RF3.1** — no figura en el informe original. Se agrega porque el reporte necesita datos de origen: hoy el sistema solo guarda el stock actual y ninguna venta deja rastro.

**Como** administrador, **quiero** registrar una venta (uno o varios productos) **para** que el stock se descuente automáticamente y quede el historial de qué se vendió, a qué precio y cuándo.

> ✅ **Backend implementado** (2026-09-20): `POST /ventas`, `GET /ventas` (filtro `desde`/`hasta`) y `GET /ventas/<id>` (`src/gedenaz/api/ventas.py`). Stock insuficiente responde `409`; datos inválidos o producto inexistente, `400` nombrando la línea (`items[1].cantidad`). Cubierto por un test de concurrencia (dos ventas simultáneas de la última unidad: una gana, la otra recibe "sin stock"). Contrato con ejemplos en [06-referencia-api.md](06-referencia-api.md). Falta la pantalla Android. Pendiente de llevar a producción con "Manual Deploy" en Render.

**Entrada**: una lista de líneas, cada una con `producto_id` y `cantidad` (una venta puede llevar varios productos distintos, como una boleta real).

**Criterios de aceptación**

- La venta debe tener **al menos una línea**. Cada `producto_id` debe existir y estar activo; cada `cantidad` es un entero ≥ 1; **no se repite** un mismo producto en dos líneas de la misma venta.
- **No se puede vender más que el stock disponible**: si alguna línea lo excede, la venta completa se rechaza y **no cambia nada** (ni stock ni registros).
- La venta se guarda **en bloque, todo o nada**: la cabecera, todas sus líneas y el descuento de stock ocurren en una sola transacción — nunca queda una venta a medias ni un stock descuadrado.
- Cada línea guarda el **precio unitario vigente en ese instante** (una "foto"): si después cambia el precio del producto, las ventas ya registradas no se alteran.
- Al éxito, se devuelve la venta completa: id, fecha, líneas (con nombre, cantidad, precio unitario y subtotal) y total.
- Las ventas se pueden **consultar** (una por id, o el listado con filtro por rango de fechas) pero **no se editan ni se eliminan** en esta versión. Si hubo un error al registrar, hoy la corrección es manual (ajustar el stock con RF3); la venta errónea queda en el historial — límite conocido, anular ventas queda fuera de alcance.
- RF5 es una acción **distinta de RF3**: RF3 sigue siendo para correcciones de inventario ("conté mal el stock"), no para registrar ventas.

> Origen del diseño: [`docs/propuestas/registro-de-ventas.md`](../propuestas/registro-de-ventas.md) (adoptada por el equipo el 2026-09-20).

---

## RF4 — Eliminar producto

**Como** administrador, **quiero** dar de baja un producto que ya no forma parte del inventario **para** que no aparezca como disponible.

> ✅ **Backend implementado y en producción** (2026-09-16): `DELETE /productos/<id>` (`src/gedenaz/api/productos.py`) — `204` si se dio de baja, `404` si no existía o ya estaba inactivo. Falta la pantalla Android con el diálogo de confirmación (criterio de aceptación de abajo) — **la confirmación es responsabilidad de la UI**, la API solo ejecuta la baja cuando la llaman, sin pedir confirmación propia.

**Criterios de aceptación**

- La eliminación requiere una **confirmación explícita** del usuario antes de ejecutarse (diálogo de confirmación) — no debe haber borrado accidental de un solo clic.
- Tras confirmar, el producto deja de aparecer en el listado (RF2).
- ✅ Decidido e implementado: **baja lógica** (columna `activo`, no `DELETE` físico) — ver [02-modelo-de-datos.md](02-modelo-de-datos.md). Sigue pendiente de validar con la empresa (Gedalias/Nazareth) si este comportamiento (el producto "desaparece" pero sus datos no se pierden) es el esperado.

---

## Trazabilidad con la Carta Gantt

| Fase Gantt | RF asociado | Hito de entrega |
|---|---|---|
| Fase 1 · Avance #1 | RF1 (Crear) | H2 — Entrega Avance #1 |
| Fase 2 · Avance #2 | RF2 (Leer) | H3 — Entrega Avance #2 |
| Fase 3 · Avance #3 | RF3 + RF3.1 + RF4 (Actualizar, Reporte de producto más vendido, Eliminar) | H4 — Avance #3, proyecto funcionalmente terminado |
| _(fuera del Gantt oficial)_ | RF5 (Registrar venta) — prerrequisito de RF3.1 | Se adelanta junto con RF3.1; el Gantt no lo lista como tarea propia |
| Fase 4 · Cierre | Pruebas de regresión, manual de usuario, video demo | H6 — Entrega Informe Final |

Ver detalle completo de fechas y responsables en [04-plan-de-trabajo.md](04-plan-de-trabajo.md).
