# security_report.md — HU-01 Onboarding guiado de wallet para el MVP

**Fecha:** 2026-10-23  
**Estado:** revisión documental; **no se proporcionó código del producto ni evidencia de ejecución**. Los riesgos de implementación que siguen son potenciales, no vulnerabilidades comprobadas. Se revisaron los criterios de aceptación y las especificaciones compartidas de arquitectura, backend y frontend.

## Resumen y alcance

La prioridad para la hackatón es comprobar que cada flujo solo pueda ser consultado o modificado por quien corresponda, que el servidor sea la autoridad sobre el estado de la wallet y que solicitudes repetidas no produzcan verificaciones o eventos inconsistentes. También hay que verificar que datos de prueba no terminen en logs o analítica.

Las rutas de API descritas en las especificaciones son propuestas; no se verificaron contra una implementación ni contra un contrato aprobado por Arquitectura. Los controles de autenticación, autorización y titularidad no están definidos suficientemente para confirmar cómo deben aplicarse. Los cambios de contrato deben coordinarse con **Architect**, no introducirse unilateralmente.

No se encontró evidencia para confirmar una inyección, exposición de secretos, creación de pagos ni filtración efectiva de datos. Tampoco hay código con el que descartarlas.

## Riesgos detectados

### SEC-01 — Autenticación, autorización y acceso a flujos de otras personas

- **Severidad:** P1 — Alta si la API resulta accesible a participantes no confiables; exposición y vulnerabilidad **no comprobadas**.
- **Estado:** brecha de especificación confirmada; riesgo en la implementación pendiente de verificar.
- **Archivo y ubicación:** no hay archivos de código disponibles. Referencias documentales: sección de configuración de `backend_spec.md` (la protección de endpoints queda a controles disponibles) y supuestos pendientes de `user_story.md` (proveedor de identidad, sesión y roles sin definir).
- **Escenario:** una persona sin autenticar, o con acceso a un `flowId` ajeno, consulta o modifica ese flujo; por ejemplo, solicita una decisión `ACTIVE`, lo cierra o consulta datos del reporte.
- **Impacto:** alteración del resultado de la demo, activación falsa de la wallet o acceso a información del flujo. Aunque la feature excluye pagos, el estado de wallet no debe poder manipularse desde otro flujo o usuario.
- **Evidencia observada:** las especificaciones enumeran operaciones para iniciar, consultar, enviar y resolver flujos, pero no establecen una identidad, un mecanismo de autenticación ni una regla comprobable de propiedad del flujo. La decisión de demo `ACTIVE` también requiere aclarar quién está autorizado a solicitarla.
- **Corrección propuesta:** exigir autenticación y comprobar en el servidor la titularidad del flujo en cada operación, incluida decisión y cierre. Restringir el reporte conforme a una decisión de producto sobre quién puede verlo. Acordar con Producto si la decisión de demo la puede solicitar cualquier titular o requiere un permiso adicional. Coordinar con Architect cualquier ajuste a las rutas, errores o contrato de autenticación.
- **Comprobación reproducible de la corrección — NO EJECUTADO:** con dos identidades de prueba, A y B, crear un flujo con A e intentar con B consultarlo, enviar OTP/KYC, resolverlo y cerrarlo. Comprobar que A puede usar su flujo, B no puede acceder al de A y las solicitudes sin credenciales son rechazadas. Repetir para el reporte según la política acordada. El formato de credenciales y los códigos HTTP esperados deben acordarse con Architect; no están definidos en la evidencia disponible.

### SEC-02 — Solicitudes repetidas y consistencia de estado, wallet y eventos

