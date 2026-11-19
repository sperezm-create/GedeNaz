# Requerimientos y estimación de horas-hombre — GedeNaz App

**Fecha de consolidación:** 16-11-2026
**Equipo:** Grupo 6 — Taller de Sistemas de Información
**Tipo de estimación:** esfuerzo total estimado para análisis, diseño, implementación, pruebas y documentación. No es un registro de horas efectivamente trabajadas.

## 1. Objetivo del documento

Consolidar los requerimientos funcionales reunidos para GedeNaz App, identificar qué está implementado y qué sigue pendiente, y proponer un reparto de trabajo para cuatro integrantes expresado en horas-hombre (h-h).

La estimación cubre la aplicación completa desde la definición del alcance hasta su validación y documentación. Se basa en las funcionalidades y roles descritos en `docs/specs/` y en los requerimientos acordados durante el desarrollo. Las horas reales deben registrarse por separado a medida que el equipo trabaja.

## 2. Descripción y alcance del producto

GedeNaz App es una aplicación de escritorio en Python con interfaz Tkinter y persistencia MySQL. La utilizan los administradores del negocio para gestionar productos, registrar ventas y consultar el movimiento del inventario.

### Incluido

- Inventario de joyas y accesorios.
- Productos con categoría, material, talla o medida, precio y stock.
- Registro, consulta, actualización y baja de productos.
- Ventas con boleta interna, detalle histórico de los productos y actualización de stock.
- Destinatario por línea de venta y, como requisito solicitado, género de quien compra.
- Estadísticas de venta y calendario de ventas.
- Planes de cuotas sin interés con abonos parciales.
- Pruebas, manual, documentación y preparación de demostración.

### Fuera del alcance actual

- Comercio electrónico, catálogo web y pedidos en línea.
- Procesamiento o integración con medios de pago.
- Emisión de boletas tributarias o documentos electrónicos oficiales.
- Intereses, recargos o cálculo de mora.
- Devolución de dinero y anulación automática de ventas que ya tienen abonos.
- Roles diferenciados, permisos por usuario o autenticación multiusuario.
- Rentabilidad, costos de adquisición y contabilidad avanzada.

## 3. Requerimientos funcionales consolidados

### RF1 — Registrar productos

- Registrar nombre, categoría (anillo, collar, pulsera, aros u otra), material, talla o medida, precio y stock inicial.
- Validar campos obligatorios, precio positivo y stock entero no negativo.
- Reconocer como variante distinta la combinación de nombre, categoría, material y talla.
- Confirmar el alta y dejar el producto disponible para la venta.
- Usar “Única” cuando la talla o medida no corresponda.

### RF2 — Consultar inventario

- Listar productos activos con código, nombre, categoría, material, talla, precio y stock.
- Buscar por nombre y filtrar por categoría.
- Consultar el detalle de un producto.
- Refrescar los datos desde la persistencia y comunicar cuando no hay resultados.

### RF3 — Actualizar productos y stock

- Editar nombre, categoría, material, talla, precio y stock.
- Validar los datos y evitar que el stock quede negativo.
- Mostrar los cambios actualizados en el inventario.

### RF4 — Dar de baja productos

- Pedir confirmación antes de dar de baja un producto.
- No mostrar productos dados de baja como disponibles.
- Preservar el historial de ventas asociado al producto.

### RF5 — Registrar ventas, boletas y pagos

**Venta y stock**

- Seleccionar productos con stock y cantidades enteras positivas.
- Calcular el total y registrar la venta con fecha/hora, boleta interna y detalle.
- Descontar el stock dentro de la misma operación; si falla una parte, no dejar una venta o descuento parcial.
- Guardar por línea el código, nombre, categoría, material, talla, precio y destinatario vigentes al momento de la venta.
- Permitir identificar para quién se compra cada producto, sin asumir que todos los artículos de una compra son para la misma persona.
- Mantener la boleta como comprobante interno, no tributario.

**Anulación**

- Permitir anular una boleta completa con confirmación y devolver las unidades al inventario.
- Conservar la boleta anulada en el historial y excluirla de calendario y estadísticas.
- No permitir anular dos veces la misma boleta.
- No permitir anular desde la aplicación una venta con abonos registrados, porque todavía no existe un flujo para registrar la devolución del dinero.

**Cuotas y abonos**

