# user_story.md — HU-01 Onboarding guiado de wallet para el MVP

> **Estado:** especificación propuesta; requiere validación y aprobación humana antes de implementarse.  
> **Comprobaciones descritas:** **NO EJECUTADO**. No se generó código ni se verificaron contratos existentes, pruebas o builds.  
> **Convención:** las rutas de la API propia y los modelos de datos de esta especificación son propuestas, no contratos ya implementados. Se conserva el contrato conocido del mock KYC, sujeto a confirmar sus esquemas completos.

## 1. Historia de usuario, alcance, exclusiones y supuestos pendientes

### Historia de usuario

Como participante de una demo de wallet, quiero recorrer un onboarding guiado desde un smartphone, validar un celular de prueba y enviar datos KYC ficticios, para conocer el resultado del mock sin confundir la demo con una verificación productiva ni presentar como activa una wallet que no esté aprobada.

### Alcance actual

- Aplicación responsive Angular 17 y monolito modular Quarkus 3.x con Java 17.
- Tres etapas visibles: **celular de prueba y OTP**, **datos KYC ficticios** y **resultado**.
- Validación del OTP fijo `123456` en backend, solo en configuración de demo. No se envía SMS.
- Validación local de `documentType=TEST` y prefijo `TEST-` antes de llamar al mock.
- Integración desde el backend con el mock existente para crear, consultar y resolver verificaciones KYC.
- Estados visibles que distinguen aprobación/activación, revisión pendiente, rechazo, indisponibilidad y resultado no confirmado.
- Persistencia efímera en H2 de estado del flujo y eventos mínimos. No se guardan documentos, OTP ni teléfono en eventos o logs.
- Medición de duración del recorrido hasta el envío de los pasos de usuario. Los tiempos KYC y de activación se informan por separado.
- Reporte de mediana observada solo sobre flujos enviados correctamente, y referencia de producto de **3 minutos** sin presentarla como resultado validado.
- Ningún pago, movimiento financiero, MAU o CAC.

### Exclusiones

- OTP real, envío de SMS, KYC productivo, datos personales o documentos reales.
- Pagos, procesamiento de operaciones financieras, saldos, reservas o movimientos.
- Consola de soporte o herramienta independiente para resolver revisiones manuales.
- Analítica de cohortes productivas, retención de largo plazo, MAU y CAC.
- Credenciales, capacidades o endpoints de un procesador de pagos.
- Afirmaciones de cumplimiento regulatorio.

### Supuestos pendientes y bloqueos

1. No se proporcionó evidencia del código, convenciones de API, modelo de autenticación ni configuración actual del repositorio. La API propia propuesta debe contrastarse con ellos.
2. Se debe confirmar el esquema exacto de petición y respuesta del mock KYC, incluidos los campos de estado, identificadores y decisión. Solo se consideran conocidos los métodos y rutas indicados en el contexto.
3. Falta definir el identificador de la fixture de celular de prueba, su presentación y cómo se valida. No se debe usar un número personal real.
4. Falta acordar los caracteres y longitud permitidos después de `TEST-`; el prefijo es obligatorio, pero no se inventa aquí una regla definitiva para el sufijo.
5. Se debe definir el proveedor de identidad, el mecanismo de sesión y los roles disponibles. La demo no debe exponerse sin control de acceso. El diseño asume que el backend recibe un principal autenticado, pero no presupone un proveedor concreto.
6. La decisión de demo `ACTIVE` o `REJECTED` debe estar restringida a la vista y al perfil de demo. Falta acordar si requiere un rol especial.
7. La instrumentación de cierre en una pestaña depende de una señal del navegador y no puede garantizarse si se pierde conectividad o el proceso se cierra abruptamente.
8. H2 es efímero y adecuado solo para el alcance de demo descrito. La retención, despliegue y uso de métricas fuera de una sesión de demo requieren decisión explícita.
9. No se propone habilitar OTP fijo ni mock KYC en un perfil productivo.

## 2. Arquitectura del monolito, módulos y recorrido de la petición

### Forma de despliegue y dependencias

Un único backend desplegable Quarkus, organizado como monolito modular. Angular 17 es la interfaz cliente y no llama directamente al mock KYC.

Las dependencias van hacia adentro:

```text
Angular
  → infraestructura/adapter/input (API REST Quarkus)
  → application/service (casos de uso)
  → domain/model y domain/port
  → infraestructura/adapter/output (H2 y cliente HTTP del mock)
```

Reglas de arquitectura:

- `domain/model/`: entidades y reglas puras; no importa `infrastructure/`.
- `domain/port/input/`: contratos de casos de uso invocados desde el exterior.
- `domain/port/output/`: contratos para persistencia, reloj, KYC y, en el futuro, pagos.
- `application/service/`: orquesta casos de uso y depende de puertos de dominio, no de adaptadores concretos.
- `infrastructure/adapter/input/`: recursos REST, validación de transporte y mapeo de DTOs.
- `infrastructure/adapter/output/`: persistencia H2 y cliente HTTP Java 17 para KYC.
- `infrastructure/config/`: configuración, perfiles, propiedades y ensamblado de adaptadores.

No se añaden microservicios, broker ni infraestructura distribuida. El mock KYC existente es un sistema externo de la demo, no un nuevo microservicio de esta solución.

### Módulos y responsabilidades

| Módulo | Responsabilidad |
|---|---|
| `wallet-onboarding` (dominio y aplicación) | Estados y transiciones permitidas, validación del flujo, medición y coordinación de los casos de uso. |
| API de onboarding | Autenticación del principal, autorización de titularidad del flujo, validación de entradas y respuestas HTTP estables. |
| Adaptador de persistencia | Guardar sesiones y eventos mínimos en H2; garantizar exclusión de envíos duplicados para un mismo flujo. |
| Adaptador KYC | Traducir el modelo interno al contrato del mock; crear, consultar y resolver una verificación. Es el único componente que llama al mock. |
| Angular | Captura guiada, conservación temporal del estado de formulario, accesibilidad y presentación fiel del estado que devuelve el backend. |
| Configuración | `MOCK_BASE_URL` configurable por ambiente/grupo y escenario de demo, con `APPROVED` por defecto. No codificar una URL de grupo ni permitir que el usuario elija el escenario. |
| Puerto futuro de pagos | Contrato interno sustituible, inactivo en HU-01. No agrega endpoints de pagos ni comportamiento financiero ahora. |