- **Severidad:** P2 — Media; duplicados y corrupción de estado **no comprobados**.
- **Estado:** riesgo potencial; hay una mitigación descrita, pero no se verificó código ni pruebas.
- **Archivo y ubicación:** no hay archivos de código disponibles. Referencia documental: sección “Estados y transacciones” de `backend_spec.md`, que describe `SUBMITTING`, comparación de estado y manejo distinto de un `503` explícito y un resultado de red ambiguo.
- **Escenario:** se envían solicitudes `submit` simultáneas o repetidas, se repite una decisión/cierre o se pierde la respuesta del mock después de que este haya creado la verificación.
- **Impacto:** verificaciones KYC duplicadas, resultados contradictorios, wallet marcada activa sin resultado final autoritativo o eventos duplicados que distorsionen la duración y los reportes.
- **Evidencia observada:** `backend_spec.md` declara que una comparación de estado impide altas duplicadas y que un resultado ambiguo produce `SUBMISSION_UNKNOWN`; no se proporcionó la implementación ni evidencia de pruebas concurrentes que lo acrediten. Tampoco se pudo comprobar idempotencia de decisiones, cierres o eventos.
- **Corrección propuesta:** hacer atómica la transición a `SUBMITTING` y el registro de eventos asociados; garantizar que solicitudes repetidas del mismo flujo no creen otro KYC. No repetir automáticamente un `POST` cuyo resultado sea ambiguo. Reintentar solo cuando el contrato del mock permita concluir que no se creó una verificación. Asegurar que la activación dependa del estado final autoritativo y que decisiones y cierres repetidos no creen transiciones o eventos contradictorios. Confirmar estas semánticas con Architect y con el contrato del mock.
- **Comprobación reproducible de la corrección — NO EJECUTADO:** con H2 aislada y un mock que cuente llamadas, disparar simultáneamente dos `submit` para el mismo flujo y comprobar que hay como máximo una creación. Repetir la misma solicitud tras una respuesta perdida y comprobar que no se crea otra verificación. Simular un `503` explícito y un timeout ambiguo por separado; verificar el estado y la posibilidad de reintento de cada caso. Repetir decisiones y cierres y comprobar transiciones y eventos consistentes.

### SEC-03 — Exposición de OTP, documento de prueba y datos de flujo

- **Severidad:** P2 — Media, condicionada a que los datos aparezcan en logs, trazas, errores o analítica; exposición **no comprobada**.
- **Estado:** riesgo potencial.
- **Archivo y ubicación:** no hay archivos de código disponibles. Referencias documentales: criterio de aceptación sobre eventos, `backend_spec.md` (eventos mínimos) y `frontend_spec.md` (mensajes sin valores personales).
- **Escenario:** un log HTTP, una excepción, una traza del cliente KYC o una herramienta de analítica registra el cuerpo de una petición. En el alcance definido se prohíben datos reales, pero el documento de prueba y el OTP siguen siendo valores que no deben incorporarse a eventos o logs.
- **Impacto:** exposición innecesaria de datos de identificación —o de información que podría convertirse en personal si se usa incorrectamente la demo— y correlación de actividad mediante identificadores de flujo.
- **Evidencia observada:** las especificaciones prohíben incluir OTP, teléfono y documento en eventos y logs, pero no se aportaron configuración de logging, código de eventos, telemetría, trazas ni manejadores de errores para verificarlo. No hay evidencia de una filtración efectiva.
- **Corrección propuesta:** no registrar cuerpos de solicitud o respuesta KYC; usar una lista permitida de propiedades para eventos; redactar datos antes de enviarlos a logs o trazas; devolver errores de aplicación sin cuerpos internos del proveedor. Evitar enviar `flowId` u otros identificadores a analítica externa sin decisión explícita de Producto y revisión de privacidad.
- **Comprobación reproducible de la corrección — NO EJECUTADO:** completar un flujo con valores sintéticos únicos, por ejemplo, un documento `TEST-SECURITY-SENTINEL`, y buscar el documento, `123456` y cualquier fixture de teléfono en logs, trazas, eventos, respuestas de error y analítica capturada. Verificar que los eventos solo contengan las propiedades aprobadas y timestamps. Examinar también el cliente HTTP y la configuración de logging; una búsqueda en logs por sí sola no prueba que no se registren datos en otros destinos.

### SEC-04 — Definición inconsistente o pendiente de métricas

