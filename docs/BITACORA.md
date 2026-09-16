# Bitácora del Proyecto — GedeNaz App

> Registro cronológico de las sesiones de trabajo: qué se hizo, qué se decidió y qué quedó pendiente. **Solo se agregan entradas nuevas arriba**, no se editan ni se borran las anteriores (si algo cambia, se anota en una entrada nueva). Para el estado *actual* del proyecto (no el historial), ver [`MEMORIA_PROYECTO.md`](MEMORIA_PROYECTO.md).

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
