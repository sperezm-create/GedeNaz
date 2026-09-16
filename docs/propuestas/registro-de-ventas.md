# Propuesta — Registro de Ventas (RF3.1)

> **Estado: propuesta, no decidida.** Este documento es una nota de diseño para discutir con el equipo, no forma parte del alcance actual del proyecto. Si el equipo decide adoptarla, se traslada primero a `docs/specs/01-requisitos-funcionales.md` y `docs/specs/02-modelo-de-datos.md` (spec-first) antes de programar nada — igual que se hizo con el cambio a Android.
>
> Autor: Nicolas (con apoyo del asistente), 2026-09-16. Nace de una pregunta sobre cómo se manejaría RF3.1 a futuro.

## Por qué esto no es parte del alcance actual

El informe entregado (Sección 7.1) marca explícitamente:

> RF3.1 --- Generación de reportes analíticos de ventas o productos más rentables (**queda como trabajo futuro**).

Y la Sección 7.2 excluye "Gestión de pedidos, despacho o seguimiento de compras" del alcance. Hoy el sistema **no tiene ningún registro de ventas**: `producto.stock` es solo un número que se edita a mano en RF3 (Actualizar). Si alguien vende un anillo, el admin resta 1 al stock — y ahí termina el rastro. No queda registrado qué se vendió, a qué precio, ni cuándo.

Esta propuesta es **solo para cuando el equipo decida abordar RF3.1**, no para ahora.

## Diseño propuesto

### Una entidad nueva, separada de `producto`

`venta` no se mezcla con `producto` porque son cosas con ciclos de vida distintos: un producto existe mientras está en el inventario; una venta es un evento puntual en el tiempo que no debería desaparecer ni modificarse después de ocurrir.

```sql
CREATE TABLE venta (
    id                INT AUTO_INCREMENT PRIMARY KEY,
    producto_id       INT NOT NULL,
    cantidad          INT NOT NULL,
    precio_unitario   DECIMAL(10,2) NOT NULL,
    fecha_venta       DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (producto_id) REFERENCES producto(id),
    CONSTRAINT chk_cantidad_positiva CHECK (cantidad > 0)
);
```

Relación: un `producto` puede tener muchas `venta` asociadas (1 a muchos).

### Decisión de diseño clave: `precio_unitario` es una foto, no una referencia

**No** basta con guardar `producto_id` y calcular el precio consultando `producto.precio` al momento de generar un reporte. Hay que **copiar** el precio vigente al momento exacto de la venta, dentro de la fila de `venta`.

**Por qué**: si mañana se sube el precio de un anillo, las ventas de la semana pasada tienen que seguir mostrando el precio al que **realmente** se vendieron. Si solo se guardara una referencia a `producto.precio` (el precio actual), cada cambio de precio reescribiría retroactivamente el historial completo de ventas — un reporte de "ingresos de la semana pasada" daría un número distinto según el día en que se consulte, lo cual es incorrecto.

### Cómo se conectaría con lo que ya existe

- **"Registrar una venta" sería una acción nueva, distinta de RF3.** RF3 (Actualizar) debería seguir siendo para correcciones de inventario (ej. "conté mal el stock", "se dañó una pieza") — mezclar eso con ventas sería confuso. "Registrar venta" haría **dos cosas en una sola transacción**: insertar la fila en `venta` y descontar el stock en `producto`, para que nunca queden desincronizados.
- **Los reportes de RF3.1** ("productos más rentables", ingresos, etc.) serían consultas de agregación sobre `venta`:
  - Producto más vendido: `SUM(cantidad)` agrupado por `producto_id`, ordenado descendente.
  - Ingresos en un período: `SUM(cantidad * precio_unitario)`, filtrado por rango de `fecha_venta`.
- **Valida una decisión ya tomada** en `docs/specs/02-modelo-de-datos.md`: usar baja lógica (columna `activo`) en vez de borrado físico para RF4. Si un producto tiene ventas históricas asociadas, un `DELETE` real rompería la relación (`FOREIGN KEY`) o perdería esa historia; con baja lógica, el producto desaparece del inventario visible pero sus ventas pasadas quedan intactas.

## Lo que falta decidir si el equipo adopta esto

- ¿"Registrar venta" es una pantalla nueva en la app Android, o parte del flujo de RF3?
- ¿Se permite anular/corregir una venta ya registrada, o son inmutables (más simple, más realista para un historial)?
- ¿Los reportes (RF3.1) son parte de esta primera versión funcional o quedan para después de tener el registro de ventas funcionando?
- Impacto en la Carta Gantt: esto es trabajo adicional no contemplado en las fechas actuales — habría que ver dónde encaja sin comprometer los hitos ya comprometidos con el curso.
