# 06 · Referencia de la API — GedeNaz App

> Contrato HTTP completo de la API (`src/gedenaz/api/`), para quien programe la app Android (framework aún por definir, ver `mobile/README.md`) o cualquier cliente que la consuma. Si el contrato cambia (nuevo endpoint, campo, código de estado), **actualizar este documento primero** (spec-first) antes de tocar el código.

## Base URL

| Entorno | URL |
|---|---|
| Producción | `https://gedenaz-api.onrender.com` |
| Local (desarrollo) | `http://127.0.0.1:5000` (o la IP de tu red local si pruebas desde un dispositivo Android físico/emulador) |

Todas las rutas de este documento son relativas a la base URL. Ej. `POST /productos` en producción es `POST https://gedenaz-api.onrender.com/productos`.

## Generalidades

- **Formato**: todo el cuerpo (request y response) es JSON. Mandar siempre el header `Content-Type: application/json` en requests con body (la mayoría de los clientes HTTP modernos —Retrofit, OkHttp— lo hacen automático al mandar un body JSON).
- **Autenticación**: **ninguna**. No hace falta token ni login — decisión ya tomada, ver [02-modelo-de-datos.md](02-modelo-de-datos.md) (un solo tipo de usuario, sin roles).
- **Fechas y zona horaria**: todas las fechas (`fecha_venta`, `fecha_creacion`, `fecha_actualizacion`) van en formato ISO 8601 **sin** offset explícito (ej. `"2026-09-20T21:57:49"`) y están en **hora de Chile** (`America/Santiago`, con su horario de verano) desde el 2026-09-20. Los filtros `desde`/`hasta` de ventas y reportes se interpretan como días de esa misma zona, así que "ventas de hoy" coincide con el día que ve el usuario. *Excepción histórica*: las filas creadas **antes** del 2026-09-20 (los productos de prueba sembrados el 16-09) tienen sus timestamps en UTC — solo afecta a `fecha_creacion`/`fecha_actualizacion` de esos productos, ninguna regla de negocio depende de ellos.
- **Recomendado — el free tier de Render duerme tras 15 min sin uso** (ver [05-entorno-desarrollo.md](05-entorno-desarrollo.md)): la primera petición después de un rato puede tardar ~1 minuto en responder mientras el servicio despierta. No es un error.

## Envoltorio de error (unificado)

**Toda** respuesta de error, sea cual sea el código de estado, tiene esta misma forma:

```json
{
  "error": {
    "mensaje": "Texto legible, listo para mostrar al usuario.",
    "campos": { "nombre": "El nombre es obligatorio." }
  }
}
```

- `mensaje` (string): siempre presente.
- `campos` (dict o `null`): presente y con contenido en errores de validación (`400`) y en conflictos de stock (`409`) — un mensaje por cada campo/línea problemática (las líneas de una venta se nombran `items[0].cantidad`, `items[1].producto_id`, etc.). En cualquier otro error (ej. `404`) viene como `null`.

Códigos de error que usa la API: `400` (datos inválidos), `404` (no existe), `409` (conflicto con el estado actual — hoy solo: stock insuficiente al registrar una venta), `503` (solo `/health/db`).

Se recomienda para Android: una sola clase/data class para deserializar **cualquier** error de esta API, sin necesitar distinguir la forma según el código de estado.

## Entidad `Producto`

Forma de un producto en las respuestas (ver [02-modelo-de-datos.md](02-modelo-de-datos.md) para el esquema de base de datos):

```json
{
  "id": 38,
  "nombre": "Anillo de plata 925",
  "categoria": "anillo",
  "precio": 15990.0,
  "stock": 12,
  "activo": true,
  "fecha_creacion": "2026-09-16T05:55:03",
  "fecha_actualizacion": "2026-09-16T05:55:03"
}
```

| Campo | Tipo JSON | Notas |
|---|---|---|
| `id` | number (entero) | Asignado por la base, no se manda al crear |
| `nombre` | string | |
| `categoria` | string | Texto libre (ver nota en [02-modelo-de-datos.md](02-modelo-de-datos.md)) |
| `precio` | number (decimal) | > 0 |
| `stock` | number (entero) | ≥ 0 |
| `activo` | boolean | Baja lógica (RF4) — la API solo devuelve/lista productos con `activo: true` |
| `fecha_creacion` | string (ISO 8601) | Asignada por la base |
| `fecha_actualizacion` | string (ISO 8601) | Asignada/actualizada por la base |

