# Spec Delta

## Purpose

Permite a una persona completar un onboarding guiado de wallet en la demo, verificar el teléfono con un OTP de prueba y conocer el resultado KYC sin confundir el envío de datos con la activación.

## ADDED Requirements

### Requirement: Onboarding guiado y validación de pasos
El sistema SHALL mostrar la secuencia requerida y el paso actual, bloquear el avance si faltan datos obligatorios o son inválidos y explicar cómo corregirlos.

#### Scenario: Usuario recorre los pasos
- **WHEN** el usuario inicia el onboarding
- **THEN** la interfaz muestra todos los pasos requeridos y señala el paso actual durante el recorrido

#### Scenario: Datos incompletos o inválidos
- **WHEN** el usuario intenta avanzar con datos obligatorios ausentes o inválidos
- **THEN** el sistema bloquea el avance y presenta un mensaje accionable sin perder los datos válidos ya ingresados

### Requirement: Verificación telefónica mediante OTP de demo
El backend SHALL validar localmente el mismo OTP fijo de seis dígitos `123456` para la demo, sin enviar SMS ni tratarlo como verificación de identidad productiva.

#### Scenario: Código fijo correcto
- **WHEN** el usuario envía el código de prueba `123456` para un celular de prueba
- **THEN** el backend acepta la verificación telefónica y permite continuar el onboarding

#### Scenario: Código incorrecto
- **WHEN** el usuario envía un código distinto de `123456`
- **THEN** el backend rechaza la verificación y el onboarding no avanza al siguiente paso

#### Scenario: No se envía SMS
- **WHEN** se inicia o valida una verificación telefónica en la demo
- **THEN** el sistema no solicita ni envía un SMS y solo utiliza un número de prueba

### Requirement: Integración con KYC simulado
El backend SHALL consumir el contrato del mock KYC con `documentType` igual a `TEST` y un documento ficticio con prefijo `TEST-`; la interfaz SHALL reflejar el estado devuelto sin inferir requisitos KYC reales.

#### Scenario: KYC aprobado
- **WHEN** el mock devuelve el escenario `APPROVED` y estado `ACTIVE`
- **THEN** el onboarding informa la aprobación y la wallet queda activa

#### Scenario: KYC requiere revisión manual
- **WHEN** el mock devuelve el escenario `MANUAL_REVIEW` y estado `PENDING`
- **THEN** el onboarding informa que la revisión sigue pendiente y la wallet no se presenta como activa

#### Scenario: Resolver revisión manual desde el resultado
- **WHEN** desde la vista de resultado pendiente se solicita la decisión de demo `ACTIVE` o `REJECTED`
- **THEN** el backend envía la decisión al mock, consulta el estado final y la interfaz activa la wallet solo para `ACTIVE`

#### Scenario: KYC rechazado
- **WHEN** el mock devuelve el escenario `REJECTED` y estado `REJECTED`
- **THEN** el onboarding informa el rechazo y la wallet no queda activa

#### Scenario: Proveedor KYC no disponible
- **WHEN** el mock responde `503 KYC_UNAVAILABLE`
- **THEN** el sistema informa que no pudo completar la verificación, no presenta la wallet como activa y permite reintentar sin afirmar un resultado KYC

### Requirement: Eventos del ciclo de onboarding
El sistema SHALL registrar el inicio, la finalización de cada paso y el cierre del flujo con marcas de tiempo, sin incluir documentos, OTP ni otros valores sensibles.

#### Scenario: Registro de eventos del flujo
- **WHEN** el usuario inicia, completa pasos y cierra el onboarding
- **THEN** quedan registrados los eventos correspondientes con un identificador de flujo y marcas de tiempo suficientes para reconstruir la duración

#### Scenario: Flujo abandonado
- **WHEN** el usuario cierra el flujo antes del envío exitoso de todos sus pasos
- **THEN** se registra el cierre como incompleto y no se contabiliza como una finalización exitosa

### Requirement: Medición de duración de la demo
La duración del onboarding SHALL medirse desde el inicio del flujo hasta el envío correcto de los datos de todos los pasos; la revisión KYC y el tiempo hasta la activación SHALL reportarse por separado.

#### Scenario: Envío exitoso de todos los pasos
- **WHEN** se envían correctamente los datos de todos los pasos del usuario
- **THEN** el reporte calcula la duración del flujo desde su evento de inicio hasta ese envío, excluyendo los tiempos posteriores de revisión KYC y activación

#### Scenario: Referencia de producto
- **WHEN** se presenta el resultado de duración de la demo
- **THEN** se informa la mediana observada y se muestra 3 minutos como referencia de producto, sin afirmar que la demo valida el impacto de un lanzamiento

### Requirement: Límites de la demo de onboarding
El onboarding SHALL usar únicamente datos de prueba y no SHALL procesar pagos ni calcular MAU o CAC como parte de esta demo.

#### Scenario: Se intenta ingresar información no permitida
- **WHEN** el flujo recibe un documento que no cumple el formato de prueba `TEST-` o un tipo distinto de `TEST`
- **THEN** el sistema no lo envía al mock y solicita datos de prueba válidos

#### Scenario: Funcionalidad fuera del alcance
- **WHEN** se completa el onboarding de la demo
- **THEN** no se crea ni procesa un pago y el resultado no incluye métricas de MAU o CAC