# Alcance del MVP: Onboarding de Wallet

## Objetivo

Validar un flujo de onboarding guiado que permita a una persona completar el registro y conocer claramente el estado de su wallet.

La referencia de producto es reducir el tiempo mediano de onboarding de 8 a 3 minutos. En esta demo se medirá únicamente el tiempo del onboarding; no se validará el impacto en métricas de un lanzamiento productivo.

## Usuarios y canales

- **Usuario objetivo:** personas en Perú de 18 a 21 años que aún no han sido bancarizadas.
- **Canales:** interfaz de usuario para smartphone usando web responsive para el flujo de onboarding.

## Alcance incluido

- Mostrar la secuencia de pasos requeridos y el paso actual.
- Validar la información ingresada y bloquear el avance si faltan datos obligatorios o hay valores inválidos.
- Mostrar mensajes accionables cuando el usuario deba corregir información.
- Integrar KYC simulado, utilizando exclusivamente datos de prueba.
- Mostrar el resultado del onboarding:
  - `APPROVED`: registro aprobado y wallet activa.
  - `MANUAL_REVIEW`: requiere revisión manual.
  - `REJECTED`: registro rechazado.
- Registrar eventos de inicio, finalización de pasos y cierre del flujo.
- Medir el tiempo desde el inicio del onboarding hasta el envío correcto de los datos de todos los pasos.
- Reportar por separado el tiempo de revisión KYC y el tiempo hasta la activación; estos tiempos no forman parte de la métrica de duración del flujo del usuario.
- Para pruebas de revisión manual, utilizar la capacidad del mock para resolver una verificación pendiente. No se incluye una consola independiente de soporte.
- Registrar un número de celular de prueba y verificar su titularidad mediante un OTP simulado; no enviar SMS reales ni utilizar números personales reales.


## Métrica

- **Métrica de la demo:** tiempo mediano desde el inicio del flujo hasta el envío correcto de los datos.
- **Referencia de producto:** reducir la línea base de 8 minutos a 3 minutos.
- La demo no medirá checkout, Usuarios Activos Mensuales (MAU) ni Costo de Adquisicion de Clientes (CAC) .

## Fuera de alcance

- Pagos a contactos o comercios.
- Pagos QR, generación o lectura de códigos QR.
- Historial de transacciones, comprobantes y web de comercios.
- Idempotencia de pagos y callbacks de pago.
- Gestión de fallas, reversos o disputas de pago.
- Herramientas de soporte para pagos.
- Conciliación y operaciones de ledger.
- KYC real, documentos reales e integraciones productivas con proveedores.
- Medición de MAU, CAC o caída en checkout.

## Restricciones de la demo

- El onboarding y KYC se ejecutan contra el mock de pruebas.
- Enviar únicamente datos `TEST`; no incluir documentos reales.
- La demo no activa operaciones financieras reales.

## Criterios de aceptación

- El usuario puede identificar los pasos requeridos y su avance.
- El flujo impide avanzar cuando faltan datos obligatorios o hay información inválida, e indica cómo corregirla.
- Una verificación aprobada deja la wallet activa; una revisión manual queda pendiente; una rechazada muestra el estado correspondiente.
- Se registran los eventos necesarios para calcular la duración definida del onboarding.
- La salida permite distinguir la duración del flujo del usuario del tiempo de revisión KYC y activación.

## Documentación fuente

- [README del proyecto](../../README.md)
- [Objetivos y componentes](../objetivos.md)
- [Épica: MVP de wallet en Perú](../epic/peru-wallet-mvp.sp.md)
- [Historia: onboarding y activación](../user-stories/user-onboarding-mvp-completion.sp.md)
- [Contrato OpenAPI del mock](../openapi.json)