---

## Endpoints

### `POST /productos` — RF1, crear producto

**Body** (los 4 campos son obligatorios):

```json
{
  "nombre": "Anillo de plata 925",
  "categoria": "anillo",
  "precio": 15990,
  "stock": 12
}
```

**Éxito**: `201 Created` + el producto creado (ver forma de `Producto` arriba, con `id` y fechas ya asignados).

**Error**: `400 Bad Request` (envoltorio de error) si falta algún campo, el precio no es > 0, o el stock es negativo o no numérico.

### `GET /productos` — RF2, listar / buscar

**Query params (opcionales)**:

| Param | Efecto |
|---|---|
| `nombre` | Filtra por coincidencia parcial en el nombre (insensible a mayúsculas) |
| `categoria` | Filtra por coincidencia parcial en la categoría (insensible a mayúsculas) |

Ejemplo: `GET /productos?categoria=anillo`

**Éxito**: `200 OK` + array de `Producto` (vacío `[]` si no hay resultados — **no** es un error, la app debe mostrar "sin resultados" en ese caso, no un error).

### `GET /productos/<id>` — RF2, detalle

Ejemplo: `GET /productos/38`

**Éxito**: `200 OK` + el `Producto`.

**Error**: `404 Not Found` (envoltorio de error, `campos: null`) si no existe o está dado de baja.

### `PUT /productos/<id>` — RF3, actualizar (reemplazo completo)

**Body**: los 4 campos completos — hay que mandar todos, incluso los que no cambian (misma validación que `POST`). Usar cuando se edita el producto completo (ej. una pantalla de edición con todos los campos precargados).

```json
{
  "nombre": "Anillo de plata 925",
  "categoria": "anillo",
  "precio": 17990,
  "stock": 10
}
```

**Éxito**: `200 OK` + el `Producto` ya actualizado (aunque los valores enviados sean idénticos a los que ya tenía — no hace falta que algo "cambie" de verdad para que sea `200`).

**Errores**: `400` (validación, igual que `POST`) o `404` (no existe / está dado de baja).

### `PATCH /productos/<id>` — RF3, actualizar parcialmente

**Body**: **solo** los campos que quieres cambiar (al menos uno de `nombre`, `categoria`, `precio`, `stock`) — los que no mandes quedan intactos. Pensado para el caso más frecuente de RF3: **ajustar solo el stock** tras una venta, sin tener que reenviar el resto del producto.

```json
{ "stock": 10 }
```

**Éxito**: `200 OK` + el `Producto` completo ya actualizado (todos los campos, no solo los que cambiaste).

**Errores**:
- `400` si no mandas ningún campo reconocido (`{"error": {"mensaje": "...", "campos": {"_general": "Debes enviar al menos un campo..."}}}`), o si alguno de los campos que sí mandaste es inválido (misma regla que en `POST`/`PUT` para ese campo específico).
- `404` si no existe / está dado de baja.

**¿Cuándo `PUT` y cuándo `PATCH`?** `PUT` para una pantalla de "editar producto completo"; `PATCH` para una acción rápida (ej. botones `+`/`-` de stock en un listado) sin tener que abrir/cargar todo el formulario primero.

### `DELETE /productos/<id>` — RF4, eliminar

Ejemplo: `DELETE /productos/38`

> La confirmación ("¿seguro que quieres eliminar?") es responsabilidad de la app — este endpoint ejecuta la baja apenas se lo llama, sin pedir confirmación propia.

**Éxito**: `204 No Content` (sin body).

**Error**: `404 Not Found` si no existe o ya estaba dado de baja.

Es una **baja lógica** (columna `activo`), no un borrado físico — ver [02-modelo-de-datos.md](02-modelo-de-datos.md). El producto deja de aparecer en `GET /productos` y `GET /productos/<id>` inmediatamente después.

---

## Ventas (RF5)

Una **venta** es una cabecera (id, fecha) con una o más **líneas** (producto, cantidad, precio unitario). Forma de una venta en las respuestas:

```json
{
  "id": 1,
  "fecha_venta": "2026-09-20T15:04:05",
  "total": 44970.0,
  "items": [
    { "producto_id": 38, "nombre": "Anillo de plata 925", "cantidad": 2, "precio_unitario": 15990.0, "subtotal": 31980.0 },
    { "producto_id": 41, "nombre": "Aros de perla cultivada", "cantidad": 1, "precio_unitario": 12990.0, "subtotal": 12990.0 }
  ]
}
```