### Recorrido de una petición

1. Angular inicia el flujo mediante la API propia.
2. El adaptador REST comprueba autenticación, valida el formato y transforma el DTO en una llamada al puerto de entrada correspondiente.
3. El servicio de aplicación crea el identificador de flujo, persiste estado y evento de inicio a través del puerto de persistencia y devuelve el estado inicial.
4. Angular envía el identificador de fixture de celular y OTP. El backend valida localmente el OTP y el estado del flujo; no llama a servicios SMS.
5. Angular envía los datos de prueba. El backend valida `documentType=TEST`, el prefijo `TEST-` y el estado. En una transacción local persiste `SUBMITTING` y los eventos de envío; **no** persiste el documento.
6. Tras confirmar la transacción local, el servicio invoca el puerto KYC. El adaptador HTTP envía el documento ficticio al mock. No se mantiene una transacción de base de datos abierta durante la llamada remota.
7. El servicio traduce la respuesta del mock a estados del dominio, persiste el resultado y devuelve una respuesta estable a Angular.
8. Angular muestra el resultado del backend sin inferir requisitos KYC ni declarar activa una wallet por su cuenta. Solo se comunica `ACTIVE` cuando el resultado KYC autoritativo corresponda a aprobación/activación.
9. La consulta del flujo obtiene el estado persistido y las métricas aplicables. Los eventos y las respuestas no incluyen documento, OTP ni teléfono.

## 3. Contrato de API

### Convenciones

Las siguientes rutas son **propuestas** y deben cotejarse con las convenciones existentes antes de implementarlas:

```text
/api/v1/wallet-onboarding/flows
```

- Formato JSON UTF-8. Fechas ISO-8601 en UTC.
- Autenticación requerida mediante un principal autenticado. El método concreto (token, sesión u otro) está pendiente; no se presupone un proveedor de identidad.
- Cada flujo queda asociado en servidor al principal que lo creó. Ningún `userId`, `accountId` o titularidad se acepta como autoridad desde el cliente. Un principal distinto no puede consultar ni modificar el flujo ajeno.
- La política de respuesta para un flujo inexistente o ajeno debe evitar enumeración; se propone responder `404` en ambos casos.
- El backend no registra cuerpos de petición que puedan contener OTP o documento. El OTP se elimina de la memoria de trabajo tras validarlo; el documento solo se mantiene lo necesario para la llamada saliente.
- El escenario KYC es configuración de demo del servidor, `APPROVED` por defecto. No se acepta `scenario` en las peticiones de usuario.
- El cuerpo, identificador y respuesta exactos del mock deben confirmarse con su contrato antes de implementar el adaptador. No se deben reenviar al cliente cuerpos internos del mock.

### Rutas propuestas

| Método y ruta | Propósito y reglas |
|---|---|
| `POST /flows` | Iniciar flujo. Devuelve `201 Created`, ID opaco, estado `STARTED` y paso actual. |
| `POST /flows/{flowId}/phone-verification` | Validar fixture de celular y OTP local. OTP incorrecto devuelve `422`; no avanza ni llama a KYC. |
| `GET /flows/{flowId}` | Consultar estado, resultado, tiempos y mediana de demo aplicable. |
| `POST /flows/{flowId}/submission` | Enviar los datos ficticios. Se permite una sola transición de envío por flujo. |
| `POST /flows/{flowId}/decision` | Resolver una revisión pendiente con decisión de demo `ACTIVE` o `REJECTED`; el backend envía la decisión al mock y consulta el resultado final. |
| `POST /flows/{flowId}/close` | Registrar cierre explícito. El navegador puede intentar esta señal al salir, sin garantía de entrega. |

### Esquemas y validaciones

#### Iniciar flujo

Sin campos de identidad o datos personales en el cuerpo. El backend genera un `flowId` aleatorio y registra `FLOW_STARTED`.

Respuesta propuesta `201`:

```json
{
  "flowId": "7c0a6e8e-5d4a-4f42-8b46-8538c2a58e10",
  "status": "STARTED",
  "currentStep": "PHONE_OTP",
  "startedAt": "2026-10-23T18:00:00Z",
  "steps": ["PHONE_OTP", "TEST_DATA", "RESULT"]
}
```

El ID es ilustrativo, no un ID real. Debe autorizarse cada lectura y escritura del flujo por principal.

#### Validar teléfono de prueba y OTP

Petición propuesta:

```json
{
  "phoneFixtureId": "DEMO_PRIMARY",
  "otp": "123456"
}
```

`DEMO_PRIMARY` es un identificador simbólico propuesto, no un número telefónico; el identificador definitivo y la fixture están pendientes. La pantalla debe explicar que es un celular de prueba. No se transmite un número real ni se envía SMS.

- Validar que la fixture esté habilitada en el perfil de demo.
- Aceptar solo seis dígitos y verificar localmente contra `123456`.
- OTP correcto: transición `STARTED → OTP_VERIFIED`, evento `STEP_COMPLETED` para `PHONE_OTP`.
- OTP incorrecto o mal formado: `422 OTP_INVALID`, sin transición y sin llamada al mock.
- No guardar OTP o número de teléfono en persistencia, eventos ni logs. No incluirlos en errores.

#### Enviar datos KYC ficticios

Petición propuesta:

```json
{
  "documentType": "TEST",
  "document": "TEST-ONB-001"
}
```

El ejemplo es ficticio. El servidor exige `documentType` exactamente `TEST` y documento no vacío con prefijo `TEST-`. El conjunto de caracteres y longitud permitidos después del prefijo debe confirmarse con el contrato del mock. No aceptar ni convertir documentos reales.

