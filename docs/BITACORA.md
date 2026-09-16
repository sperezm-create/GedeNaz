# Bitácora del Proyecto — GedeNaz App

> Registro cronológico de las sesiones de trabajo: qué se hizo, qué se decidió y qué quedó pendiente. **Solo se agregan entradas nuevas arriba**, no se editan ni se borran las anteriores (si algo cambia, se anota en una entrada nueva). Para el estado *actual* del proyecto (no el historial), ver [`MEMORIA_PROYECTO.md`](MEMORIA_PROYECTO.md).

---

## 2026-09-16 (cont. 10) — PATCH para actualización parcial + bug de rowcount corregido

Nicolas preguntó si RF3 (`PUT`) podía evitar tener que mandar los 4 campos para actualizar solo uno (ej. ajustar stock). Se acordó: `PATCH` nuevo para actualización parcial, `PUT` se mantiene para reemplazo completo.

**Bug real encontrado al implementar esto** (y que ya estaba en el `PUT` en producción, no solo en el `PATCH` nuevo): se probó empíricamente contra Aiven que `cursor.rowcount` de `mysql-connector-python` reporta filas **cambiadas**, no filas que matchearon el `WHERE` — si se actualiza un producto mandando exactamente los mismos valores que ya tenía (sin cambio real), `rowcount` da `0`, y el código interpretaba eso como "el producto no existe", devolviendo un `404` incorrecto. Confirmado con una prueba directa (`UPDATE` con mismo valor → `rowcount = 0`; con valor distinto → `rowcount = 1`).

**Arreglo**: ninguna función de actualización usa `rowcount` para decidir "no existe" — ahora, después del `UPDATE`, siempre se hace un `SELECT` aparte (`WHERE id = ... AND activo = 1`) para confirmar la existencia, sin importar si el `UPDATE` cambió algo o no.

**Qué se agregó/cambió:**

- `logic/productos.py`: refactor de `validar_producto` para compartir validadores por campo (`_validar_nombre`, `_validar_categoria`, `_validar_precio`, `_validar_stock`) entre la validación completa (RF1/PUT) y la nueva `validar_producto_parcial` (PATCH — exige al menos un campo reconocido, valida solo los presentes).
- `data/productos.py`: `actualizar_producto` corregido (bug de arriba) + `actualizar_producto_parcial` nueva (UPDATE dinámico solo de los campos presentes).
- `api/productos.py`: `PATCH /productos/<id>` nuevo.
- **11 tests nuevos** (30 → 41), incluidas 2 pruebas de regresión específicas del bug de `rowcount` (actualizar con los mismos valores, completo y parcial, debe seguir encontrando el producto).
- `docs/specs/06-referencia-api.md`: documentado `PATCH`, con guía de cuándo usar `PUT` vs `PATCH`. `01-requisitos-funcionales.md` y `03-arquitectura.md` actualizados (el detalle del bug de `rowcount` queda anotado en la arquitectura para quien toque `data/` a futuro).

**Verificado manualmente** con `curl`: `PATCH` solo con `stock` cambia solo ese campo; repetir el mismo `PATCH` (mismo valor) sigue devolviendo `200`, no `404`; `PATCH` sin campos devuelve `400`. Base de Aiven confirmada en 6 productos activos (sin basura de tests).

**Pendiente de tu parte**: otro "Manual Deploy" en Render para llevar el `PATCH` y el arreglo del bug a producción.

---

## 2026-09-16 (cont. 9) — Referencia de API y unificación del formato de errores

Nicolas preguntó si backend + BD ya estaban listos para que el equipo avance con Android. Se hizo una auditoría honesta y se encontraron 2 huecos reales:

1. **No existía un documento de referencia de la API** — el contrato HTTP estaba desperdigado en notas de implementación dentro de cada RF, sin ejemplos de JSON. Quien programe el networking de la app Android habría tenido que leer el código fuente directamente.
2. **Inconsistencia real en el formato de errores**: `400` devolvía `{"errores": {...}}` (plural, dict) y `404` devolvía `{"error": "..."}` (singular, string) — dos formas distintas para el mismo concepto.