- Permitir pago completo o un plan sin interés de 2 a 120 cuotas.
- Al crear un plan, seleccionar frecuencia semanal, quincenal o mensual y fecha del primer vencimiento.
- Generar montos para cubrir el total; asignar cualquier diferencia de redondeo a la última cuota.
- Registrar uno o más abonos parciales por cuota, conservando el monto y fecha/hora de cada pago.
- Mostrar el monto de cada cuota, cuánto se ha abonado, saldo, estado (pendiente, parcial o pagada) y el saldo total del plan.
- Rechazar abonos mayores que el saldo de la cuota.
- Registrar el pago en el sistema; no procesar transacciones bancarias o pagos con tarjeta.
- Para cuotas mensuales, conservar el día del primer vencimiento cuando exista; si el mes no tiene ese día, usar el último día del mes.

### RF6 — Estadísticas de venta y demanda

- Mostrar productos más vendidos, unidades e ingresos por ventas vigentes.
- Mostrar unidades por categoría y su porcentaje sobre el total.
- Mostrar precios unitarios agrupados por unidades vendidas.
- No incluir ventas anuladas.
- Incorporar el desglose solicitado para responder qué categorías o productos se compran más según el género de quien compra y según el destinatario.
- Incorporar análisis de tallas/medidas más vendidas, filtrable por categoría para no comparar tallas no equivalentes (por ejemplo, anillos y collares).
- No atribuir género a ventas antiguas cuando ese dato no fue registrado; agruparlas como “No informado”.

### RF7 — Calendario e historial

- Consultar las ventas por año, mes, día y hora.
- Indicar en el calendario los días con ventas vigentes y mostrar el detalle de las boletas vigentes.
- No mostrar ventas anuladas en el calendario.
- Mantener las boletas anuladas visibles e identificadas en el historial general.
- Permitir navegar por años con ventas y por el año actual; calcular correctamente meses, días y años bisiestos.
- Consultar la boleta y sus detalles desde el historial.

### RF8 — Registrar género de comprador

- Capturar quién realiza la compra en la venta, separado del destinatario de cada línea.
- Permitir Hombre, Mujer o No informado, sin obligar a declarar el dato.
- Conservar este valor en la venta para habilitar estadísticas por perfil de comprador.
- No inferir el dato en ventas históricas anteriores a su captura.

## 4. Estado al consolidar la nota

El estado se refiere al código y documentos del proyecto revisados al redactar esta nota. La ejecución de migraciones depende de la base MySQL usada por el equipo.

| Área | Estado | Nota |
|---|---|---|
| Alta, consulta, edición y baja de productos | Implementado | El modelo de producto contempla categoría, material y talla. Confirmar que esas columnas también existan en cada base MySQL utilizada. |
| Venta, boleta interna, descuento y reposición de stock al anular | Implementado | Mantiene los detalles históricos por línea. |
| Destinatario por producto vendido | Implementado | Se registra separadamente por línea de venta. |
| Calendario: ocultar ventas anuladas y navegación anual | Implementado | Las anuladas permanecen en historial general, no en calendario. |
| Estadísticas por producto, categoría y precio | Implementado | Excluyen las ventas anuladas. |
| Estadísticas por género de comprador/destinatario | Pendiente | Requiere integrar el campo de comprador en el código y agregar los nuevos desgloses. |
| Estadísticas por talla/medida | Pendiente | Definir y mostrar rankings por talla, con filtro de categoría. |
| Captura de género del comprador | Pendiente de integración | La columna se ejecutó manualmente en MySQL según la conversación, pero falta incorporarla al esquema versionado, al registro y lectura de ventas y a la interfaz. |
| Cuotas y abonos parciales | Implementado en código | Incluye planes, cuotas, vencimientos, abonos y cálculo de saldos. |
| Migración MySQL para cuotas | Pendiente de ejecutar por el equipo | Ejecutar una vez `src/gedenaz/data/installment_migration.sql` en Workbench y verificar la conexión de la aplicación. |
| Pruebas con MySQL real de pagos | Pendiente | Las pruebas automatizadas locales validan la lógica en memoria; falta validar el ciclo completo contra la base del equipo. |

## 5. Equipo y responsabilidades propuestas

Se conservan los roles establecidos en el plan de trabajo. La asignación de pruebas, integración y revisiones se comparte para que cada área tenga un responsable principal y apoyo.