- Validar estado `OTP_VERIFIED` antes del envío.
- Validar tipo y prefijo antes de cualquier llamada al mock.
- Registrar completado `TEST_DATA` y `FLOW_SUBMITTED` en el instante en que se han validado y enviado correctamente los pasos de usuario, antes de iniciar la llamada KYC. Ese instante termina la métrica del recorrido.
- Persistir `SUBMITTING` antes de llamar al mock. No persistir el documento.
- Una solicitud concurrente mientras esté `SUBMITTING` no debe crear otra verificación.
- Una solicitud repetida para un flujo ya enviado no crea otra verificación; el cliente debe consultar el flujo. Contenido diferente luego del primer envío devuelve conflicto y no reemplaza la solicitud original.
- No permitir una nueva llamada automática si el resultado de la creación es ambiguo.

Respuesta: representación del estado del flujo y, cuando exista, el resultado KYC normalizado. No se expone el documento ni es necesario exponer el ID interno del mock.

#### Consultar estado y resultado

`GET /flows/{flowId}` devuelve, como mínimo:

- `flowId`, `status`, `currentStep`, `walletStatus`, `startedAt`.
- `submittedAt` cuando corresponda; tiempos de KYC y activación separados si están disponibles.
- Resultado normalizado `APPROVED`, `MANUAL_REVIEW`, `REJECTED` o no confirmado, sin inferir más requisitos.
- `durationMetrics`: duración del usuario, mediana observada, tamaño de muestra y referencia de producto. Si no hay flujos enviados, la mediana es `null`; no se inventa una muestra.
- `walletStatus` solo puede ser `ACTIVE` cuando el estado autoritativo es `ACTIVE`. En revisión pendiente, rechazo, indisponibilidad o incertidumbre es `NOT_ACTIVE`.

Las métricas son efímeras y corresponden al ámbito de la demo. La respuesta no incluye MAU ni CAC.

#### Resolver revisión manual

Petición propuesta:

```json
{
  "decision": "ACTIVE"
}
```

Valores permitidos: `ACTIVE` o `REJECTED`. Solo se admite para un flujo cuyo último estado KYC conocido sea `MANUAL_REVIEW`/`PENDING`. El backend envía la decisión al mock y consulta el resultado final antes de reflejar un estado definitivo.

- `ACTIVE` confirmado por el mock: estado `ACTIVE` y wallet `ACTIVE`.
- `REJECTED` confirmado: estado `REJECTED` y wallet `NOT_ACTIVE`.
- No se activa la wallet basándose únicamente en la decisión solicitada.
- El acceso a esta decisión de demo requiere autorización, cuyo rol concreto está pendiente.
- Ante un timeout de resolución, no afirmar el resultado solicitado; informar que no pudo confirmarse y consultar el estado antes de permitir otra decisión.

#### Cierre

Petición propuesta:

```json
{
  "reason": "USER_EXIT"
}
```

`reason` es una clasificación no sensible; se debe acordar su catálogo definitivo. El resultado del cierre es `SUBMITTED` si ya ocurrió el envío exitoso de los pasos de usuario, e `INCOMPLETE` si no ocurrió. El cierre no altera un resultado KYC ni convierte una solicitud en exitosa. Cerrar una pestaña puede impedir que se entregue el evento; el evento es informativo.

### Errores HTTP

Formato propuesto tipo `application/problem+json`, sin detalles del proveedor ni valores de entrada sensibles:

```json
{
  "type": "about:blank",
  "title": "No se pudo validar el código",
  "status": 422,
  "code": "OTP_INVALID",
  "detail": "Verifica el código de demo e inténtalo de nuevo.",
  "traceId": "c8e24b65-4a89-4f10-a1ea-e7bf29263ec1",
  "fieldErrors": [
    {
      "field": "otp",
      "code": "OTP_INVALID",
      "message": "Ingresa el código de seis dígitos indicado para la demo."
    }
  ]
}
```

| HTTP | Código de aplicación | Uso |
|---|---|---|
| `400` | `INVALID_REQUEST` | JSON mal formado o estructura inválida. |
| `401` | `AUTHENTICATION_REQUIRED` | No hay principal autenticado. |
| `403` | `FORBIDDEN` | Principal autenticado sin permiso para una acción protegida. |
| `404` | `FLOW_NOT_FOUND` | Flujo inexistente o no accesible por el principal. |
| `409` | `FLOW_STATE_CONFLICT`, `SUBMISSION_IN_PROGRESS`, `SUBMISSION_UNKNOWN`, `DECISION_NOT_ALLOWED` | Estado incompatible, repetición concurrente o resultado incierto. |
| `422` | `OTP_INVALID`, `TEST_PHONE_FIXTURE_INVALID`, `TEST_DOCUMENT_INVALID`, `DOCUMENT_TYPE_INVALID` | Validación funcional; no se llama al mock si falla tipo o formato de documento. |
| `502` | `KYC_INVALID_RESPONSE` | Respuesta del mock inválida o incompatible; no activar. |
| `503` | `KYC_UNAVAILABLE` | El mock confirma indisponibilidad sin resultado KYC; el flujo puede reintentarse según las reglas descritas. |
| `504` | `KYC_RESULT_UNKNOWN` | Timeout o resultado ambiguo. El estado del flujo queda no confirmado y no se repite el `POST` a ciegas. |

Los errores `400`, `404` o `409` del mock se traducen a códigos internos seguros conforme a su significado confirmado. Nunca se devuelve su cuerpo sin filtrar. Un `429` no se considera reintentable automáticamente salvo que el contrato del mock confirme que no creó la verificación.

### Ejemplos negativos

Tipo inválido:

```json
{
  "documentType": "PASSPORT",
  "document": "TEST-ONB-001"
}
```

Respuesta propuesta: `422 DOCUMENT_TYPE_INVALID`; el adaptador no llama al mock.

Prefijo inválido:

