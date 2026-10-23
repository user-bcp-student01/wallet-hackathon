# Revisión de Chapter

VEREDICTO: RECHAZADO

## Alcance y evidencia

Se revisó el contrato de los agentes, el flujo de seis y siete roles, el checkpoint/aprobación humana y las pruebas locales. `output/` está vacío y no hay un Issue/feature seleccionado ni criterios concretos del producto. Por eso este informe evalúa si el pipeline puede satisfacer los criterios de revisión solicitados; no afirma incompatibilidades de una feature ni declara seguro un producto no disponible.

La guía del proyecto asigna a Chapter la comparación de cada criterio con entregables aprobados y exige que no invente ejecuciones ni reemplace aprobaciones humanas ([MEJORA_TU_AGENTE.md](MEJORA_TU_AGENTE.md#L22-L30)). La suite del pipeline pasó **5/5 pruebas** con `.venv`; sus respuestas de agentes son simuladas y comprueba transmisión de contexto, guardado/reanudación y flujo de roles, no la corrección funcional de una feature ([tests/test_workflow.py](tests/test_workflow.py#L23-L48), [tests/test_workflow.py](tests/test_workflow.py#L60-L67), [tests/test_workflow.py](tests/test_workflow.py#L128-L136)).

## Contraste de criterios

| Criterio de aceptación de esta revisión | Arquitectura y persistencia | Implementación | Pruebas | Seguridad | Resultado |
| --- | --- | --- | --- | --- | --- |
| Contrastar cada criterio con arquitectura, persistencia, código, pruebas y seguridad | Arquitectura pide alinear componentes y API con los criterios, pero no sugiere un formato de contrato verificable. Datos define esquema/migraciones solo en el modo opcional de siete roles. | Backend refiere a contratos aprobados de Arquitectura y Datos; en el modo de seis roles también asume persistencia. Frontend tiene un contrato detallado y prohíbe inventar endpoints/campos. | Testing pide casos positivos, negativos, de borde e integración, pero no exige matriz criterio-caso-resultado en el prompt actual. | Seguridad enumera áreas de revisión, pero no exige ubicación, impacto ni estado de evidencia. | **No satisfecho:** los criterios llegan a los agentes, pero Chapter no debe reportar trazabilidad por criterio y los contratos requeridos no son uniformes ([agents/architect.py](agents/architect.py#L10-L20), [agents/data.py](agents/data.py#L10-L22), [agents/backend.py](agents/backend.py#L10-L20), [agents/frontend.py](agents/frontend.py#L8-L28), [agents/testing.py](agents/testing.py#L10-L20), [agents/security.py](agents/security.py#L10-L20), [agents/chapter.py](agents/chapter.py#L10-L20)). |
| Detectar contratos incompatibles, criterios sin cobertura y hallazgos pendientes | En modo de siete roles, el diseño de Datos precede a Backend y se añade una nota específica para que Chapter revise compatibilidad. En modo de seis roles no existe ese artefacto; Backend absorbe persistencia, pero Chapter no recibe una instrucción equivalente. | Outputs aprobados se agregan como contexto; cada output puede truncarse a 8.000 caracteres y se etiqueta como truncado. Chapter no recibe la regla de tratar contexto ausente/truncado como no verificable. No hay artefactos reales para comparar en este workspace ([main.py](main.py#L848-L855), [main.py](main.py#L996-L1002)). | Las pruebas confirman que llega texto de outputs previos, no que el agente detecte una contradicción ni una cobertura faltante. | No se exige bloquear un veredicto positivo si hay hallazgos de seguridad abiertos. | **No verificable para una feature; control insuficiente en ambos modos.** No se afirma una incompatibilidad concreta sin contratos reales. |
| Por observación, indicar responsable, cambio y verificación | La guía asigna roles y entregables, pero Chapter no está instruido para asignar dueño por hallazgo. | La salida esperada de Chapter solo requiere un informe con uno de dos veredictos. Seguridad tampoco exige todos los campos de hallazgo que sí describe la guía. | No hay aserciones de contrato para responsable, corrección y comprobación. | Ubicación, impacto, corrección y verificación deben aparecer según la guía, pero no están garantizados por `agents/security.py` ([MEJORA_TU_AGENTE.md](MEJORA_TU_AGENTE.md#L26-L28)). | **No satisfecho.** |
| Justificar veredicto con evidencia y señalar pruebas pendientes | No hay especificaciones ni salidas aprobadas de una feature bajo `output/`. | Chapter no distingue evidencia observada de afirmaciones ni especifica cómo tratar artefactos faltantes. | La suite es simulada; `NO EJECUTADO` aparece en un output de prueba y se verifica su paso al contexto, no que el informe final lo marque como pendiente. | El prompt de Seguridad no prohíbe afirmar seguridad sin evidencia, pese a que la guía lo exige. | **No satisfecho como garantía; ejecución del producto pendiente.** |
| Conservar aprobaciones humanas | El flujo normal solicita aprobar/rechazar/reintentar y persiste el estado aprobado en checkpoint ([main.py](main.py#L996-L1037)). | Ante `EOFError`, `hitl_approve` retorna `("s", "")`; se guarda el output y se avanza como si hubiera aprobación humana ([main.py](main.py#L784-L814), [main.py](main.py#L1017-L1028)). | Las pruebas reemplazan `hitl_approve` con decisiones simuladas y no cubren EOF. | Es un bypass comprobado del control de aprobación, no una aprobación humana válida. | **No satisfecho; bloqueante.** |
| Entregar `chapter_review.md` con veredicto, motivos y correcciones sin sustituir aprobaciones | El rol Chapter tiene `SPEC_FILE` y el flujo guarda los outputs bajo `output/specs/`; la guía exige el informe con motivos/correcciones ([agents/chapter.py](agents/chapter.py#L5-L20), [main.py](main.py#L605-L611)). | El nombre del artefacto está configurado, pero el prompt no exige motivos, matriz, responsables, verificaciones ni pruebas pendientes. Este documento es una revisión estática y no aprueba pasos del pipeline. | La suite verifica guardado de archivos, no el contenido semántico de un informe real. | El informe no reemplaza decisiones de responsables ni autoriza por sí mismo un despliegue. | **Parcial:** existe el mecanismo de salida, no el contrato que garantiza el contenido requerido. |

## Hallazgos y correcciones

### H1. EOF se convierte en aprobación humana

**Responsable:** propietario del flujo HITL (`main.py`).

**Evidencia:** `hitl_approve` devuelve `("s", "")` ante `EOFError`. El bucle principal interpreta `s` como aprobación, guarda el output y checkpoint como `approved`, y puede avanzar sin intervención humana ([main.py](main.py#L784-L814), [main.py](main.py#L1017-L1028)).

**Cambio requerido:** Fallar de forma cerrada ante EOF: abortar o mantener el paso sin aprobar. No guardar como aprobado ni iniciar el rol siguiente sin decisión explícita.

**Verificación:** Prueba unitaria con `input` que lanza `EOFError`; comprobar que no retorna aprobación. Prueba de integración del flujo que confirme que no se crea checkpoint aprobado ni se ejecuta el siguiente rol. Repetir para interrupción de teclado.

### H2. Chapter no tiene contrato de revisión verificable

**Responsable:** Chapter (`agents/chapter.py`); Arquitectura, Datos, Backend, Pruebas y Seguridad para los contratos fuente.

**Evidencia:** La instrucción de Chapter solo pide una comparación general y un veredicto. Frontend sí prescribe contrato y comprobaciones concretas, pero los prompts actuales de Arquitectura, Pruebas y Seguridad no exigen trazabilidad completa ni los campos de evidencia indicados por la guía. El contexto puede truncarse por output y Chapter no tiene instrucción explícita de marcar la parte truncada o ausente como pendiente ([agents/chapter.py](agents/chapter.py#L10-L20), [agents/frontend.py](agents/frontend.py#L8-L28), [agents/testing.py](agents/testing.py#L10-L20), [agents/security.py](agents/security.py#L10-L20), [main.py](main.py#L848-L855)).

**Cambio requerido:** Exigir una fila por criterio con evidencia/artefacto, contrato de arquitectura, persistencia cuando aplique, implementación, prueba, seguridad y estado `CUMPLE`, `NO CUMPLE` o `NO VERIFICABLE`. Añadir hallazgos con responsable, ubicación, impacto, cambio y verificación; incluir pruebas pendientes. Información ausente o truncada debe quedar no verificable y no respaldar `APROBADO`. Alinear los prompts fuente con este formato.

**Verificación:** Pruebas de contrato para la tarea y salida de Chapter que fallen al omitir cualquier criterio/campo; incluir criterios sin cobertura, contradicción entre API y persistencia, hallazgo de seguridad abierto, evidencia truncada y prueba `NO EJECUTADO`. Ejecutar en modos de seis y siete roles.

### H3. Propiedad de persistencia y revisión varía por modo

**Responsable:** Arquitectura y Backend en modo de seis roles; Datos, Backend y Chapter en modo de siete.

**Evidencia:** El agente Datos solo se activa opcionalmente. Backend indica que en el equipo de seis también cubre persistencia, mientras el contrato de Chapter solo recibe una instrucción explícita de revisar el modelo/migración en modo de siete ([agents/data.py](agents/data.py#L1-L22), [agents/backend.py](agents/backend.py#L10-L20), [main.py](main.py#L996-L1002)). El workspace no contiene un feature que permita demostrar un conflicto concreto.

**Cambio requerido:** Definir explícitamente quién produce y aprueba el contrato de persistencia en cada modo. En modo de seis, pedir a Arquitectura/Backend un contrato de datos verificable y a Chapter revisar el esquema, migraciones y compatibilidad cuando haya persistencia; registrar `NO APLICA` con justificación cuando no la haya.

**Verificación:** Casos de prompt/salida para ambos modos: feature persistente con migración, feature persistente sin rol Datos y feature sin persistencia. Verificar propietario, contrato, cobertura de prueba e integración con backend.

### H4. Evidencia de feature y pruebas de producto ausentes

**Responsable:** Ingeniería de Pruebas y responsable humano de ejecución; Chapter registra pendientes.

**Evidencia:** `output/` está vacío. Pasan cinco pruebas del pipeline, pero usan respuestas simuladas y no compilan ni ejecutan código del producto ni migraciones ([tests/test_workflow.py](tests/test_workflow.py#L60-L67), [tests/test_workflow.py](tests/test_workflow.py#L90-L99), [tests/test_workflow.py](tests/test_workflow.py#L128-L136)).

**Cambio requerido:** Con un Issue real, conservar criterios, outputs aprobados y resultados reproducibles. Relacionar cada criterio con pruebas de backend/frontend, integración y persistencia aplicable; registrar `EJECUTADO`, `FALLIDO` o `NO EJECUTADO` con evidencia. No inferir cobertura por la mera presencia de texto en el prompt.

**Verificación pendiente:** Pruebas funcionales y de integración del feature, build de backend y frontend, aplicación/verificación de migraciones si aplican, y comprobaciones de seguridad. No se ejecutaron porque no hay feature ni artefactos disponibles.

### H5. Informe de seguridad no garantiza hallazgos accionables

**Responsable:** Revisor de Seguridad (`agents/security.py`).

**Evidencia:** El prompt enumera autenticación, autorización, entradas, secretos, datos sensibles e inyección y pide hallazgos/correcciones/comprobaciones; no obliga a informar ubicación e impacto, enumerar pendientes o evitar una afirmación de seguridad sin evidencia, requisitos presentes en la guía ([agents/security.py](agents/security.py#L10-L20), [MEJORA_TU_AGENTE.md](MEJORA_TU_AGENTE.md#L26-L28)). No hay código de feature que permita afirmar una vulnerabilidad concreta.

**Cambio requerido:** Hacer obligatorios ubicación, impacto, evidencia, corrección, comprobación y estado de cada hallazgo; reportar pendientes y prohibir declarar seguridad verificada sin evidencia ejecutada.

**Verificación:** Validar la salida contra casos con entrada no confiable, acceso no autorizado, secreto expuesto y hallazgo sin resolver; confirmar que el informe identifica evidencia/ubicación, dueño, corrección y comprobación, y que no declara seguridad ante pruebas pendientes.

## Pruebas pendientes para reconsiderar

- Corregir H1 y añadir las pruebas unitarias/de integración de EOF e interrupción antes de aceptar cambios al flujo HITL.
- Implementar H2 y H3 y validar el contrato de Chapter en los modos de seis y siete roles, incluidos faltantes, contradicciones y truncamiento.
- Implementar H5 y validar informes de seguridad con hallazgos y pendientes explícitos.
- Seleccionar un Issue real y obtener artefactos aprobados; ejecutar y registrar pruebas funcionales, integración, compilación, persistencia/migración y seguridad que correspondan al feature.
- Obtener las aprobaciones humanas de cada etapa. Este veredicto no las sustituye.