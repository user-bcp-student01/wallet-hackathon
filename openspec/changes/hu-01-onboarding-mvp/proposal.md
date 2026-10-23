# Proposal

## Why

El MVP necesita validar un onboarding guiado para smartphone que explique el avance, bloquee datos incompletos o inválidos y presente con claridad el resultado del registro. La demo debe medir únicamente la duración del flujo del usuario, separándola de la espera de KYC y de la activación.

## What Changes

- Introducir el flujo responsive de onboarding con pasos visibles, validaciones y mensajes accionables.
- Verificar el celular de prueba con un OTP local fijo de seis dígitos; no enviar SMS ni usar datos personales reales.
- Consumir el mock existente para crear y consultar verificaciones KYC y resolver revisiones manuales, usando solo datos de prueba.
- Reflejar los resultados `APPROVED`, `MANUAL_REVIEW` y `REJECTED`; solo `APPROVED` activa la wallet.
- Registrar inicio, finalización de cada paso y cierre del flujo, y medir desde el inicio hasta el envío correcto de todos los pasos. Reportar aparte la revisión KYC y el tiempo hasta la activación.
- Mantener fuera de alcance los pagos, MAU, CAC, KYC productivo, SMS reales y operaciones financieras.

## Capabilities

### New Capabilities
- `wallet-onboarding`: Flujo de registro guiado, validación local de OTP de demo, integración con KYC simulado, estados de activación e instrumentación de duración.

### Modified Capabilities
None.

## Impact

- Solución de demo generada para Angular 17 y Quarkus 3; este repositorio aporta historias, alcance, contratos y agentes CrewAI, no la aplicación generada.
- El backend implementa su lógica y consume `POST /kyc/verifications`, `GET /kyc/verifications/{id}` y `POST /kyc/verifications/{id}/decision` según `docs/openapi.json`. El mock no define endpoints OTP; el código fijo se valida localmente y solo para la demo.
- Se requiere persistir o correlacionar el estado del onboarding y sus eventos durante la demo, sin almacenar documentos reales ni códigos OTP.
- La métrica de 3 minutos es referencia de producto, no una garantía de resultado de esta demo. No se implementan reportes de MAU ni CAC.
- Fuente de alcance: `docs/alcance/HU-01.md`; la capacidad excluye el acceso y procesamiento de pagos aunque aparezcan en la historia de negocio más amplia.