```json
{
  "documentType": "TEST",
  "document": "DOC-ONB-001"
}
```

Respuesta propuesta: `422 TEST_DOCUMENT_INVALID`; el adaptador no llama al mock.

OTP incorrecto:

```json
{
  "phoneFixtureId": "DEMO_PRIMARY",
  "otp": "000000"
}
```

Respuesta propuesta: `422 OTP_INVALID`; el flujo no avanza.

## 4. Modelo de dominio, persistencia e invariantes transaccionales

### Estados del flujo

Estados base propuestos, consistentes con el diseño de la demo:

```text
STARTED
  → OTP_VERIFIED
  → SUBMITTING
      → PENDING
      → ACTIVE
      → REJECTED
      → SUBMISSION_UNKNOWN
```

- `STARTED`: flujo iniciado, teléfono de prueba/OTP aún sin validar.
- `OTP_VERIFIED`: OTP validado; datos de prueba pueden enviarse.
- `SUBMITTING`: envío de usuario validado y creación KYC en curso.
- `PENDING`: mock devuelve `MANUAL_REVIEW`/`PENDING`.
- `ACTIVE`: mock confirma `APPROVED`/`ACTIVE`.
- `REJECTED`: mock confirma rechazo.
- `SUBMISSION_UNKNOWN`: el backend no puede confirmar si el `POST` creó la verificación.

Ante un `503 KYC_UNAVAILABLE` explícito que confirme indisponibilidad sin creación, se vuelve a `OTP_VERIFIED`, se registra un código de error no sensible y se permite reintentar manualmente. Esto no se aplica a un timeout ambiguo.

No existe una transición que active la wallet por decisión del frontend. Una inconsistencia entre estado y resultado del mock, o una respuesta no interpretable, nunca produce `ACTIVE`.

### Persistencia conceptual en H2

- **Flujo:** ID opaco, principal propietario o referencia no reversible suficiente para autorización, estado, versión para control concurrente, marcas de tiempo y referencia KYC necesaria para consultar/resolver.
- **Eventos:** ID de evento, ID de flujo, tipo, paso, resultado y timestamp UTC.
- **Métricas:** se derivan de las marcas de tiempo de flujos enviados. La mediana excluye flujos incompletos y no enviados.
- **Configuración:** URL base del mock y escenario de demo del servidor; no se controla desde Angular.

No guardar en H2, eventos o logs: OTP, teléfono, documento, cuerpos HTTP del usuario o del mock, credenciales o secretos. El documento se usa transitoriamente para la petición al mock. El identificador externo KYC se conserva solo si es necesario para consultas y resolución.

H2 en memoria se pierde al reiniciar; los informes no representan cohortes persistentes. No se afirma que H2 cubra despliegues con varias instancias. Si se requiriera ese modo, habría que revisar persistencia compartida y garantías de concurrencia.

### Eventos y medición

Eventos mínimos:

- `FLOW_STARTED`
- `STEP_COMPLETED` con pasos `PHONE_OTP`, `TEST_DATA` y `RESULT` cuando el resultado se haya presentado en una respuesta del servidor
- `FLOW_SUBMITTED`
- `FLOW_CLOSED` con resultado `SUBMITTED` o `INCOMPLETE`

Cada evento incluye ID de flujo y timestamp UTC. No incluye OTP, teléfono, documento ni payloads. Se registra como máximo una finalización inicial por paso, evitando duplicados por refrescos.

Fórmulas:

- **Duración de usuario:** `FLOW_SUBMITTED.at - FLOW_STARTED.at`.
- **Mediana observada:** mediana de duraciones de flujos con `FLOW_SUBMITTED`; excluye incompletos.
- **Tiempo KYC:** desde la solicitud al mock hasta un estado final confirmado; queda sin duración final mientras siga pendiente.
- **Tiempo hasta activación:** desde el envío de usuario hasta la confirmación de `ACTIVE`. Se informa aparte y nunca se suma a la duración del usuario.
- **Referencia de producto:** `180000 ms` (3 minutos), rotulada como referencia, no como resultado observado.

Un cierre antes de `FLOW_SUBMITTED` es `INCOMPLETE` y no cuenta para la mediana. La duración no se presenta como evidencia del impacto de un lanzamiento.

### Invariantes transaccionales

- Validar autenticación, titularidad del flujo, estado y datos antes de efectuar cambios.
- La transición a `SUBMITTING` y los eventos asociados se confirman localmente antes de la llamada remota.
- No mantener una transacción H2 abierta durante una llamada HTTP.
- Aplicar control de concurrencia atómico (versión, actualización condicional o mecanismo local equivalente) para que solo una petición del mismo flujo inicie la creación KYC.
- Si una petición competidora encuentra `SUBMITTING`, responder conflicto o estado consultable; nunca crear otra verificación.
- Un resultado exitoso ya persistido no habilita repetir la creación KYC.
- Timeout o fallo de red ambiguo: persistir `SUBMISSION_UNKNOWN`, no repetir automáticamente ni presentar aprobación.
- Fallo explícito `503 KYC_UNAVAILABLE`: permitir reintento manual bajo las condiciones del contrato del mock.
- Respuesta KYC sin estado válido: no activar la wallet.
- Actualizar estado y evento de forma consistente en la transacción local. Las limitaciones de recuperación entre una respuesta remota y su persistencia deben cubrirse con pruebas y manejo de resultado incierto; el mock no ofrece deduplicación según el contexto.

## 5. Integración futura de pagos

**Fuera del alcance de HU-01.** Esta sección prepara límites arquitectónicos; no autoriza pagos, no define una API pública de pagos y no asume capacidades de un procesador. No se ejecutan cargos ni se crea un módulo operativo de pagos en esta entrega.

### Puerto futuro y sustitución del adaptador

En el límite del dominio se reservaría un puerto de salida de pagos, invocado por un servicio de aplicación. Un adaptador sustituible implementaría el puerto; ningún servicio de dominio, contrato Angular ni caso de uso dependería de un proveedor concreto. El puerto y el adaptador permanecen inactivos hasta aprobar el caso de negocio, el procesador y los requisitos de seguridad.