**Decisión** (confirmada con Nicolas): unificar el formato de error ahora, porque nadie ha escrito código Android todavía que dependa de la forma actual — es el momento más barato para cambiarlo. Nuevo formato único para **todo** error, sea `400` o `404`:

```json
{"error": {"mensaje": "...", "campos": {...} | null}}
```

`mensaje` siempre presente (string legible); `campos` (dict campo→error) presente solo en validación (`400`), `null` en el resto.

**Qué se cambió:**

- `src/gedenaz/api/productos.py`: helper `_error()` centraliza la construcción del envoltorio; los 4 endpoints que pueden fallar (`POST`, `GET <id>`, `PUT`, `DELETE`) lo usan.
- `tests/api/test_productos.py`: actualizado para verificar la nueva forma (`body["error"]["campos"]` en vez de `body["errores"]`).
- **Nuevo documento**: [`docs/specs/06-referencia-api.md`](specs/06-referencia-api.md) — contrato HTTP completo: base URL (local y producción), envoltorio de error, forma de `Producto`, y los 5 endpoints (los 4 de RF1-RF4 + `/health`/`/health/db`) con ejemplos de request/response. **Verificado contra el servidor real** con `curl` (400, 404 y listado vacío) — los ejemplos del documento coinciden exactamente con las respuestas reales.
- `README.md` y `mobile/README.md` enlazan al nuevo documento; `mobile/README.md` también actualizado con la URL de producción (ya no es un pendiente).

**30 tests en verde.** Datos de prueba (6 productos sembrados antes) siguen intactos — no se tocaron durante esta sesión de trabajo.

**Pendiente de tu parte**: hacer "Manual Deploy" en Render para que el cambio de formato de errores quede en producción (por ahora solo está en local y en el repo).

---

## 2026-09-16 (cont. 8) — CRUD completo en el backend (RF2, RF3, RF4)

Con RF1 ya en producción, Nicolas pidió dejar el CRUD completo del backend listo (RF2 Leer, RF3 Actualizar, RF4 Eliminar), siguiendo el mismo patrón de 3 capas que RF1.

**Qué se agregó, en `data/productos.py` → `logic/productos.py` → `api/productos.py`:**

- **RF2**: `listar_productos(nombre?, categoria?)` (filtro parcial insensible a mayúsculas, solo productos con `activo = 1`) y `obtener_producto(id)` (detalle, `NotFoundError` si no existe/inactivo) → `GET /productos` y `GET /productos/<id>`.
- **RF3**: `actualizar_producto(id, datos)` — reusa `validar_producto()` de RF1 (mismas reglas), UPDATE completo de los 4 campos (el "ajuste de stock" es simplemente mandar el nuevo valor, no un delta) → `PUT /productos/<id>` (`400` validación, `404` no existe).
- **RF4**: `eliminar_producto(id)` — baja lógica (`UPDATE activo = 0`, nunca `DELETE` físico, valida la decisión de `02-modelo-de-datos.md`) → `DELETE /productos/<id>` (`204` éxito, `404` no existe/ya inactivo).
- Excepción nueva `NotFoundError` en `logic/productos.py`, paralela a `ValidationError`, para que la API traduzca a `404` limpiamente.

**Tests**: de 21 a 30. Los de `logic/` siguen sin tocar la base (la validación de RF3 corre antes de llamar a `data/`, así que se puede probar sin `.env`). Los de `data/` y `api/` prueban contra Aiven de verdad — incluye un test que confirma que la baja lógica **no borra la fila** (se verifica `activo = 0` directo en la tabla) y que repetir la baja sobre algo ya inactivo no hace nada.

