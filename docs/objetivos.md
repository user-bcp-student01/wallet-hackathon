 Onboarding Wallet
 Alta, validaciones y estados de cuenta de prueba.

- Registro de usuario (UI o API)
- Validaciones básicas y KYC mock
- Estado: activa, pendiente, rechazada

COMPONENTES  UI · API · KYC mock · HITL
---
Pago a contacto
Crear intención, confirmar resultado e historial con proveedor 
simulado.
- Pago a persona o comercio (mock)
- Confirmación y comprobante
- Historial de transacciones
COMPONENTES  API · Estados · Payment mock
---
Pago QR comercio
Generar o leer QR de prueba, iniciar el pago y reflejar su 
resultado.
- Generación de QR (mock)
- Lectura de QR (cámarao archivo)
- Procesode pagoy comprobante
COMPONENTES  QR local · Acquiring mock
---
Idempotencia
Repetir requests y callbacks sin duplicar operaciones. Esta lógica 
sí es real.
- Reintentos con idempotency key
- Callbacks duplicados
- Validación en base de datos o store
COMPONENTES  Clave idempotente· Test
---
Fallas y reversos
Timeout, rechazo, pending y duplicados; reversos simulados y 
escalamiento.
- Casos de error: timeout, rechazo, pending
- Simulación de reversos
- Escalamiento a soporte humano (HITL)
COMPONENTES  Fault injection · HITL
---
 Conciliación
Comparar Wallet, proveedor mock y ledger local; detectar 
diferencias.
- Conciliación entre fuentes (mock)
- Detección de diferencias
- Estado final de las operaciones
COMPONENTES  Reconciliador real · Datos mock

