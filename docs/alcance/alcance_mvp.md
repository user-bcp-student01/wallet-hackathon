# Alcance del MVP de Wallet en Perú

## Propósito

Construir una demo funcional con el mock de Wallet para validar un recorrido de onboarding y pagos de prueba. El MVP prioriza medir el tiempo de onboarding y demostrar que se puede completar un pago sin duplicarlo.

La demo utiliza únicamente datos `TEST`; no procesa dinero real ni valida los objetivos comerciales de un lanzamiento productivo.

## Usuarios y canales

- **Pagador:** interfaz para smartphone y API.
- **Comercio:** interfaz web para consultar el historial de pagos directos recibidos.
- **Operaciones y soporte:** interfaz web para consultar pagos, revisar conciliaciones y registrar resoluciones.

## Alcance incluido

### Onboarding

- Flujo guiado con validaciones y señalización del paso actual.
- KYC simulado.
- Estados de wallet contemplados por el flujo: activa, pendiente y rechazada.
- Registro de eventos para medir el tiempo desde el inicio del onboarding hasta el envío correcto de los datos.
- Revisión KYC y activación medidas por separado; no forman parte de la duración objetivo del flujo del usuario.

### Pagos de prueba

- Pago de bajo monto a un contacto.
- Pago directo a un comercio, sin QR.
- Interfaz y API para los pagos.
- Mostrar identidad del destinatario y monto antes de confirmar.
- Límite de producto de PEN 200 por operación, o un límite menor si lo exige el proveedor o canal.
- Mostrar el resultado del pago y conservar referencia, comprobante e historial cuando corresponda.
- Probar resultados aprobados y rechazados.
- Idempotencia real: los reintentos con la misma clave y contenido deben devolver el resultado existente sin crear una operación duplicada. La retención objetivo de la clave es de 7 días.
- Los callbacks duplicados no deben duplicar el efecto financiero.

El mock puede dejar inicialmente un pago en `PENDING`; la entrega del evento de prueba permite llegar al resultado aprobado o rechazado. Esta transición es parte del mecanismo de prueba, no un flujo de investigación de pagos pendientes.

### Web del comercio

- Consultar el historial de pagos directos recibidos, sin QR.
- Consultar el estado y la referencia de cada operación.
- Filtrar el historial por fecha y referencia.

El contrato del mock no proporciona filtros por fecha ni referencia. Esta capacidad debe estar disponible en la solución del MVP.

### Soporte

- Vista web para consultar el estado y los datos de una operación.
- Registrar la resolución de un caso con su referencia de transacción.

El MVP no incluye gestión de disputas desde la app ni un flujo avanzado de investigación de timeouts o resultados inciertos.

### Conciliación

- Un operador inicia la conciliación usando datos de wallet, proveedor mock y ledger.
- Mostrar todas las diferencias detectadas con referencia, motivo y estado de investigación.
- Registrar la resolución de cada diferencia y mostrar un resumen de conciliadas, no conciliadas y resueltas.

La demo no establece una tasa tolerable de diferencias ni define cuáles son “críticas”. No mueve dinero ni corrige automáticamente saldos o asientos.

## Métrica de la demo

La única métrica de negocio que se medirá en esta demo será el tiempo de onboarding, desde el inicio del flujo hasta el envío correcto de los datos.

Los objetivos de caída en checkout, MAU y CAC quedan fuera de la medición de esta demo. Podrán evaluarse en un piloto o lanzamiento posterior.

## Fuera de alcance

- Pagos por QR, generación o lectura de QR y validación EMVCo.
- Operaciones con dinero real.
- KYC con documentos reales o proveedor productivo.
- Integraciones productivas con proveedores, bancos o adquirentes.
- Flujos de timeout, indisponibilidad de proveedor e investigación de resultados inciertos.
- Reversos y disputas.
- Automatización de conciliación diaria y corrección de diferencias.
- Medición de checkout, MAU o CAC en la demo.
- Despliegue multipaís, lealtad y APIs abiertas para terceros.

## Restricciones del mock

- El contrato OpenAPI corresponde a un mock de pruebas; usar el grupo asignado al equipo.
- Enviar únicamente datos `TEST`; no incluir documentos reales.
- Los importes se expresan en céntimos de PEN; por ejemplo, `1500` equivale a S/ 15.00.
- Los eventos del proveedor se entregan manualmente durante las pruebas.
- El mock no envía webhooks automáticamente ni verifica firmas externas.
- `POST /control/reset` borra todos los datos del grupo y restaura los datos semilla; afecta a todos sus integrantes.

## Criterios de aceptación del MVP

- Un usuario puede completar el onboarding de prueba y queda registrado el tiempo hasta el envío correcto de sus datos.
- El pagador puede realizar un pago de prueba a un contacto y un pago directo a un comercio, sin QR.
- Se muestran destinatario, monto y resultado del pago.
- Repetir un pago con la misma clave no crea una operación duplicada.
- El comercio puede consultar y filtrar por fecha y referencia su historial de pagos directos.
- Soporte puede consultar una operación y registrar la resolución de su caso.
- Operaciones puede iniciar la conciliación, consultar todas las diferencias y registrar su resolución.
- Ningún flujo de la demo utiliza dinero o documentos reales.

## Documentación fuente

- [README del proyecto](../../README.md)
- [Objetivos y componentes](../objetivos.md)
- [Épica: MVP de wallet en Perú](../epic/peru-wallet-mvp.sp.md)
- [Onboarding y activación](../user-stories/user-onboarding-mvp-completion.sp.md)
- [Confirmación de pagos de bajo monto](../user-stories/payer-low-value-payment-confirmation.sp.md)
- [Visibilidad de pagos QR para comercios](../user-stories/merchant-qr-payment-status-visibility.sp.md)
- [Idempotencia en pagos](../user-stories/payment-idempotency-protection.sp.md)
- [Fallas y reversos](../user-stories/payment-failure-reversal-handling.sp.md)
- [Conciliación operativa](../user-stories/operations-transaction-reconciliation.sp.md)
- [Contrato OpenAPI del mock](../openapi.json)