**Verificado manualmente** con `curl` contra la API local: flujo completo crear → listar (filtrado) → detalle → actualizar → eliminar → detalle post-eliminación (`404`) — todo correcto. Base de Aiven confirmada en 0 filas después de limpiar los datos de prueba (incluido un producto que quedó con baja lógica, borrado físicamente a mano por ser solo dato de prueba).

**Specs actualizadas**: notas "✅ Backend implementado" en RF2, RF3 y RF4 (`01-requisitos-funcionales.md`) — la de RF4 además marca como resuelta la decisión "física vs. lógica" que estaba pendiente (se implementó baja lógica), aunque sigue sin confirmarse con la empresa. Estado de `data/` actualizado en `03-arquitectura.md` (CRUD completo, ya no "pendiente para RF2-RF4").

**Estado**: el backend tiene las 4 operaciones CRUD completas, probadas y en producción. Lo único que falta para el sistema completo es la app Android (bloqueada por la decisión de framework).

---

## 2026-09-16 (cont. 7) — Propuesta de diseño: registro de ventas (RF3.1)

Nicolas preguntó cómo se manejaría el registro de ventas (¿se guarda en la BD? ¿cómo?). Se aclaró que **hoy no existe ningún registro de ventas** — RF3 solo permite editar el stock a mano, sin dejar rastro de qué se vendió ni a qué precio. Se confirmó con Nicolas que esto era **solo curiosidad sobre RF3.1** (trabajo futuro, explícitamente fuera del alcance del informe entregado), no un pedido de ampliar el alcance ahora.

Se documentó como propuesta en [`docs/propuestas/registro-de-ventas.md`](propuestas/registro-de-ventas.md) (nuevo directorio `docs/propuestas/`, para ideas discutidas pero no decididas — distinto de `docs/specs/`, que es la fuente de verdad del alcance ya confirmado). Puntos clave de la propuesta: tabla `venta` separada de `producto` (relación 1 a muchos), con `precio_unitario` guardado como "foto" del precio al momento de la venta (no como referencia al precio actual, para no reescribir el historial cada vez que cambia un precio); "registrar venta" como acción nueva y distinta de RF3 (inserta en `venta` + descuenta stock en una sola transacción); valida la decisión ya tomada de usar baja lógica (`activo`) en vez de `DELETE` físico para RF4.

**No se tocó** el modelo de datos actual (`02-modelo-de-datos.md`, `schema.sql`) ni el código — es una nota para que Nicolas la lleve a discutir con el equipo, nada más. Si se decide adoptar, se traslada primero a las specs oficiales (spec-first) antes de programar.

---

## 2026-09-16 (cont. 6) — Backend desplegado en Render, funcionando en producción

Se ejecutó el despliegue preparado en la sesión anterior. Un problema en el camino:

**El repo no es de Nicolas** (lo creó Sebastian) — al conectar GitHub, Render pedía permisos que un colaborador (no dueño) del repo no necesariamente tiene para instalar la app de GitHub. Se resolvió aprovechando que el repo `sperezm-create/GedeNaz` es **público** (confirmado vía API de GitHub): se usó la opción **"Public Git Repository"** de Render (pegar la URL del repo directo), que no requiere conectar ninguna cuenta de GitHub. Trade-off aceptado: sin auto-deploy en cada push, hay que apretar "Manual Deploy" a mano cuando quieran subir cambios nuevos — aceptable para un proyecto de curso.

**Configuración usada**: Build Command `pip install -r requirements.txt && pip install -e .`, Start Command `gunicorn "gedenaz.app:create_app()"`, plan Free. Variables de entorno (`DB_HOST/PORT/USER/PASSWORD/NAME`) + el certificado CA subido como Secret File (`aiven-ca.pem`), con `DB_SSL_CA` apuntando a la ruta que Render mostró al montarlo.

**Verificado en producción** (`https://gedenaz-api.onrender.com`): `/health` y `/health/db` responden `200`, y un `POST /productos` real creó un producto en Aiven (id 10, borrado después de la prueba) — confirma la cadena completa `Render → SSL → Aiven` funcionando.