El frontend solo podría solicitar una operación a una API pública que se defina y consultar su estado. **Toda ejecución, confirmación contable o transición a pagado ocurriría en backend.** El cliente nunca acredita fondos ni declara éxito.

### Contrato interno propuesto

El contrato interno tendría, como mínimo:

- Identificador propio de operación.
- Clave de idempotencia aportada para la solicitud y alcance definido por identidad y operación.
- Importe decimal exacto y moneda explícita.
- Referencia de negocio no sensible.
- Estado, timestamps y código de resultado normalizado.
- Referencia externa opaca solo si el adaptador la necesita; nunca credenciales ni datos completos de tarjeta.

No se determina aquí el payload de un proveedor ni se inventa un endpoint externo.

Estados internos propuestos:

```text
ACCEPTED → PROCESSING → CONFIRMED
                     → DECLINED
                     → PENDING_RECONCILIATION
PENDING_RECONCILIATION → CONFIRMED | DECLINED
```

`ACCEPTED` o `PROCESSING` significan solicitud recibida/en curso, **no** pago confirmado. Un timeout después de haber enviado una solicitud puede dejarla en `PENDING_RECONCILIATION`; no se informa éxito o rechazo definitivo hasta obtener evidencia autoritativa. Las operaciones de compensación, cuando correspondan, serán operaciones separadas y auditables; no se simula que una reversa borra un movimiento ya confirmado.

### Dinero, fondos y datos sensibles

- Representar el importe con decimal exacto, no coma flotante; incluir moneda en cada operación.
- No redondear silenciosamente. La escala admitida se deriva de la moneda y de una política aprobada. Cálculos que requieran redondeo deben usar una regla explícita aprobada; la regla contable concreta queda pendiente.
- Aplicar límites de importe y disponibilidad en backend, una vez definidos por producto y riesgo. No aceptar una validación del cliente como autorización.
- Si se incorpora saldo: distinguir saldo contabilizado, reservas/retenciones y saldo disponible; el cálculo y la actualización deben ser atómicos para impedir gastar fondos reservados o insuficientes.
- Nunca guardar o exponer secretos, credenciales o números completos de tarjeta en solicitudes, respuestas, eventos o logs.

### Idempotencia, concurrencia y fallos

- Persistir en una transacción local la clave idempotente, la identidad y el alcance, una huella canónica de la solicitud, el ID de operación y su estado inicial. La composición exacta de la huella debe evitar almacenar datos sensibles.
- Una clave repetida con el mismo contenido devuelve la misma operación y su estado actual; no inicia una segunda ejecución.
- Una clave concurrente con el mismo contenido se resuelve mediante restricción de unicidad y transacción local: una creación gana y las demás recuperan la operación existente.
- Reutilizar una clave con contenido distinto devuelve conflicto y no ejecuta nada.
- No mantener una transacción de base de datos abierta durante una llamada remota.
- Ante timeout o resultado ambiguo, conservar la operación pendiente de conciliación y consultar por un mecanismo autorizado cuando se conozcan las capacidades del procesador. No reintentar un cargo a ciegas.
- Aplicar una confirmación y los movimientos locales correspondientes solo después de confirmación autoritativa, en una transacción local consistente.
- La conciliación y la compensación requieren contrato, permisos, evidencia y pruebas específicos. No se presupone un sistema externo de conciliación.

### Callbacks y estado regulatorio

Si el procesador elegido admite callbacks, el diseño futuro deberá autenticar el origen (por mecanismo confirmado con el proveedor), validar frescura, proteger contra replay, deduplicar eventos, persistir su ID y tolerar eventos fuera de orden. Los callbacks no podrán degradar un estado final confirmado; ante conflicto se consultará la fuente autorizada.

La forma de callback, autenticación, firma, campos y reintentos está **propuesta y pendiente** de las capacidades reales del procesador. No es un contrato implementable todavía.

Requieren evaluación jurídica y de Seguridad, según jurisdicción y alcance: privacidad y retención, KYC/AML, protección al consumidor, autenticación reforzada y alcance PCI DSS si se procesaran datos de tarjeta. No se afirma cumplimiento.

## 6. Diseño responsive y accesible

### Recorrido y presentación

1. **Celular de prueba y OTP:** instrucción clara de demo, fixture configurada y entrada OTP de seis dígitos. No insinuar envío de SMS.
2. **Datos KYC ficticios:** campo de documento de prueba, tipo `TEST` fijo o claramente limitado. Indicar el prefijo permitido y cómo corregir el error.
3. **Resultado:** mostrar estado y mensaje correspondiente. `ACTIVE`, pendiente, rechazo, indisponibilidad y resultado no confirmado deben ser visual y verbalmente distintos. Para revisión pendiente, ofrecer en la misma vista acciones de demo `ACTIVE` y `REJECTED` si el principal está autorizado.
4. Presentar la mediana observada solo con muestra disponible y la referencia de 3 minutos separada y rotulada. No mostrar MAU, CAC ni pagos.

El progreso muestra los tres pasos y el actual. En pantallas estrechas, usar indicador compacto “Paso N de 3” junto con nombres accesibles; en tablet y escritorio puede presentarse una lista horizontal o lateral sin depender del color.

### Layout y viewports de verificación

Diseño de una columna en móvil, formulario centrado y ancho limitado en escritorio. No exigir scroll horizontal para contenido, navegación, mensajes o formularios.

Viewports propuestos para verificación, no resultados de pruebas:

- Móvil estrecho: **320 px** de ancho.
- Móvil común: **360–390 px**.
- Tableta: **768 px**.
- Escritorio: **1024 px** y **1280 px**.

En móvil, botones y campos ocupan el ancho útil, mantienen separación y no quedan ocultos por teclado o elementos fijos. En tableta y escritorio, conservar lectura en una columna o distribuir progreso y contenido solo si el orden de lectura y el foco siguen siendo claros. No recortar mensajes ni identificadores necesarios.