| Integrante | Responsabilidad principal | Apoyo |
|---|---|---|
| **Francisco Jara** | Jefatura de proyecto, backend, lógica de negocio, modelo y persistencia MySQL. | Revisión técnica, integridad transaccional e integración. |
| **Sebastian Perez** | Interfaz Tkinter y experiencia de uso de inventario, ventas, calendario y estadísticas. | Revisión visual y pruebas de aceptación. |
| **Nicolas Silva** | Interfaz de usuario, integración de pantallas y pruebas funcionales/regresión. | Coordinación técnica con backend y soporte al entorno. |
| **Cristóbal Sierra Porras** | Especificaciones, manuales, informes y material de presentación. | Diseño de casos de prueba, revisión de requisitos y aceptación funcional. |

## 6. Estimación de horas-hombre por paquete

Cada número representa horas de trabajo de una persona. Las horas simultáneas de dos integrantes se suman como h-h, aunque el tiempo calendario resulte menor.

| Paquete de trabajo | Francisco | Sebastian | Nicolas | Cristóbal | Total |
|---|---:|---:|---:|---:|---:|
| 1. Levantamiento, alcance, requisitos, arquitectura y planificación | 3 | 2 | 2 | 5 | 12 |
| 2. Entorno, conexión MySQL, modelo de datos y migraciones | 12 | 2 | 4 | 2 | 20 |
| 3. CRUD de productos, validaciones, búsqueda y detalle | 10 | 15 | 8 | 5 | 38 |
| 4. Venta, stock, boleta interna, historial y anulación | 10 | 10 | 8 | 5 | 33 |
| 5. Material, talla, destinatario, género comprador y estadísticas asociadas | 7 | 8 | 8 | 5 | 28 |
| 6. Estadísticas generales y calendario de ventas | 4 | 8 | 7 | 5 | 24 |
| 7. Cuotas, calendario de pagos y abonos parciales | 9 | 9 | 8 | 5 | 31 |
| 8. Integración, pruebas finales, manual, informes y demo | 5 | 6 | 10 | 18 | 39 |
| **Total estimado por integrante** | **60** | **60** | **55** | **50** | **225 h-h** |

### Lectura de la estimación

- **Esfuerzo total estimado:** 225 horas-hombre.
- **Promedio de referencia:** 56,25 h-h por integrante.
- **Desglose estimado por integrante:** Francisco, 60 h-h principalmente en backend/base de datos; Sebastian, 60 h-h principalmente en interfaz; Nicolas, 55 h-h en interfaz, integración y pruebas; Cristóbal, 50 h-h en documentación, validación y presentación.
- El desglose es una estimación de planificación, no una medición de productividad ni un registro de lo que ya trabajó cada integrante.
- La estimación contempla una primera entrega funcional del alcance descrito, sin incorporar requisitos futuros listados como fuera de alcance.

## 7. Secuencia sugerida y dependencias

| Orden | Paquete | Dependencia principal | Criterio para darlo por terminado |
|---:|---|---|---|
| 1 | Requisitos y arquitectura | Ninguna | Requisitos revisados por el equipo y alcance acordado. |
| 2 | Modelo de datos y entorno | 1 | Esquema y migraciones ejecutan en una base de pruebas; entorno documentado. |
| 3 | Inventario CRUD | 2 | RF1–RF4 cumplen validaciones y aceptación del usuario. |
| 4 | Venta y boleta | 2 y 3 | Venta completa actualiza stock atómicamente y deja historial consultable. |
| 5 | Género, material y tallas | 4 | Comprador y destinatario se distinguen; snapshots históricos se preservan. |
| 6 | Estadísticas y calendario | 4 y 5 | Desgloses coinciden con datos de prueba; calendario excluye anuladas. |
| 7 | Cuotas y abonos | 4 | Se crean vencimientos y los abonos actualizan los saldos sin exceder la cuota. |
| 8 | Integración y cierre | 3–7 | Suite de regresión, prueba MySQL, manual, informe y demostración listos. |

## 8. Validación recomendada

1. Revisar esta estimación entre los cuatro integrantes y corregir horas según lo que ya se ejecutó o lo que indique la Carta Gantt oficial.
2. Separar en un registro semanal las horas reales por integrante y paquete; no reemplazar esta estimación con horas trabajadas sin evidencia.
3. Crear casos de prueba para ventas completas, anulaciones, datos no informados, cuotas con redondeo, vencimientos al cierre de mes, pagos parciales, pagos completos y exceso de abono.
4. Ejecutar migraciones y validar las nuevas operaciones contra una base MySQL de pruebas antes de la base con datos reales.
5. Cerrar RF8 y los desgloses de estadísticas por género y talla antes de considerar completas todas las necesidades acordadas para análisis de demanda.