**Estado**: el backend (RF1 completo) ya está corriendo en producción, gratis, accesible por HTTPS desde cualquier lado (incluida la futura app Android).

---

## 2026-09-16 (cont. 5) — Preparación para desplegar el backend en Render

Se dejó todo listo para desplegar la API en Render (verificado por web: sintaxis de Gunicorn para app factory, y que Render tiene una sección "Secret Files" separada de las variables de entorno, justo para casos como el certificado CA de Aiven).

**Qué se hizo:**

- `requirements.txt`: se agregó `gunicorn` (el dev server de Flask no sirve para producción — la propia app lo advierte al arrancar). Se confirmó que instala bien en Windows (aunque solo se ejecuta de verdad en el Linux de Render).
- `docs/specs/05-entorno-desarrollo.md`, nueva sección 9 "Desplegar el backend en Render": cuenta con GitHub, conectar el repo, Build Command (`pip install -r requirements.txt && pip install -e .`), Start Command (`gunicorn "gedenaz.app:create_app()"`), variables de entorno, y cómo subir el certificado CA como Secret File (no como variable de entorno normal, porque es un archivo).
- `03-arquitectura.md`: fila de Render actualizada (guía lista, pendiente de ejecutar) + fila nueva para Gunicorn.

**Pendiente**: los pasos son manuales en la web de Render (crear cuenta, conectar repo, configurar) — documentados pero no ejecutados todavía.

---

## 2026-09-16 (cont. 4) — RF1 completo en el backend (crear producto)

Con la conexión ya lista (tarea 1.3), se implementó RF1 de punta a punta en el backend — tareas 1.5 y 1.6 de la Carta Gantt (Francisco y Sebastian respectivamente), avanzadas en conjunto.

**Qué se agregó, en las 3 capas de la arquitectura:**

- `src/gedenaz/logic/productos.py`: `validar_producto()` y `crear_producto()`. Valida los 4 campos de RF1 (nombre, categoría, precio, stock) según los criterios de aceptación del spec — reporta **todos** los errores a la vez (no uno por uno), como un dict `{campo: mensaje}`. No importa nada de Flask ni de MySQL, se prueba con Python puro.
- `src/gedenaz/data/productos.py`: `crear_producto()` — hace el `INSERT` y devuelve la fila ya guardada (con `id` y timestamps de MySQL), convirtiendo tipos (`Decimal`→`float`, `datetime`→ISO string) para que sea directamente serializable a JSON.
- `src/gedenaz/api/productos.py`: blueprint con `POST /productos` — parsea el JSON de la request, llama a `logic.crear_producto()`, devuelve `201` con el producto creado o `400` con los errores de validación.

**Tests nuevos** (21 en total ahora, antes 6): `tests/logic/test_productos.py` (puros, sin DB, corren siempre), `tests/data/test_productos.py` y `tests/api/test_productos.py` (contra Aiven de verdad, se saltan solos sin `.env` configurado). Los tests de integración **borran lo que crean** (`try/finally` con `DELETE`) para no ensuciar la base compartida.

**Verificado manualmente** con `curl` contra la API corriendo local: creación exitosa devuelve `201` con el producto completo; falta de campos obligatorios devuelve `400` con el detalle por campo. Se confirmó que la tabla `producto` en Aiven quedó en 0 filas después de correr todos los tests (sin basura de pruebas).

**Specs actualizadas**: nota "✅ Backend implementado" en RF1 (`01-requisitos-funcionales.md`) y estado actualizado de `data/` en `03-arquitectura.md`.

---

## 2026-09-16 (cont. 3) — Tarea 1.3: capa de conexión Python–MySQL

Con la base ya lista en Aiven, se avanzó la tarea 1.3 de la Carta Gantt (asignada a Francisco, pero se siguió trabajando en conjunto para no perder impulso).

**Qué se agregó:**

