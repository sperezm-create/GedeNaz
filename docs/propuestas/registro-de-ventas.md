# Propuesta — Registro de Ventas (RF3.1)

> **Estado: ✅ ADOPTADA por el equipo el 2026-09-20.** Tras presentarla, el equipo aclaró que RF3.1 (producto más vendido) **no es trabajo futuro sino un requerimiento pedido por el cliente**, y aprobó este modelo (cabecera/detalle). Ya se trasladó a las specs oficiales — **la fuente de verdad ahora es** [`01-requisitos-funcionales.md`](../specs/01-requisitos-funcionales.md) (RF3.1 y RF5), [`02-modelo-de-datos.md`](../specs/02-modelo-de-datos.md) y [`06-referencia-api.md`](../specs/06-referencia-api.md). Este documento se conserva como registro del razonamiento original; las secciones de abajo están escritas en el tiempo verbal de cuando aún era una propuesta (p. ej. "no es parte del alcance actual" ya no aplica).
>
> Autor: Nicolas (con apoyo del asistente), 2026-09-16. Nace de una pregunta sobre cómo se manejaría RF3.1 a futuro.
>
> **Revisión 2026-09-16**: la primera versión de esta propuesta asumía una venta = un producto (`venta.producto_id` como FK único). Se corrigió a un modelo de cabecera/detalle para soportar ventas con varios productos (ver más abajo).

## Por qué esto no es parte del alcance actual

El informe entregado (Sección 7.1) marca explícitamente:

> RF3.1 --- Generación de reportes analíticos de ventas o productos más rentables (**queda como trabajo futuro**).

Y la Sección 7.2 excluye "Gestión de pedidos, despacho o seguimiento de compras" del alcance. Hoy el sistema **no tiene ningún registro de ventas**: `producto.stock` es solo un número que se edita a mano en RF3 (Actualizar). Si alguien vende un anillo, el admin resta 1 al stock — y ahí termina el rastro. No queda registrado qué se vendió, a qué precio, ni cuándo.

Esta propuesta es **solo para cuando el equipo decida abordar RF3.1**, no para ahora.

## Diseño propuesto

### Por qué no un campo `id_productos` con una lista de ids

Una venta real (una boleta) puede incluir varios productos — el cliente se lleva un anillo y un collar juntos. La tentación es agregar un campo `id_productos` que guarde algo como `"3,7,12"` en un solo `VARCHAR`. **Se descartó**: eso rompe la primera forma normal (1NF) — no se puede declarar `FOREIGN KEY` sobre una lista serializada, no hay dónde guardar una `cantidad` o `precio_unitario` distinto por producto dentro de la misma venta, y cualquier reporte de RF3.1 ("producto más vendido") tendría que parsear el string a mano en vez de usar SQL normal (`GROUP BY`, `SUM`, índices).

### Dos entidades: `venta` (cabecera) y `detalle_venta` (líneas)

Mismo patrón que una boleta de verdad: la boleta en sí (fecha, folio) es una cosa; cada línea de producto dentro de ella es otra. `venta` no se mezcla con `producto` porque son cosas con ciclos de vida distintos: un producto existe mientras está en el inventario; una venta es un evento puntual en el tiempo que no debería desaparecer ni modificarse después de ocurrir.

```sql
CREATE TABLE venta (
    id                INT AUTO_INCREMENT PRIMARY KEY,
    fecha_venta       DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE detalle_venta (
    id                INT AUTO_INCREMENT PRIMARY KEY,
    venta_id          INT NOT NULL,
    producto_id       INT NOT NULL,
    cantidad          INT NOT NULL,
    precio_unitario   DECIMAL(10,2) NOT NULL,
    FOREIGN KEY (venta_id) REFERENCES venta(id),
    FOREIGN KEY (producto_id) REFERENCES producto(id),
    CONSTRAINT chk_cantidad_positiva CHECK (cantidad > 0)
);
```

Relaciones: una `venta` tiene muchas `detalle_venta` (1 a muchos — una fila por producto distinto en esa boleta); un `producto` puede aparecer en muchas `detalle_venta` a lo largo del tiempo (1 a muchos).

### Decisión de diseño clave: `precio_unitario` sigue siendo una foto, no una referencia

Esto no cambió respecto a la primera versión, solo se movió de `venta` a `detalle_venta`. **No** basta con guardar `producto_id` y calcular el precio consultando `producto.precio` al momento de generar un reporte. Hay que **copiar** el precio vigente al momento exacto de la venta, dentro de la fila de `detalle_venta`.

**Por qué**: si mañana se sube el precio de un anillo, las ventas de la semana pasada tienen que seguir mostrando el precio al que **realmente** se vendieron. Si solo se guardara una referencia a `producto.precio` (el precio actual), cada cambio de precio reescribiría retroactivamente el historial completo de ventas — un reporte de "ingresos de la semana pasada" daría un número distinto según el día en que se consulte, lo cual es incorrecto.

### Cómo se conectaría con lo que ya existe

- **"Registrar una venta" sería una acción nueva, distinta de RF3.** RF3 (Actualizar) debería seguir siendo para correcciones de inventario (ej. "conté mal el stock", "se dañó una pieza") — mezclar eso con ventas sería confuso. "Registrar venta" haría, en **una sola transacción**: insertar 1 fila en `venta` (la cabecera), insertar 1 fila en `detalle_venta` por cada producto vendido, y descontar el stock de cada producto en `producto` — para que nunca queden desincronizados.
- **Los reportes de RF3.1** ("productos más rentables", ingresos, etc.) serían consultas de agregación sobre `detalle_venta`:
  - Producto más vendido: `SUM(cantidad)` agrupado por `producto_id`, ordenado descendente.
  - Ingresos en un período: `SUM(cantidad * precio_unitario)` sobre `detalle_venta` unido a `venta` (para filtrar por `fecha_venta`), o directamente filtrando `detalle_venta` si se agrega `fecha_venta` ahí también (a decidir — ver más abajo).
- **Valida una decisión ya tomada** en `docs/specs/02-modelo-de-datos.md`: usar baja lógica (columna `activo`) en vez de borrado físico para RF4. Si un producto tiene líneas de venta históricas asociadas, un `DELETE` real rompería la relación (`FOREIGN KEY`) o perdería esa historia; con baja lógica, el producto desaparece del inventario visible pero sus ventas pasadas quedan intactas.

## Lo que falta decidir si el equipo adopta esto

- ¿"Registrar venta" es una pantalla nueva en la app Android, o parte del flujo de RF3?
- ¿Se permite anular/corregir una venta ya registrada, o son inmutables (más simple, más realista para un historial)?
- ¿Los reportes (RF3.1) son parte de esta primera versión funcional o quedan para después de tener el registro de ventas funcionando?
- ¿`fecha_venta` vive solo en `venta`, o también se duplica en `detalle_venta` para simplificar los reportes (evitar el `JOIN`)? Duplicarla es una desnormalización deliberada, no un error — común en tablas de detalle pensadas para reportes.
- Impacto en la Carta Gantt: esto es trabajo adicional no contemplado en las fechas actuales — habría que ver dónde encaja sin comprometer los hitos ya comprometidos con el curso.