### Accesibilidad: objetivo WCAG 2.2 AA verificable

- Etiquetas visibles asociadas a cada campo; no usar placeholder como etiqueta.
- Orden de lectura y navegación por teclado coherentes. Foco visible y no oculto por cabeceras o paneles.
- Contraste de texto y componentes conforme al objetivo AA; el color no es el único indicador de estado.
- Errores asociados al campo, escritos en lenguaje claro y con una acción correctiva.
- Resumen de errores enfocable o anunciado; cambios de estado y errores dinámicos comunicados con regiones accesibles sin anuncios excesivos.
- Título, instrucciones y progreso comprensibles por lector de pantalla.
- OTP con entrada de texto y teclado numérico apropiado; no tratarlo como número para evitar pérdida de ceros iniciales. Permitir pegar el código y navegación estándar.
- Al cambiar de paso, mover el foco de forma predecible al encabezado del paso o al resumen pertinente.
- Ampliación de texto y orientación móvil sin pérdida de contenido.

Las verificaciones de contraste, teclado, lector de pantalla y reflow quedan pendientes y no se consideran aprobadas por esta especificación.

### Estados e interacciones

- **Carga:** indicar que se está verificando/enviando; deshabilitar la acción que causaría duplicado, sin ocultar datos.
- **Vacío:** explicar qué dato de prueba se requiere.
- **Validación:** conservar datos válidos en memoria; señalar el campo inválido y cómo corregirlo.
- **OTP incorrecto:** indicar que el código no coincide y que se use el código de demo; el flujo no avanza.
- **Pendiente:** “La revisión sigue pendiente”; mostrar explícitamente wallet no activa. La acción de decisión solo se ofrece en demo y con autorización.
- **KYC no disponible (`503`):** informar que no pudo completarse la verificación y ofrecer reintentar. No describirlo como aprobación, rechazo ni resultado KYC.
- **Resultado incierto (`SUBMISSION_UNKNOWN`):** comunicar que no se pudo confirmar el envío, no mostrar wallet activa y no ofrecer un nuevo envío que pueda duplicar la creación. Permitir consultar el estado.
- **Doble envío:** prevenirlo en UI como ayuda y protegerlo en backend como garantía. La UI no es la barrera de idempotencia.
- **Pérdida de conectividad:** conservar el contexto no sensible en memoria cuando sea posible y ofrecer reintentar la consulta. No convertir un timeout en rechazo ni repetir automáticamente una operación ambigua.
- **Confirmación:** diferenciar aprobación/activación confirmada de una solicitud aceptada o pendiente. En HU-01 no hay pagos.

OTP y documento no se guardan en almacenamiento local persistente del navegador. Se eliminan del estado de formulario cuando ya no son necesarios.

## 7. Criterios verificables y matriz de trazabilidad

Todos los casos de abajo son **propuestos y NO EJECUTADOS**. Los escenarios futuros de pagos no forman parte de la aceptación de HU-01.

### Casos Dado/Cuando/Entonces

1. **Progreso y validación — actual**  
   **Dado** un flujo iniciado; **cuando** el usuario intenta avanzar con campos obligatorios vacíos o inválidos; **entonces** permanece en el paso actual, recibe indicaciones accionables y conserva los valores válidos ya ingresados.

2. **OTP correcto — actual**  
   **Dado** un flujo en `STARTED` y la fixture de demo habilitada; **cuando** se envía `123456`; **entonces** el backend pasa a `OTP_VERIFIED`, permite continuar y no llama a SMS ni al mock KYC.

3. **OTP incorrecto — actual**  
   **Dado** un flujo en `STARTED`; **cuando** se envía cualquier valor distinto de `123456`; **entonces** la API rechaza la validación, no avanza el flujo y no llama al mock.

4. **Documento/tipo inválido — actual**  
   **Dado** un flujo con OTP válido; **cuando** el documento no comienza con `TEST-` o el tipo no es `TEST`; **entonces** la API indica cómo corregirlo y el adaptador KYC no recibe ninguna llamada.

5. **Aprobación — actual**  
   **Dado** que el mock devuelve `APPROVED`/`ACTIVE`; **cuando** el backend consulta y persiste el resultado; **entonces** la interfaz muestra aprobación y `walletStatus=ACTIVE`.

6. **Revisión manual — actual**  
   **Dado** que el mock devuelve `MANUAL_REVIEW`/`PENDING`; **cuando** la interfaz presenta el estado; **entonces** informa que está pendiente y no presenta la wallet como activa.

7. **Resolver revisión — actual**  
   **Dado** un flujo pendiente y un principal autorizado para acciones de demo; **cuando** solicita `ACTIVE` o `REJECTED`; **entonces** el backend envía esa decisión al mock, consulta el estado final y solo comunica wallet activa si el resultado confirmado es `ACTIVE`.

8. **Rechazo — actual**  
   **Dado** que el mock devuelve `REJECTED`; **cuando** se muestra el resultado; **entonces** la interfaz informa rechazo y la wallet permanece no activa.

9. **Mock no disponible — actual**  
   **Dado** que el mock devuelve explícitamente `503 KYC_UNAVAILABLE`; **cuando** el backend procesa la respuesta; **entonces** no afirma un resultado KYC, no activa la wallet, devuelve un error recuperable y permite reintento manual.

10. **Resultado ambiguo — actual**  
    **Dado** que se pierde la respuesta del `POST` de creación KYC; **cuando** el backend no puede determinar si el mock creó una verificación; **entonces** registra `SUBMISSION_UNKNOWN`, no repite el `POST` automáticamente y la interfaz no comunica éxito ni wallet activa.

11. **Eventos y privacidad — actual**  
    **Dado** el inicio, los pasos y el cierre de un flujo; **cuando** se revisan eventos, persistencia y logs; **entonces** se encuentran ID y marcas de tiempo suficientes, pero no OTP, teléfono ni documento.