- `src/gedenaz/data/db.py`: `get_connection()` y `connection_scope()` (context manager) — abren una conexión a MySQL usando `config.get_db_config()`, agregando `ssl_verify_cert=True` automáticamente cuando hay `ssl_ca` configurado (evita el error "Invalid ssl-mode" de la sesión anterior).
- `GET /health/db` en la API (`app.py`): intenta conectarse a MySQL y devuelve `ok`/`error` — sirve para confirmar la conexión real por HTTP, útil también una vez desplegado en Render.
- `tests/data/test_db.py` y `tests/test_environment.py::test_api_health_db`: prueban la conexión real. Se saltan solos (`pytest.mark.skipif`) si no hay `DB_PASSWORD` en el entorno, para no romper el setup de alguien que todavía no tiene su propio `.env` con Aiven.

**Bug encontrado y arreglado al probar de punta a punta**: `python src/gedenaz/main.py` (el comando ya documentado desde la tarea 1.1) fallaba con `ModuleNotFoundError: No module named 'gedenaz'` — problema clásico de la estructura `src/` sin el paquete instalado. Se agregó `pyproject.toml` (setuptools, `where = ["src"]`) y se sumó `pip install -e .` al paso de instalación de dependencias en `05-entorno-desarrollo.md`. **Cada integrante necesita correr `pip install -e .` una vez** además de `pip install -r requirements.txt` (o va a fallar al intentar correr la API).

**Verificado end-to-end**: se levantó la API local (`python src/gedenaz/main.py`) y se confirmó con `curl` que tanto `/health` como `/health/db` responden `200 {"status": "ok"}` — la cadena completa `API local → SSL → Aiven` funciona.

**Los 6 tests pasan** (`pytest`, incluye los 2 nuevos de conexión real).

---

## 2026-09-16 (cont. 2) — Base de datos Aiven creada y esquema aplicado

Nicolas creó la cuenta de Aiven y el servicio `mysql-gedenaz-bd` (plan Free). Dos problemas al conectar, ambos resueltos:

1. **"Invalid ssl-mode"** al conectar con MySQL Workbench dando el certificado CA sin pedir verificación. Arreglo: pestaña SSL de la conexión → "Use SSL" = "Require and Verify CA". Se documentó en `05-entorno-desarrollo.md` y se dejó un comentario en `config.py` (campo `ssl_ca`) para que a Francisco no le pase lo mismo al programar la conexión en Python (hay que pasar `ssl_verify_cert=True` junto con `ssl_ca`).
2. **Workbench se quedó colgado en "Starting editor session"** (bug conocido de Workbench contra bases remotas, no es un problema de la conexión en sí). En vez de pelear con la UI, se armó `scripts/apply_schema.py` — un script chico que usa `mysql-connector-python` (ya instalado) para correr cualquier archivo `.sql` contra la base del `.env`. Se usó para aplicar `schema_cloud.sql` a Aiven, confirmado con éxito y verificado con `DESCRIBE producto` (todas las columnas, tipos, defaults e índices tal como en el spec).

**Estado**: la base `gedenaz` en Aiven ya tiene la tabla `producto` lista para usarse. El `.env` local de Nicolas ya está completo y probado.

**Nota técnica para quien programe la capa de datos (tarea 1.3, Francisco)**: al conectar con `mysql-connector-python`, si `DBConfig.ssl_ca` no es `None`, pasar también `ssl_verify_cert=True` a `mysql.connector.connect(...)` — si no, tira el mismo error "Invalid ssl-mode" que dio Workbench.

---

## 2026-09-16 (cont.) — PythonAnywhere descartado: MySQL ya no está en el plan gratis

Nicolas fue a ejecutar la guía de PythonAnywhere y el panel le avisó que MySQL no está disponible en cuentas gratis. Se verificó por web: **PythonAnywhere movió el acceso a MySQL (y las tareas programadas) a sus planes pagos desde enero de 2026** (cuentas gratis creadas antes del 15-01-2026 conservan el acceso, las nuevas no). Además, se confirmó que las cuentas gratuitas de PythonAnywhere **no pueden conectarse a ninguna base de datos externa** (solo HTTP/HTTPS a una lista blanca de sitios, ningún otro protocolo) — así que tampoco servía como "solo hosting del backend" apuntando a MySQL en otro lado.

