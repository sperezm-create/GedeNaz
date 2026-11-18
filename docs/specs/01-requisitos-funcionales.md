# 01 · Requisitos Funcionales — GedeNaz App

> Ver [00-vision-y-alcance.md](00-vision-y-alcance.md) para el contexto general. Este documento incluye los campos de producto y venta acordados para esta implementación.

Usuario único del sistema: **administrador** (Gedalias / Nazareth), sin diferenciación de roles ni permisos.

---

## RF1 — Crear producto

**Como** administrador, **quiero** registrar un nuevo producto en el inventario **para** dejar de depender de anotaciones manuales.

**Entrada (formulario "Crear producto")**

| Campo | Tipo | Obligatorio | Regla |
|---|---|---|---|
| Nombre | texto | sí | no vacío |
| Categoría | texto o lista (anillo, collar, pulsera, aro, otro) | sí | no vacío |
| Material | texto | sí | no vacío |
| Talla | texto | sí | no vacío; admite tallas numéricas, medidas y "Única" |
| Precio | numérico (decimal, CLP) | sí | > 0 |
| Stock inicial | entero | sí | ≥ 0 |

**Criterios de aceptación**

- No se permite guardar el formulario si falta un campo obligatorio o el tipo de dato es inválido (ver Fase 1.6 de la Carta Gantt: "Validaciones del formulario — campos obligatorios y tipos de dato").
- Precio debe ser numérico positivo; stock inicial debe ser un entero ≥ 0.
- Al guardar exitosamente, el producto queda disponible inmediatamente en RF2 (listado/consulta).
- La combinación de nombre, categoría, material y talla identifica una variante al reponer stock; las variantes de talla o material distintos no se fusionan.
- El usuario recibe confirmación visual de que el producto fue creado (o del error, si aplica).

---

## RF2 — Leer / consultar productos

**Como** administrador, **quiero** ver y buscar los productos del inventario **para** conocer la disponibilidad real sin ir a bodega.

**Funciones**

- Listado completo de productos (nombre, categoría, material, talla, precio, stock).
- Búsqueda/filtro por **nombre** y por **categoría**.
- Vista de detalle de un producto individual.

**Criterios de aceptación**

- El listado refleja el estado actual de la base de datos (sin caché obsoleta) cada vez que se abre o refresca la pantalla.
- Buscar por un nombre parcial o por categoría reduce correctamente el listado (coincidencia insensible a mayúsculas/minúsculas).
- Si no hay resultados, se informa al usuario en vez de mostrar una lista vacía sin contexto.

---

## RF3 — Actualizar producto

**Como** administrador, **quiero** editar los datos de un producto existente y ajustar su stock **para** mantener el inventario al día tras una venta o reposición.

**Funciones**

- Editar nombre, categoría, material, talla, precio y/o stock de un producto existente.
- Ajuste de stock (incremento/decremento) como parte de la edición.

**Criterios de aceptación**

- El stock resultante nunca puede quedar en negativo (ver Fase 3.2 de la Carta Gantt: "Validaciones de actualización — stock no negativo, campos"); si una edición lo produciría, se rechaza con mensaje claro.
- Los mismos campos obligatorios y tipos de dato de RF1 aplican al editar.
- Tras guardar, los cambios son visibles de inmediato en RF2.

---

## RF4 — Eliminar producto

**Como** administrador, **quiero** dar de baja un producto que ya no forma parte del inventario **para** que no aparezca como disponible.

**Criterios de aceptación**

- La eliminación requiere una **confirmación explícita** del usuario antes de ejecutarse (diálogo de confirmación) — no debe haber borrado accidental de un solo clic.
- Tras confirmar, el producto deja de aparecer en el listado (RF2).
- Decisión a validar con el equipo: borrado físico (`DELETE`) vs. baja lógica (columna `activo`/`eliminado`). Ver nota en [02-modelo-de-datos.md](02-modelo-de-datos.md).

## RF5 — Registrar ventas y emitir boleta interna

**Como** administrador, **quiero** seleccionar productos del inventario por su código, indicar cantidades y confirmar la venta **para** emitir un comprobante y mantener el stock actualizado.

**Criterios de aceptación**

