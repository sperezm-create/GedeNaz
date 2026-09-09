# 04 · Plan de Trabajo — GedeNaz App

> Derivado de `Carta Gantt GedeNaz.xlsx`. Metodología: **Kanban** en Jira (columnas Por hacer / En curso / Terminado). El jefe de proyecto (Francisco Jara) revisa y aprueba las tareas antes de marcarlas "Terminado". Fechas convertidas desde la Carta Gantt (semana S1 = 31-08-2026).
>
> **Nota (2026-09-09)**: la tabla de abajo es una transcripción fiel de la Carta Gantt oficial, que fue armada pensando en una app de escritorio. Tras la corrección de alcance a app Android ([00-vision-y-alcance.md](00-vision-y-alcance.md)), donde diga "interfaz de escritorio" o "formulario de escritorio" léase "pantalla Android"; donde diga "conexión Python–MySQL" léase "API Python que conecta con MySQL" ([03-arquitectura.md](03-arquitectura.md)). Las fechas, responsables y RF asociados no cambian — no se editó la tabla para no perder la trazabilidad con el documento oficial entregado.

## Roles del equipo

| Integrante | Rol |
|---|---|
| Francisco Jara | Jefe de Proyecto + Backend/Base de Datos (modelo de datos, conexión Python–MySQL, lógica CRUD). Revisa y aprueba tareas del tablero. |
| Sebastian Perez | Desarrollo de interfaz de usuario en Python (pantallas y formularios). Revisa y aprueba tareas del tablero. |
| **Nicolas Silva** | Desarrollo de interfaz de usuario en Python + apoyo en pruebas funcionales CRUD. |
| Cristóbal Sierra Porras | Documentación de informes de avance/final, apoyo en presentaciones. |

Decisiones relevantes (alcance, diseño, prioridades) se toman en conjunto por consenso; si no hay acuerdo, decide el jefe de proyecto priorizando los plazos de la Carta Gantt.

## Fases e hitos

| Hito | Descripción | Fecha |
|---|---|---|
| H1 | ★ Entrega Informe Propuesta Proyecto SI + Presentación | 2026-09-09 (hoy) |
| H2 | ★ Entrega Avance #1 (RF1 Crear) | 2026-09-30 |
| H3 | ★ Entrega Avance #2 (RF2 Leer) | 2026-10-21 |
| H4 | ★ Entrega Avance #3 (RF3 Actualizar / RF4 Eliminar) — proyecto funcionalmente terminado | 2026-11-11 |
| H6 | ★ Entrega Informe Final + Presentación | 2026-12-02 |

## Fase 1 · Avance #1 (RF1 — Crear) — 2026-09-10 a 2026-09-29

| ID | Tarea | Responsable | Inicio | Fin |
|---|---|---|---|---|
| **1.1** | **Configurar entorno de desarrollo (VS Code, Python, entorno virtual y librerías)** | **Nicolas Silva** | **2026-09-10** | **2026-09-12** |
| 1.2 | Instalar y configurar servidor MySQL; crear base de datos y tabla `producto` | Francisco Jara | 2026-09-12 | 2026-09-16 |
| 1.3 | Implementar capa de conexión Python–MySQL (driver y acceso a datos) | Francisco Jara | 2026-09-14 | 2026-09-16 |
| 1.4 | Implementar interfaz "Crear producto" (formulario de escritorio) | Sebastian Perez | 2026-09-17 | 2026-09-21 |
| 1.5 | Implementar lógica de inserción de productos en MySQL (INSERT) | Francisco Jara | 2026-09-20 | 2026-09-23 |
| 1.6 | Validaciones del formulario (campos obligatorios y tipos de dato) | Sebastian Perez | 2026-09-22 | 2026-09-25 |
| 1.7 | Pruebas de RF1 (Crear producto) | Todo el equipo | 2026-09-24 | 2026-09-27 |
| 1.8 | Redactar y revisar Informe Avance #1 | Nicolas Silva | 2026-09-26 | 2026-09-29 |

**➜ Tarea actual de esta sesión: 1.1**, ver [05-entorno-desarrollo.md](05-entorno-desarrollo.md).

## Fase 2 · Avance #2 (RF2 — Leer) — 2026-10-01 a 2026-10-20