12. **Cierre incompleto — actual**  
    **Dado** un flujo sin `FLOW_SUBMITTED`; **cuando** el backend recibe el cierre; **entonces** registra `INCOMPLETE` y excluye el flujo de la duración y mediana. Si el navegador no logra enviar el cierre, no se presume que el evento exista.

13. **Medición — actual**  
    **Dado** un flujo con envío exitoso; **cuando** se calcula su duración y la mediana; **entonces** se mide desde inicio hasta envío de pasos de usuario, se excluyen esperas KYC/activación, se informan aparte cuando estén disponibles y los incompletos no integran la mediana. La referencia de 3 minutos se rotula como referencia.

14. **Doble envío concurrente — actual**  
    **Dado** un flujo en `OTP_VERIFIED`; **cuando** llegan dos envíos concurrentes; **entonces** solo una transición puede iniciar el `POST` KYC y la otra obtiene conflicto/estado consultable, sin crear una segunda verificación.

15. **Autorización — actual**  
    **Dado** un flujo asociado a un principal; **cuando** otro principal intenta leerlo, enviarlo o resolverlo; **entonces** no obtiene acceso ni datos del flujo.

16. **Responsive y accesibilidad — actual**  
    **Dado** los viewports definidos y navegación por teclado; **cuando** se recorre el flujo; **entonces** no hay desplazamiento horizontal en los escenarios objetivo y los campos, progreso, errores, foco y estados pueden comprenderse y operarse según el objetivo WCAG 2.2 AA.

17. **Pagos inciertos — futuro, fuera de HU-01**  
    **Dado** una futura operación de pago que queda incierta tras un timeout; **cuando** el adaptador no tiene confirmación autoritativa; **entonces** la operación queda pendiente de conciliación, no se informa como confirmada y no se repite el cargo a ciegas.

18. **Idempotencia de pagos — futuro, fuera de HU-01**  
    **Dado** una clave de idempotencia persistida; **cuando** se reenvía con igual contenido o con contenido distinto; **entonces** se recupera la operación original en el primer caso y se devuelve conflicto en el segundo, sin duplicar ejecución.

### Matriz de criterios originales

| Criterio original | Componente principal | Caso de prueba propuesto | Resultado esperado / alcance |
|---|---|---|---|
| Secuencia visible, validación y conservación de datos | Angular y API de onboarding | Componente: pasos vacío/inválido/correcto; REST: estado no avanza con entrada inválida | Bloquea avance, explica corrección y conserva datos válidos. **Actual; NO EJECUTADO.** |
| OTP fijo `123456`, sin SMS | Servicio de aplicación OTP y API | Unitario/REST: código correcto e incorrecto; verificar ausencia de llamada SMS/mock | Solo correcto avanza; ningún código causa SMS. **Actual; NO EJECUTADO.** |
| KYC con `TEST`, documento ficticio y estado reflejado fielmente | Servicio y adaptador KYC; Angular | Prueba HTTP con payload y estados del mock; componente para reflejar respuesta | Solo se envían datos válidos; UI no infiere requisitos KYC. **Actual; confirmar esquema externo; NO EJECUTADO.** |
| `APPROVED/ACTIVE`, `MANUAL_REVIEW/PENDING`, `REJECTED` | Servicio de aplicación y UI | Pruebas de contrato para cada mapeo y estado de wallet | Solo `ACTIVE` confirmado activa; pendiente/rechazado no activan. **Actual; NO EJECUTADO.** |
| Resolver revisión desde resultado con `ACTIVE` o `REJECTED` | API, adaptador KYC y Angular | REST/HTTP de prueba: decisión y consulta posterior | Decisión se envía al mock; UI refleja el estado final confirmado; sin consola separada. **Actual; NO EJECUTADO.** |
| `503 KYC_UNAVAILABLE`, sin activar y con reintento | Servicio, adaptador y UI | HTTP de prueba para `503`; verificar nuevo intento solo tras fallo explícito | No afirma resultado KYC, permite reintento y no activa. **Actual; NO EJECUTADO.** |
| Eventos de ciclo sin valores sensibles y cierre incompleto | Aplicación, persistencia y logging | Pruebas de eventos/logs con captura; cierre antes/después del envío | ID y timestamps presentes; no hay OTP/teléfono/documento; cierre temprano es `INCOMPLETE`. **Actual; NO EJECUTADO.** |
| Duración, mediana y referencia 3 minutos, excluyendo revisión y activación | Servicio de métricas | Reloj controlado con KYC lento, activación lenta y flujo incompleto | Duración termina en `FLOW_SUBMITTED`; mediana solo incluye enviados; tiempos posteriores separados. **Actual; NO EJECUTADO.** |
| Documento que no cumple `TEST-` o tipo distinto no se envía | Validación backend y adaptador KYC | REST con tipo inválido y prefijo inválido; aserción de cero llamadas salientes | Error accionable y cero solicitudes al mock. **Actual; NO EJECUTADO.** |
| No pagos ni MAU/CAC | API, dominio, persistencia y reporte | Revisión de rutas, dependencias, respuestas y datos persistidos | Sin endpoint, operación o resultado de pago; sin métricas MAU/CAC. **Actual; NO EJECUTADO.** |
| Prevención de solicitudes duplicadas/concurrentes | Aplicación y persistencia | Prueba concurrente con dos envíos del mismo flujo | Un solo `POST` KYC; otras solicitudes reciben conflicto/estado. **Actual; NO EJECUTADO.** |
| Pago incierto, idempotencia y conciliación | Puerto futuro, aplicación y adaptador futuro | Pruebas contractuales futuras, al seleccionar procesador | Pendiente sin éxito falso ni reintento a ciegas; no bloquea ni pertenece a HU-01. **Futuro; NO EJECUTADO.** |

## 8. Decisiones y tareas, riesgos, preguntas abiertas y evidencia pendiente

### Backend