**Nuevo plan, verificado por web**: separar los dos servicios.
- **Aiven** para MySQL — plan "Free" (1GB RAM/almacenamiento), sin tarjeta, sin límite de tiempo (aunque se apaga solo tras inactividad prolongada, avisando antes por correo). Base por defecto: `defaultdb`; exige conexión SSL (certificado CA descargable desde su consola).
- **Render** para alojar la API Flask — su free tier sí permite conexiones salientes a bases de datos externas como Aiven (solo bloquea puertos SMTP), a diferencia de PythonAnywhere.

**Qué se cambió en el repo:**

- `src/gedenaz/data/schema_pythonanywhere.sql` → renombrado a `schema_cloud.sql` (sigue sirviendo: la idea de "sin CREATE DATABASE, la base ya existe" aplica igual a Aiven).
- `docs/specs/05-entorno-desarrollo.md` sección 8 reescrita para Aiven (pasos verificados: crear servicio MySQL, anotar host/puerto/usuario/password, descargar certificado CA, crear/usar base, correr `schema_cloud.sql`), con nota de que desplegar el backend en Render queda pendiente de ejecutar.
- `src/gedenaz/config.py`: se agregó el campo `ssl_ca` a `DBConfig` (variable de entorno `DB_SSL_CA`), porque Aiven exige SSL y `mysql-connector-python` necesita la ruta al certificado.
- `.env.example` actualizado con el formato de Aiven en vez de PythonAnywhere.
- `docs/specs/03-arquitectura.md`: tabla de stack actualizada (Aiven para MySQL, Render para el backend, ambos pendientes de desplegar de verdad).

**Pendiente**: ejecutar de verdad los pasos en Aiven (crear cuenta, servicio, correr el esquema) y luego desplegar la API en Render — ninguno de los dos está hecho todavía, solo documentado.

---

## 2026-09-16 — SQL vs NoSQL, evaluación de Render, y guía de despliegue en PythonAnywhere

**Contexto**: Nicolas preguntó si el modelo de datos SQL serviría para Firebase (NoSQL) a futuro, lo que llevó a una conversación más amplia sobre SQL vs NoSQL para este proyecto.

**SQL vs NoSQL**: se recomendó quedarse con MySQL (SQL) en vez de pasarse a Firebase/Firestore (NoSQL), por: (1) el informe ya entregado compromete MySQL por escrito — cambiarlo de nuevo (ya se corrigió escritorio→Android una vez) suma riesgo frente a la rúbrica; (2) el modelo es una sola tabla simple, no hay ventaja real de NoSQL acá; (3) ya se invirtió el trabajo de esta semana en Flask+MySQL; (4) el objetivo de centralización se logra igual con cualquiera de las dos. Se dejó explícito que si el motivo real hubiera sido "no queremos mantener un backend", Firebase sí tendría una ventaja concreta (SDK Android nativo, sin necesidad de Flask) — pero el equipo decidió seguir con MySQL.

**Se evaluó Render.com** (verificado por web): no ofrece MySQL gestionado, solo PostgreSQL (y con límite de 30 días en el plan gratis). Podría servir solo para alojar el Flask (tier gratis, 750h/mes, sin tarjeta), pero la app "duerme" tras 15 min sin uso — mal síntoma para el uso real de la tienda. Se descartó frente a PythonAnywhere.

**Decisión confirmada**: hosting en **PythonAnywhere** (API Flask + MySQL juntos, gratis, sin tarjeta).

**Qué se hizo en el repo:**

