# Informe de implementación — HU-01 Onboarding guiado de wallet para el MVP

**VEREDICTO: RECHAZADO**

## Alcance de la revisión

La evaluación se basa únicamente en las especificaciones e informes proporcionados en el historial. No se tuvo acceso al repositorio ni se ejecutaron herramientas; por tanto, no se modificó código y no se pudo verificar una implementación, sus contratos ni sus pruebas.

Este veredicto indica que **no hay evidencia suficiente para aceptar la tarea**, no que se haya comprobado un defecto específico en el producto.

## Criterios de aceptación

| # | Criterio | Resultado | Evidencia |
|---|---|---|---|
| 1 | Mostrar la secuencia y el paso actual; bloquear datos ausentes o inválidos con instrucciones accionables y conservar los datos válidos. | **No verificado** | Hay una especificación frontend, pero no se proporcionó código ni evidencia visual o de pruebas. |
| 2 | Validar en backend el OTP fijo `123456`; rechazar otros códigos y no solicitar ni enviar SMS. | **No verificado** | El comportamiento está descrito en la especificación backend; no se aportó implementación ni pruebas ejecutadas. |
| 3 | Enviar al mock KYC `documentType=TEST` y documento ficticio con prefijo `TEST-`; reflejar su estado sin inferir requisitos reales. | **No verificado** | No se inspeccionó el cliente KYC ni se observó una petición al mock. |
| 4 | Activar la wallet solo con `APPROVED`/`ACTIVE`; informar pendiente o rechazo sin presentarla como activa. | **No verificado** | No hay código, respuestas observadas ni pruebas de integración disponibles. |
| 5 | Permitir resolver una revisión pendiente con `ACTIVE` o `REJECTED`, consultando el estado final del mock. | **No verificado** | El flujo está especificado, pero no se verificó su implementación. |
| 6 | Ante `503 KYC_UNAVAILABLE`, informar el fallo, mantener la wallet inactiva y permitir reintentar sin afirmar un resultado KYC. | **No verificado** | No se aportaron pruebas con un mock que simule la indisponibilidad. |
| 7 | Registrar inicio, finalización de pasos y cierre con ID y timestamps, sin valores sensibles; marcar como incompleto el cierre previo al envío. | **No verificado** | No se proporcionó esquema implementado, consulta de eventos ni inspección de logs. |
| 8 | Medir inicio hasta envío exitoso, reportar KYC y activación aparte, mostrar mediana observada y presentar tres minutos solo como referencia. | **No verificado** | No se aportó el reporte implementado ni pruebas con reloj controlado. |
| 9 | Rechazar tipo distinto de `TEST` o documento que no cumpla `TEST-` antes de llamar al mock. | **No verificado** | No se inspeccionó la validación backend ni se verificaron llamadas al proveedor. |
| 10 | No crear ni procesar pagos; excluir MAU y CAC del resultado. | **No verificado** | No se inspeccionaron endpoints, servicios ni respuestas del reporte. |

## Pruebas y builds

No se ejecutaron pruebas. En particular, quedan pendientes:

- `mvn test` en `output/backend-quarkus`.
- `npm test` y `npm run build` en `output/frontend-angular`.
- Pruebas de integración con el mock para OTP, estados KYC, resolución manual, indisponibilidad y reintentos.
- Revisión responsive y accesible en viewport móvil y de escritorio.
- Verificación de eventos, logs, duplicados y cálculo de medianas.

No se atribuyen resultados exitosos o fallidos a comandos que no se ejecutaron.

## Bloqueos y riesgos pendientes

1. **Acceso y autorización:** los informes previos señalan que no están definidos el mecanismo de autenticación, la titularidad de los flujos ni quién puede consultar el reporte o solicitar una decisión de demo. Esta política debe acordarse antes de exponer los endpoints.
2. **Contrato del mock:** se deben confirmar los esquemas exactos de solicitudes y respuestas, incluidos identificadores y estados, contra el mock real.
3. **Contrato frontend/backend:** deben confirmarse las respuestas y errores de los endpoints propios, incluido el DTO de `/report`.
4. **Protección de datos:** debe verificarse con código y pruebas que OTP, teléfono y documento no se registren en logs, eventos, trazas ni analítica.
5. **Concurrencia e idempotencia:** debe probarse que solicitudes concurrentes no crean verificaciones duplicadas y que un resultado ambiguo no provoca un nuevo `POST` automático.

## Conclusión

No se puede aprobar HU-01 con la evidencia disponible. La documentación describe un diseño y una estrategia de pruebas, pero no demuestra que el flujo esté implementado ni que los criterios de aceptación se cumplan. Para reconsiderar el veredicto se requiere acceso a los archivos del proyecto, ejecución de las pruebas indicadas y evidencia de integración con el mock.