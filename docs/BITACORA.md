# Bitácora del Proyecto — GedeNaz App

> Registro cronológico de las sesiones de trabajo: qué se hizo, qué se decidió y qué quedó pendiente. **Solo se agregan entradas nuevas arriba**, no se editan ni se borran las anteriores (si algo cambia, se anota en una entrada nueva). Para el estado *actual* del proyecto (no el historial), ver [`MEMORIA_PROYECTO.md`](MEMORIA_PROYECTO.md).

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
