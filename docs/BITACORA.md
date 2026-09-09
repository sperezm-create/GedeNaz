# Bitácora del Proyecto — GedeNaz App

> Registro cronológico de las sesiones de trabajo: qué se hizo, qué se decidió y qué quedó pendiente. **Solo se agregan entradas nuevas arriba**, no se editan ni se borran las anteriores (si algo cambia, se anota en una entrada nueva). Para el estado *actual* del proyecto (no el historial), ver [`MEMORIA_PROYECTO.md`](MEMORIA_PROYECTO.md).

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