- **Severidad:** P3 — Baja para seguridad técnica; relevante para privacidad e integridad de resultados.
- **Estado:** inconsistencia documental confirmada; implementación y métricas emitidas no verificadas.
- **Archivo y ubicación:** no hay archivos de código disponibles. Referencias: criterio de aceptación sobre duración; sección “Analítica y duración” de `frontend_spec.md`, que deja pendiente confirmar la frontera temporal; sección de duración de `backend_spec.md`, que propone `submittedAt - startedAt`.
- **Escenario:** distintos componentes presentan duraciones calculadas con fronteras diferentes, o se agregan métricas de usuarios activos o atribución de adquisición sin una definición aprobada.
- **Impacto:** reportes no comparables y recolección de identificadores o datos de atribución que no son necesarios para la demo.
- **Evidencia observada:** hay definiciones candidatas de duración en los criterios y en `backend_spec.md`, pero la frontera oficial figura pendiente en `frontend_spec.md`. No se puede tratar una de ellas como definición aprobada. MAU y CAC están excluidos; no hay una definición proporcionada de usuarios activos o atribución de adquisición.
- **Corrección propuesta:** solicitar a Producto la decisión explícita sobre la frontera de duración y cómo reportar por separado espera KYC y activación. No presentar la fórmula como oficial hasta esa decisión. Mantener fuera del reporte MAU/CAC y no añadir métricas de usuarios activos o atribución de adquisición sin definición y aprobación de Producto. Producto y Cumplimiento deben confirmar las decisiones de privacidad o uso de datos que correspondan; este informe no presupone requisitos regulatorios.
- **Comprobación reproducible de la corrección — NO EJECUTADO:** una vez aprobada la definición, usar un reloj controlado para probar inicio, envío, espera KYC, activación y flujos incompletos. Verificar que el resultado aplique la misma fórmula y población en backend y frontend, excluya los flujos no completados según la decisión y no incluya métricas no aprobadas. La frontera temporal permanece **pendiente**.

## Pendientes de verificación: entradas, inyección, secretos y pagos

No se observaron archivos ejecutables que permitan evaluar estas áreas. Lo siguiente no es una afirmación de vulnerabilidad:

- **Validación e inyección:** las especificaciones indican validación de `documentType=TEST`, prefijo `TEST-` y OTP, pero no permiten verificar controles del servidor, acceso a base de datos, codificación de salida, límites de tamaño ni manejo de caracteres de control. Confirmar validación en backend, consultas parametrizadas y ausencia de interpolación de entrada en SQL, logs o comandos. No inventar restricciones al sufijo `TEST-`; acordarlas con Producto/Architect si hacen falta. Verificación pendiente: pruebas con valores malformados y caracteres de control, comprobando rechazo o tratamiento seguro y ausencia de llamadas al mock para entradas inválidas.
- **Secretos y configuración:** no hay evidencia de secretos expuestos ni información suficiente para revisar archivos de configuración o despliegue. Confirmar que la demo esté deshabilitada fuera del perfil aprobado, que `MOCK_BASE_URL` no sea controlable por una petición de usuario y que cualquier credencial del mock no esté en código, frontend, logs o repositorio. Verificación pendiente: inspección de configuración y repositorio, más comprobación de que el artefacto frontend no contiene credenciales.
- **Pagos y métricas excluidas:** las especificaciones excluyen pagos, MAU y CAC, pero no se proporcionó código para confirmar rutas, dependencias, llamadas salientes o campos del reporte. Verificación pendiente: inspeccionar rutas y llamadas del producto y confirmar que el reporte no expone MAU/CAC. No se deben añadir flujos de pagos por este cambio.

## Verificaciones realmente ejecutadas

**NO EJECUTADO:** no se ejecutaron comandos, pruebas, inspecciones de repositorio, peticiones HTTP, revisión visual ni pruebas con mock. No se recibió código del producto para comprobar los hallazgos. Por tanto, no se declara ejecutada ninguna corrección ni prueba.

## Verificaciones propuestas pendientes

Después de disponer del repositorio y de confirmar contratos:

1. Añadir pruebas de autorización cruzada, transiciones e idempotencia, privacidad de eventos/logs, validación de entradas y cálculo de métricas.
2. En `output/backend-quarkus`, ejecutar `mvn test` y las pruebas de integración con H2 aislada y un mock instrumentado.
3. En `output/frontend-angular`, ejecutar `npm test` y `npm run build`; revisar además la interfaz y que los mensajes no revelen valores ni estados inferidos.
4. Ejecutar pruebas de API con identidades de prueba y flujos distintos, una vez que Architect confirme el contrato de autenticación y errores.
5. Registrar resultados reales de cada comprobación; hasta entonces, todos los puntos anteriores siguen **NO EJECUTADO**.