- Definir los puertos de entrada/salida y transiciones del dominio respetando la arquitectura hexagonal.
- Implementar API propia solo tras cotejar rutas, autenticación y convenciones actuales.
- Validar OTP localmente y activarlo exclusivamente en perfil de demo.
- Implementar validación del tipo y prefijo antes de cualquier llamada KYC.
- Implementar cliente HTTP Java 17 según el esquema confirmado del mock; mantener `MOCK_BASE_URL` configurable y escenario `APPROVED` por defecto.
- Persistir `SUBMITTING` antes del `POST`; resolver concurrencia y no repetir una creación ambigua.
- Traducir errores externos a errores estables y no exponer cuerpos del mock.
- Implementar propiedad del flujo por principal, cierre, eventos mínimos y cálculo de duración.
- Documentar configuración, estados, límites del mock, manejo de timeout y comandos de prueba. El directorio indicado por el proyecto debe confirmarse antes de dar instrucciones de ejecución.

### Frontend

- Implementar los tres pasos, progreso accesible y formularios con validación en cliente como ayuda, manteniendo validación autoritativa en backend.
- Integrar únicamente la API propia; no llamar al mock.
- Mostrar fielmente aprobación, pendiente, rechazo, no disponibilidad y resultado incierto.
- Conservar datos válidos en memoria ante errores; no persistir OTP ni documento en almacenamiento local.
- Prevenir doble envío en interfaz, mantener consulta de estado y distinguir resultado pendiente de fallo confirmado.
- Implementar resolución de demo en la misma vista, condicionada a permisos.
- Documentar cómo usar las fixtures ficticias, una vez definida la fixture.

### Datos, si el rol está activo

- Acordar si Backend define el esquema efímero o consume un contrato de esquema definido por Datos.
- Confirmar campos mínimos de flujo y eventos, control de concurrencia, timestamps UTC e índices.
- Revisar que no se guarden OTP, teléfono ni documento. Confirmar manejo del identificador del mock.
- Definir alcance y límites del reporte efímero en H2.

### Testing

- Definir runner compatible con Angular 17 y pruebas unitarias, REST, adaptador HTTP y componentes.
- Probar mapeos KYC, llamadas salientes exactas, errores, concurrencia, reloj controlado, privacidad y ausencia de rutas de pago.
- Probar los viewports definidos y navegación por teclado/lector de pantalla.
- Ejecutar, cuando el código esté disponible y desde los directorios confirmados, las pruebas y builds requeridos. Registrar resultados reales; no se atribuye aquí ningún resultado.

### Seguridad y cumplimiento

- Confirmar autenticación, autorización por principal, rol de resolución de demo y política de acceso al reporte.
- Revisar redacción y enmascaramiento de logs, trazas, cuerpos HTTP, excepciones y telemetría.
- Restringir la activación del OTP fijo y escenarios mock al perfil de demo.
- Revisar transporte seguro al mock y gestión de configuración/secrets sin incluirlos en contratos ni logs.
- Determinar jurisdicción, retención, privacidad, auditoría y requisitos regulatorios aplicables antes de cualquier uso real.
- Evaluar por separado requisitos futuros de pagos, incluidos datos de tarjeta, alcance PCI DSS si corresponde, controles de fraude, límites, titularidad de cuentas y conciliación. No se declara cumplimiento.

### Riesgos y mitigaciones

| Riesgo | Mitigación propuesta |
|---|---|
| OTP fijo confundido con autenticación real | Rotularlo como código de demo, validarlo solo en perfil de demo y no registrar el valor. |
| Duplicados en el mock | Transición atómica por flujo, sin reintento automático ambiguo y consulta de estado. |
| Documento real ingresado por error | Aviso visible de datos ficticios, validación `TEST-` antes del mock y no persistencia del documento. |
| Timeout de creación con resultado desconocido | `SUBMISSION_UNKNOWN`, consulta/revisión antes de cualquier acción; nunca repetir a ciegas. |
| Mock caído o con límites | URL configurable, traducción segura del error y reintento solo cuando el contrato indique que no hubo creación. |
| Evento de abandono perdido | Tratar cierre de navegador como señal de mejor esfuerzo; excluirlo de la definición de finalización y no fabricar eventos. |
| Reinicio de H2 | Declarar métricas efímeras de demo; no presentarlas como analítica productiva. |
| Acceso a flujos o decisiones por usuario no autorizado | Asociar flujo al principal en servidor y verificar titularidad en cada petición. |
| Solicitud de pagos sin requisitos aprobados | Mantener puerto inactivo y sin API pública; abrir diseño separado con Seguridad, Riesgo, Datos y negocio. |

### Preguntas abiertas

1. ¿Qué proveedor o mecanismo de identidad existe y cómo obtiene Quarkus el principal?
2. ¿Cuál es el identificador y el texto exacto de la fixture del celular de demo? ¿La API debe recibir ese alias o la fixture se determina solo en backend?
3. ¿Cuál es el esquema completo y la semántica de estados del mock, incluidos timeout, `429`, `404`, `409` y decisión?
4. ¿Qué formato de sufijo acepta el mock para documentos `TEST-`?
5. ¿Qué rol puede resolver revisiones y quién puede consultar la mediana de la sesión?
6. ¿Cómo se recuperará operativamente un flujo `SUBMISSION_UNKNOWN` si no se recibió el ID KYC?
7. ¿El equipo Datos está activo y define el esquema o Backend lo propone?
8. ¿Qué alcance tiene la muestra de mediana (usuario, grupo o sesión de demo) y cómo se evita mezclar sesiones no relacionadas?
9. ¿Qué requisitos de retención, privacidad y auditoría corresponden a la jurisdicción y al entorno de demo?

### Evidencia pendiente

No se ha inspeccionado el código ni se han validado esquemas, rutas, perfiles, dependencias o convenciones del repositorio. No se han ejecutado pruebas, builds, pruebas de accesibilidad o revisiones responsive. Todas estas comprobaciones están **NO EJECUTADO** y deben aportar evidencia antes de considerar lista la implementación. Esta especificación no sustituye la aprobación humana ni la confirmación de contratos externos.