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
- **Zona horaria**: todas las fechas (`fecha_creacion`, `fecha_actualizacion`) son `DATETIME` de MySQL en formato ISO 8601 sin offset de zona horaria explícito (ej. `"2026-09-16T05:55:03"`), en la hora del servidor.
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
- `campos` (dict o `null`): presente y con contenido **solo** en errores de validación (`400`) — un mensaje por cada campo inválido. En cualquier otro error (ej. `404`) viene como `null`.

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

## Endpoints de diagnóstico

### `GET /health`

`200 OK` + `{"status": "ok", "service": "gedenaz-api"}` — confirma que la API está arriba (no prueba la base de datos).

### `GET /health/db`

`200 OK` + `{"status": "ok", "service": "gedenaz-db"}` si logra conectarse a MySQL; `503 Service Unavailable` + `{"status": "error", "detail": "..."}` si falla la conexión.