| ID | Tarea | Responsable | Inicio | Fin |
|---|---|---|---|---|
| 2.1 | Implementar interfaz de listado de inventario | Cristobal Sierra | 2026-10-01 | 2026-10-06 |
| 2.2 | Implementar consultas SQL (SELECT) para obtener productos | Francisco Jara | 2026-10-03 | 2026-10-07 |
| 2.3 | Implementar búsqueda y filtro por nombre/categoría | Francisco Jara | 2026-10-06 | 2026-10-10 |
| 2.4 | Implementar vista de detalle de producto | Cristobal Sierra | 2026-10-09 | 2026-10-13 |
| 2.5 | Iniciar interfaz "Actualizar producto" (formulario de edición) | Nicolas Silva | 2026-10-12 | 2026-10-16 |
| 2.6 | Pruebas de RF2 (Leer/consultar productos) | Todo el equipo | 2026-10-15 | 2026-10-18 |
| 2.7 | Redactar y revisar Informe Avance #2 | Nicolas Silva | 2026-10-17 | 2026-10-20 |

## Fase 3 · Avance #3 (RF3 · RF3.1 · RF4) — 2026-10-22 a 2026-11-10

| ID | Tarea | Responsable | Inicio | Fin |
|---|---|---|---|---|
| 3.1 | Completar lógica de actualización de datos y stock (UPDATE) en MySQL | Francisco Jara | 2026-10-22 | 2026-10-27 |
| 3.2 | Validaciones de actualización (stock no negativo, campos) | Cristobal Sierra | 2026-10-26 | 2026-10-29 |
| 3.3 | Implementar eliminación de producto con confirmación | Cristobal Sierra | 2026-10-28 | 2026-10-31 |
| 3.4 | Implementar lógica de borrado (DELETE) en MySQL | Francisco Jara | 2026-10-30 | 2026-11-03 |
| 3.5 | Pruebas integrales de las 4 operaciones CRUD (RF1–RF4) | Todo el equipo | 2026-11-03 | 2026-11-07 |
| 3.6 | Corrección de errores y pulido de la interfaz | Sebastian Perez | 2026-11-05 | 2026-11-09 |
| 3.7 | Generación de reportes analíticos (RF3.1) — trabajo futuro | Nicolas Silva | 2026-11-08 | 2026-11-10 |
| 3.7b | Redactar y revisar Informe Avance #3 | Nicolas Silva | 2026-11-08 | 2026-11-10 |

## Fase 4 · Cierre — 2026-11-12 a 2026-12-02

| ID | Tarea | Responsable | Inicio | Fin |
|---|---|---|---|---|
| 4.1 | Pruebas de regresión y control de calidad final | Todo el equipo | 2026-11-12 | 2026-11-17 |
| 4.2 | Elaborar manual de usuario para Gedalias y Nazareth | Todo el equipo | 2026-11-16 | 2026-11-20 |
| 4.3 | Grabación del video demo del sistema | Todo el equipo | 2026-11-20 | 2026-11-24 |
| 4.4 | Redacción del Informe Final del Proyecto SI | Nicolas Silva | 2026-11-28 | 2026-11-30 |
| 4.5 | Preparación de la Presentación Final | Todo el equipo | 2026-11-30 | 2026-11-30 |

## Análisis de riesgos (del informe)

| Riesgo | Prob. | Impacto | Mitigación |
|---|---|---|---|
| Curva de aprendizaje del equipo en Python y MySQL | Media | Medio | Dedicar la primera semana a tutoriales guiados antes de programar funcionalidades reales |
| Cambios de alcance solicitados por la empresa | Baja | Alto | Fijar el alcance de los 4 RF en la Propuesta y validarlo con la empresa antes de programar |
| Pérdida/inconsistencia de datos por mala configuración de MySQL | Baja | Alto | Definir esquema y restricciones desde el inicio; probar cada CRUD en entorno de pruebas antes de usar datos reales |
| Retrasos por disponibilidad limitada del equipo | Media | Medio | Distribuir tareas según la Carta Gantt con holguras; seguimiento semanal en Jira |
| Incompatibilidad de versiones de Python/MySQL entre integrantes | Media | Baja | Estandarizar versión de Python, librerías y MySQL; documentar configuración del entorno (ver [05-entorno-desarrollo.md](05-entorno-desarrollo.md)) |