- `src/gedenaz/data/schema_pythonanywhere.sql` — variante del esquema sin `CREATE DATABASE`/`USE` (en PythonAnywhere la base se crea desde su panel web, con nombre prefijado por el usuario, ej. `tuusuario$gedenaz`).
- `docs/specs/05-entorno-desarrollo.md` — nueva sección 8 "Desplegar la base de datos en PythonAnywhere", paso a paso completo (crear cuenta, crear base, correr el esquema, configurar `.env`).
- `.env.example` — comentario explicando el formato de `DB_HOST`/`DB_USER`/`DB_NAME` cuando la base vive en PythonAnywhere.
- `docs/MEMORIA_PROYECTO.md` actualizado.

**Pendiente**: los pasos de la sección 8 son manuales (crear cuenta, usar el panel de PythonAnywhere) — quedaron documentados pero **no ejecutados todavía**. Alguien del equipo tiene que efectivamente crear la cuenta y correr el esquema.

---

## 2026-09-09 (cont. 2) — Corrección de alcance: la app es Android, no de escritorio

Nicolas avisó que la app **no es de escritorio, es una app móvil para Android** — contradice lo que dice el informe ya entregado hoy (H1). Se conversó con el equipo (Nicolas hizo de puente) sobre cómo conectar a MySQL desde una app móvil, porque conectar el teléfono directo a MySQL no es seguro (credenciales dentro del APK, puerto expuesto a internet).

**Se investigaron alternativas gratuitas de hosting** (verificado por web, no solo memoria): PlanetScale ya no tiene plan gratis (desde abril 2024, parte en US$5/mes); Railway tiene "plan gratis" pero es en la práctica un crédito de prueba limitado; **Aiven** ofrece MySQL "always free" (1GB, sin tarjeta); **PythonAnywhere** tier gratis permite alojar un backend Flask + MySQL juntos sin tarjeta (el MySQL gratis de PythonAnywhere solo es accesible desde dentro de la misma plataforma, lo cual calza bien porque la API vive ahí mismo); **db4free.net** es gratis pero sin garantías de uptime.

**Decisión del equipo**: mantener MySQL (no pasarse a SQLite local), y como es una app móvil, usar una API en el medio en vez de conexión directa — así la app nunca guarda credenciales de la base.

**Qué se cambió en el repo:**

- Specs actualizadas: `00-vision-y-alcance.md` (resumen y objetivos ahora dicen "app Android"), `01-requisitos-funcionales.md` (nota sobre cliente Android + validación también en la API), `02-modelo-de-datos.md` (nota: el esquema no cambia, pero ahora la API es la única que toca MySQL; se marcó como pendiente reforzar autenticación de la API ya que queda expuesta a internet), `03-arquitectura.md` (reescrito: arquitectura cliente-servidor App Android → API Flask → MySQL, reemplaza las 3 capas locales de escritorio), `04-plan-de-trabajo.md` (nota aclaratoria arriba, no se tocó la tabla transcrita de la Carta Gantt oficial).
- Código: se eliminó `src/gedenaz/ui/` (pantallas Tkinter) y el `main.py` viejo (ventana Tkinter). Se agregó `src/gedenaz/api/` (endpoints Flask, por ahora vacío) y `src/gedenaz/app.py` (fábrica de la app Flask con un endpoint `/health`). `main.py` ahora levanta el servidor Flask. `logic/` y `data/` no cambiaron.
- `requirements.txt`: se agregó `Flask`. Se mantienen `mysql-connector-python`, `python-dotenv`, `pytest` (siguen siendo necesarios para el backend).
- Se creó `mobile/README.md` como placeholder: ahí va a vivir la app Android una vez que el equipo elija el framework (Kotlin / Flutter / Python+Kivy — **todavía sin decidir**, es lo próximo que hay que resolver).
- Tests de humo actualizados: se sacó el test de Tkinter, se agregó uno que prueba que la API Flask responde en `/health`. Los 3 tests siguen en verde.
- `README.md` y `docs/MEMORIA_PROYECTO.md` actualizados para reflejar todo esto.

**Pendiente/bloqueante**: el framework de la app Android. Sin eso, Sebastian no puede empezar la pantalla "Crear producto" (tarea 1.4).