`precio_unitario` es el precio que tenía el producto **en el momento de la venta** — no cambia aunque después se edite el precio del producto. `subtotal = cantidad × precio_unitario`; `total` = suma de subtotales.

### `POST /ventas` — RF5, registrar venta

**Body**: una lista `items` con al menos una línea; cada línea lleva `producto_id` y `cantidad` (enteros ≥ 1). Un mismo producto no puede repetirse en dos líneas.

```json
{
  "items": [
    { "producto_id": 38, "cantidad": 2 },
    { "producto_id": 41, "cantidad": 1 }
  ]
}
```

**Éxito**: `201 Created` + la venta completa (forma de arriba). En la misma operación se descontó el stock de cada producto.

**Errores** (en todos los casos **no se guarda nada**, ni la venta ni el descuento de stock):
- `400` — `items` ausente/vacío, línea mal formada, `cantidad` no entera o < 1, producto repetido, o un `producto_id` que no existe / está dado de baja. `campos` indica la línea: por ejemplo `{"items[1].producto_id": "No existe un producto activo con id 999."}`.
- `409 Conflict` — alguna línea pide más unidades que el stock disponible. `campos` indica cuál: `{"items[0].cantidad": "Stock insuficiente: disponible 3, solicitado 5."}`.

### `GET /ventas/<id>` — RF5, detalle de una venta

**Éxito**: `200 OK` + la venta. **Error**: `404` si no existe.

### `GET /ventas` — RF5, listar ventas

**Query params (opcionales)**: `desde` y `hasta`, fechas `YYYY-MM-DD`, ambas **inclusive** (`hasta=2026-09-20` incluye todo ese día).

**Éxito**: `200 OK` + array de ventas (forma de arriba, con sus `items`), de la más reciente a la más antigua. Sin resultados → `[]`. **Error**: `400` si una fecha no tiene formato `YYYY-MM-DD` o `desde` es posterior a `hasta`.

> Las ventas **no se editan ni se eliminan** (no hay `PUT`/`PATCH`/`DELETE` sobre `/ventas`) — ver RF5 en [01-requisitos-funcionales.md](01-requisitos-funcionales.md).

---

## Reportes (RF3.1)

### `GET /reportes/productos-mas-vendidos` — producto más vendido

Ranking de productos según las ventas registradas.

**Query params (todos opcionales)**:

| Param | Efecto | Por defecto |
|---|---|---|
| `desde`, `hasta` | Limita a ventas de ese rango de fechas (`YYYY-MM-DD`, ambas inclusive) | todo el historial |
| `orden` | `unidades` (más unidades vendidas) o `ingresos` (más dinero generado — aproximación de "más rentable", el sistema no registra costos) | `unidades` |
| `limite` | Cuántos productos devolver (1 a 100) | `10` |

Ejemplo: `GET /reportes/productos-mas-vendidos?desde=2026-09-01&hasta=2026-09-30&limite=5`

**Éxito**: `200 OK` + array ordenado de mayor a menor (el **primer elemento es el más vendido**). Ante un empate desempata el nombre alfabéticamente.

```json
[
  {
    "producto_id": 38,
    "nombre": "Anillo de plata 925",
    "categoria": "anillo",
    "activo": true,
    "unidades_vendidas": 12,
    "ingresos": 191880.0
  }
]
```

- Incluye productos **dados de baja** (`"activo": false`) que tuvieron ventas — es historia de ventas, no inventario.
- `ingresos` suma `cantidad × precio_unitario` con el precio **vigente en cada venta**.
- Sin ventas en el rango → `[]` (no es un error: la app debe mostrar "sin ventas en este período").

**Error**: `400` si `desde`/`hasta` tienen formato inválido, `desde` > `hasta`, `orden` no es uno de los dos valores, o `limite` no es un entero entre 1 y 100.

---

## Endpoints de diagnóstico

### `GET /health`

`200 OK` + `{"status": "ok", "service": "gedenaz-api"}` — confirma que la API está arriba (no prueba la base de datos).

### `GET /health/db`

`200 OK` + `{"status": "ok", "service": "gedenaz-db"}` si logra conectarse a MySQL; `503 Service Unavailable` + `{"status": "error", "detail": "..."}` si falla la conexión.
