# Design

## Context

Ver `proposal.md` para motivación y `specs/wallet-onboarding/spec.md` para el contrato observable. Este repositorio genera una solución Angular 17 y Quarkus 3 con Java 17; no contiene la aplicación de wallet generada. El andamiaje Quarkus ya incluye H2 en memoria.

El contrato `docs/openapi.json` define `POST /kyc/verifications`, `GET /kyc/verifications/{id}` y `POST /kyc/verifications/{id}/decision`. Crear una verificación acepta únicamente `documentType: TEST` y documentos `TEST-...`; `scenario` admite `APPROVED`, `REJECTED`, `MANUAL_REVIEW` y `UNAVAILABLE`. OTP no forma parte de ese contrato.

## Goals / Non-Goals

**Goals:**
- Separar la captura guiada, la validación local de OTP, la integración KYC y la presentación de estados.
- Medir la duración del flujo con marcas de tiempo independientes de la espera de KYC y de la activación.
- Mantener la integración configurable por grupo y segura para datos ficticios.

**Non-Goals:**
- Añadir OTP real, SMS, KYC productivo, pagos, soporte productivo, MAU o CAC.
- Crear una consola independiente para soporte o revisión manual.
- Garantizar persistencia de largo plazo o mediciones de cohortes productivas.

## Decisions

### Flujo y propiedad de responsabilidades

La interfaz Angular presenta tres etapas: celular de prueba y OTP; datos KYC ficticios (`documentType=TEST`, `document=TEST-...`); y resultado KYC. El backend Quarkus expone los endpoints propios que necesite la interfaz, mantiene el estado del flujo y es el único componente que llama al mock. La revisión `MANUAL_REVIEW` se resuelve desde la misma vista de resultado de demo, no mediante una consola separada.

La secuencia mínima se limita a los datos definidos por HU-01 y el contrato. No se solicitan edad, documentos reales ni otros campos KYC no especificados.

### OTP fijo de demo

El backend compara localmente el código recibido con `123456`, definido como valor fijo de demo. El frontend lo identifica como dato de prueba para que la verificación pueda completarse sin SMS. El código y el teléfono no se guardan como eventos ni se escriben en logs. Esta verificación no constituye prueba de titularidad real y no se habilita en un perfil productivo.

### Adaptador KYC

El backend usa un cliente HTTP Java 17 para consumir el mock sin añadir una dependencia al POM generado. `MOCK_BASE_URL` identifica la URL del grupo; no se codifica el grupo 5 en el cliente. El adaptador crea la verificación con los datos `TEST`, consulta por el ID KYC (no por el ID de wallet) y, ante revisión pendiente, envía `ACTIVE` o `REJECTED` al endpoint de decisión y vuelve a consultar el estado.

El escenario se controla en configuración de demo/pruebas y por defecto usa `APPROVED`; no se permite que un usuario elija escenarios productivos. `503 KYC_UNAVAILABLE` se muestra como fallo recuperable, sin activar la wallet. Los errores 400/404/409 del mock se traducen a estados de aplicación sin exponer cuerpos internos.

### Estado y prevención de altas repetidas

El backend conserva una máquina de estados por flujo: `STARTED`, `OTP_VERIFIED`, `SUBMITTING`, `PENDING`, `ACTIVE`, `REJECTED` o `SUBMISSION_UNKNOWN`. Antes de llamar a `POST /kyc/verifications`, persiste la transición a `SUBMITTING`; una repetición del mismo envío para ese flujo no vuelve a crear una wallet.

El mock no deduplica altas. Por ello, no se reintenta automáticamente un `POST` con resultado de red ambiguo: se marca `SUBMISSION_UNKNOWN` y se informa que el resultado no pudo confirmarse. Un `503 KYC_UNAVAILABLE` explícito sí permite reintentar porque el contrato indica que no se creó una wallet.

### Eventos y duración

El backend genera marcas de tiempo UTC y correlaciona eventos con un ID aleatorio de flujo. Registra inicio, pasos completados y cierre; el cierre incluye resultado `SUBMITTED` o `INCOMPLETE`. El evento de envío exitoso se registra después de validar todos los pasos y antes de iniciar KYC. Ese timestamp define el fin de la métrica del onboarding.

El tiempo de KYC se mide por separado desde la solicitud al mock hasta recibir un estado final; el tiempo de activación se mide desde el envío hasta que el estado es `ACTIVE`. Ningún evento contiene OTP, teléfono ni documento. En H2 de demo se guardan únicamente estado, tipo de evento, paso, resultado y timestamps. La mediana se calcula sobre flujos con envío exitoso; un cierre incompleto no se cuenta como finalización.

### Persistencia y configuración

La demo usa H2 en memoria ya incluido en el andamiaje. En equipos de seis, Backend define las tablas y el acceso a datos; en equipos con rol Datos, ese rol define el esquema y Backend consume su contrato. `MOCK_BASE_URL` y el escenario KYC son configuración de demo, no valores repartidos entre componentes.

## Risks / Trade-offs

- [El OTP fijo permite completar la pantalla, pero no prueba titularidad] → Mostrarlo como mecanismo de demo, no registrar el código y no reutilizarlo en perfiles productivos.
- [El mock conserva estado y no evita altas repetidas] → Mantener estado por flujo, evitar reintentos automáticos ambiguos y usar solo documentos ficticios.
- [Un cierre de pestaña puede impedir enviar el evento de abandono] → Medir la duración únicamente con eventos de inicio y envío confirmados; tratar el evento de abandono como informativo, no como requisito para el cálculo.
- [H2 en memoria se pierde al reiniciar] → Limitar los reportes a la sesión/duración de la demo; no presentar los datos como analítica productiva.
- [El mock puede no estar disponible o alcanzar límites del grupo] → Configurar la URL, tratar `503`/`429` sin activar la wallet y documentar el reinicio del grupo como recuperación operativa.

## Migration Plan

No hay migración productiva. Crear las tablas de sesión y eventos en el esquema efímero de H2 para la demo y agregar pruebas con base de datos aislada. El despliegue se revierte descartando la aplicación generada y sus datos temporales; no se envía ni modifica información financiera real.