---

## 2026-09-09 (cont.) — Acceso a GitHub resuelto, primer push

Sebastian dio acceso de escritura a Nicolas (`goost01`) en el repo. Se hizo `git push -u origin main`: los 2 commits locales (montaje del proyecto + bitácora/memoria) ya están en `https://github.com/sperezm-create/GedeNaz.git`, visibles para todo el equipo. Rama local `main` quedó trackeando `origin/main`.

Se conversó y se decidió **mantener** `MEMORIA_PROYECTO.md` tal como está (no se simplifica ni se elimina): las specs documentan decisiones, `MEMORIA_PROYECTO.md` es la foto del estado operativo, `BITACORA.md` es el registro cronológico personal.

---

## 2026-09-09 — Montaje del proyecto y specs iniciales

**Participantes**: Nicolas Silva + asistente.

**Contexto**: hoy se entregó el Informe Propuesta Proyecto SI (H1 de la Carta Gantt). Empezamos a trabajar spec-first a partir de ese informe, y arrancamos la tarea 1.1 de la Carta Gantt ("configurar entorno de desarrollo"), asignada a Nicolas para el 10–12 de septiembre.

**Qué se hizo**:

- Se extrajo el contenido del informe (`Informe propuesta Proyecto GedeNaz.docx`), la Carta Gantt (`Carta Gantt GedeNaz.xlsx`) y se revisaron las imágenes de la presentación (`GedeNaz_presentacion.pdf`, `GedeNaz_Inventory_System.pdf`) y la rúbrica de evaluación.
- Se creó `docs/specs/` con 6 documentos: visión y alcance, requisitos funcionales (RF1–RF4), modelo de datos, arquitectura, plan de trabajo (derivado de la Carta Gantt) y guía de entorno de desarrollo.
- **Decisión de equipo**: interfaz gráfica con **Tkinter estándar** (no CustomTkinter ni PyQt) — simple, sin dependencias externas, cero costo.
- Se montó el entorno de desarrollo: `venv/` (Python 3.14.5), `requirements.txt` (`mysql-connector-python`, `python-dotenv`, `pytest`), `.gitignore`, `.env.example`, estructura `src/gedenaz/{ui,logic,data}` + `tests/`.
- Se verificó el entorno con 3 tests de humo (`pytest` en verde) y se probó que la ventana Tkinter placeholder abre y cierra sin errores.
- Se inicializó el repo Git local, commit inicial creado (identidad local: `goost01` / `nikolas.silva.fuentes@gmail.com`, configurada solo para este repo, no global).
- Se conectó el remoto `https://github.com/sperezm-create/GedeNaz.git` (repo del equipo, dueño Sebastian Perez). El remoto ya tenía un commit inicial con un README placeholder — se hizo merge (`--allow-unrelated-histories`) conservando nuestro README más completo, sin usar `--force`.
- **Pendiente / bloqueado**: `git push` rechazado con `403 Permission denied to goost01` — Nicolas aún no es colaborador con permiso de escritura en el repo. Nicolas pidió acceso a Sebastián. El commit queda listo en local para subir apenas llegue el acceso.
- A pedido de Nicolas, se creó este archivo (`BITACORA.md`) y `MEMORIA_PROYECTO.md` como mecanismo de continuidad entre sesiones.

**Decisiones abiertas / a validar** (quedaron documentadas como notas en los specs, no bloquean el avance):

- Campos exactos de "Producto" (`nombre`, `categoría`, `precio`, `stock`) — a confirmar con la empresa GedeNaz.
- RF4: ¿baja lógica (columna `activo`) o borrado físico? Se propuso baja lógica en `02-modelo-de-datos.md`, a confirmar con el equipo.
- Sin autenticación en esta versión (un solo tipo de usuario, sin login) — asumido, no confirmado explícitamente en el informe.

**Próxima sesión**: retomar desde `docs/MEMORIA_PROYECTO.md` → sección "Próximos pasos".