- Cada producto se identifica en la app con un código estable derivado de su ID (`GN-000001`).
- Solo se puede vender un producto activo con stock suficiente; las cantidades deben ser enteros positivos.
- La confirmación registra la venta y sus líneas con precio/nombre de venta, número de boleta interno y fecha; descuenta el stock en la misma operación.
- En cada línea se registra si el producto fue comprado para un hombre o una mujer. Cada línea conserva como historial el material y talla vigentes al momento de la venta.
- La fecha y hora de cada venta se registran juntas con precisión de segundos.
- Si el registro falla o falta stock, no se registra una venta parcial ni se descuenta parcialmente el stock.
- La boleta interna se muestra al confirmar la venta. No reemplaza una boleta tributaria ni procesa pagos.
- Al confirmar, se puede registrar como pago completo o crear un plan de cuotas sin interés, con frecuencia configurable (semanal, quincenal o mensual), entre 2 y 120 cuotas y fecha del primer vencimiento.
- El total se divide entre las cuotas y cualquier diferencia de redondeo se asigna a la última cuota. Cada cuota puede recibir varios abonos parciales; se conserva fecha y monto de cada abono.
- En el historial y la gestión de pagos se muestran el monto pagado, el saldo pendiente, el estado de cada cuota y su próximo vencimiento. No se permite abonar más que el saldo de la cuota.
- Una venta que ya tenga abonos registrados no se puede anular hasta resolver esos pagos fuera del sistema; el sistema debe informar claramente ese límite y no alterar el stock ni el historial financiero.
- El administrador puede anular una boleta completa con confirmación; la operación devuelve todas sus unidades al stock, conserva la boleta marcada como anulada y excluye sus líneas de estadísticas. Una boleta no se puede anular dos veces.

## RF6 — Consultar productos más vendidos

**Como** administrador, **quiero** ver las unidades vendidas por producto **para** identificar cuáles tienen mayor demanda.

**Criterios de aceptación**

- La estadística se calcula desde ventas vigentes, muestra unidades vendidas y se ordena de mayor a menor; las boletas anuladas no cuentan.
- Muestra unidades vendidas por categoría y su porcentaje sobre todas las unidades vendidas vigentes.
- Muestra los precios unitarios agrupados y ordenados de mayor a menor cantidad de unidades vendidas para identificar el precio más frecuente.
- Para cada producto, muestra las unidades vendidas por talla y destinatario (Hombre o Mujer), ordenadas por producto y cantidad; las boletas anuladas y destinatarios no especificados no cuentan.
- El historial y las estadísticas se actualizan después de confirmar una venta.

## RF8 — Consultar resumen mensual de ventas

**Como** administrador, **quiero** conocer cuántas ventas vigentes se realizaron y cuánto ingreso generaron en un mes **para** revisar el desempeño mensual del negocio.

**Criterios de aceptación**

- La pestaña de estadísticas muestra el número de ventas y la suma de sus totales para el mes y año actuales.
- Incluye una sección de historial mensual con cantidad de ventas e ingresos para cada mes/año que tenga ventas vigentes, ordenada desde el período más reciente al más antiguo.
- El resumen se actualiza al refrescar las estadísticas o registrar/anular una venta.
- Las ventas anuladas no cuentan ni suman ingresos.
- La API permite consultar el resumen para un año y mes específicos y el historial de todos los meses con ventas.

## RF7 — Consultar calendario e historial de ventas

**Como** administrador, **quiero** consultar las ventas en un calendario por año, mes, día y hora **para** encontrar rápidamente una venta y revisar lo vendido.

**Criterios de aceptación**

- El calendario permite filtrar por año y mes, elegir un día y filtrar sus ventas por hora.
- Los días con ventas vigentes muestran su cantidad; el detalle del día muestra hora, boleta, total y cantidad de unidades. Las ventas anuladas no aparecen en el calendario.
- Al abrir una venta se presenta la fecha/hora completa y cada producto con material, talla y destinatario.
- Las ventas anuladas permanecen consultables y claramente identificadas en el historial, pero no aparecen en el calendario ni se suman a las estadísticas.
- El selector de año incluye el año actual y los años con ventas vigentes; al cambiar de año, el calendario continúa usando las fechas y días correctos.

---

## Trazabilidad con la Carta Gantt

| Fase Gantt | RF asociado | Hito de entrega |
|---|---|---|
| Fase 1 · Avance #1 | RF1 (Crear) | H2 — Entrega Avance #1 |
| Fase 2 · Avance #2 | RF2 (Leer) | H3 — Entrega Avance #2 |
| Fase 3 · Avance #3 | RF3 + RF4 (Actualizar, Eliminar) | H4 — Avance #3, proyecto funcionalmente terminado |
| Fase 4 · Cierre | Pruebas de regresión, manual de usuario, video demo | H6 — Entrega Informe Final |

Ver detalle completo de fechas y responsables en [04-plan-de-trabajo.md](04-plan-de-trabajo.md).
