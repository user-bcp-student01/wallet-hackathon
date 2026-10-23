# testing_report.md — HU-01 Onboarding guiado de wallet para el MVP

**Fecha del informe:** 2026-10-23  
**Estado:** diseño de pruebas propuesto; **no se ejecutaron pruebas**. No se proporcionó acceso al repositorio ni evidencia de ejecuciones.

## Resumen

Se propone cobertura manual y automatizada para el flujo de tres etapas, el OTP local, la integración con el mock KYC, los estados de la wallet, los eventos y la medición de duración. La prioridad es evitar avances o activaciones incorrectos, envíos KYC duplicados y exposición de datos sensibles.

Los endpoints y algunos campos mencionados aquí proceden de las especificaciones entregadas y deben confirmarse contra la implementación antes de integrar las pruebas. Se incluye un smoke test de API en Bash para el contrato propuesto; no sustituye las pruebas de integración con el mock ni las pruebas de interfaz.

## Alcance y supuestos

- Datos exclusivamente sintéticos: OTP `123456` y documento de ejemplo `TEST-DEMO-001`. No se usa ni se solicita un teléfono real.
- Se asumen los endpoints propios descritos en `backend_spec.md`, incluida la respuesta de inicio con `flowId` y la consulta con `state`.
- Se asumen los estados descritos: `STARTED`, `OTP_VERIFIED`, `PENDING`, `ACTIVE`, `REJECTED` y `SUBMISSION_UNKNOWN`.
- La validación del documento se prueba según el contrato descrito: tipo exacto `TEST` y prefijo `TEST-` con un sufijo no vacío. Los límites adicionales del sufijo no están especificados.
- Para pruebas de integración KYC se requiere un mock aislado que registre llamadas y permita controlar respuestas. No se proporcionó el esquema completo de respuesta del mock.
- La respuesta de `/report` y algunos DTO de error no están definidos completamente. Se debe confirmar su contrato antes de automatizar aserciones sobre esos campos.
- No se asume autenticación, rol ni mecanismo de autorización. Su definición y pruebas son pendientes.
- El smoke test propuesto crea un flujo en el entorno donde se ejecute. Debe usarse únicamente con una instancia de pruebas, nunca con producción.
- No se verifican requisitos KYC reales: la interfaz debe limitarse a presentar el estado devuelto por el mock.

## Matriz de criterios de aceptación a casos

Todos los resultados de esta matriz son **esperados**, no observados. Los casos identificados como manuales requieren revisión en la interfaz; los de integración requieren un mock de prueba instrumentado.

| Criterio | Casos | Precondiciones y datos sintéticos | Pasos y resultado esperado |
|---|---|---|---|
| Secuencia, paso actual, validación y conservación de datos | **UI-01**, **UI-02** | Frontend y backend en entorno de pruebas. Datos no sensibles de formulario; para KYC, `TEST-DEMO-001`. Viewports de 320, 768 y 1280 px, además de orientación móvil y zoom al 200%. | **UI-01:** iniciar el flujo; comprobar que se ven las tres etapas y que se señala el paso actual al avanzar. **UI-02:** intentar continuar con OTP vacío/mal formado y documento vacío, solo espacios o sin prefijo; comprobar que el avance queda bloqueado, el mensaje indica cómo corregir y los datos válidos ya ingresados se conservan. Comprobar carga, error, foco del primer campo inválido, uso por teclado y ausencia de scroll horizontal inesperado. |
| OTP local, sin SMS | **OTP-01**, **OTP-02** | Flujo nuevo en demo habilitada; mock de prueba con contador de solicitudes KYC y observación de salidas SMS, si existe infraestructura para ello. | **OTP-01:** enviar `123456`; se acepta y el flujo avanza a `OTP_VERIFIED`. **OTP-02:** probar `000000`, `123457` y `12345`; se rechazan, el flujo permanece en `STARTED` y no se llama al mock KYC. Verificar también que no se solicita ni envía SMS y que OTP/teléfono no aparecen en eventos o logs. |
| Payload KYC y representación fiel del estado | **KYC-01**, **KYC-02** | OTP verificado; mock aislado que capture la petición y permita elegir escenarios. Documento ficticio `TEST-DEMO-001`. | **KYC-01:** enviar datos válidos y comprobar que el backend llama al mock con `documentType=TEST` y documento con prefijo `TEST-`; la interfaz muestra el estado devuelto sin añadir requisitos KYC. **KYC-02:** enviar tipo distinto de `TEST`, documento sin prefijo y documento igual a `TEST-`; cada solicitud se rechaza antes de llamar al mock y se solicita un dato de prueba válido. |
| Aprobación, revisión pendiente y rechazo | **KYC-03**, **KYC-04**, **KYC-05** | Un flujo aislado por escenario; configurar el escenario del backend o la respuesta del mock según el contrato. | **KYC-03:** con `APPROVED` y estado final `ACTIVE`, la respuesta e interfaz muestran wallet activa. **KYC-04:** con `MANUAL_REVIEW`/`PENDING`, se informa que la revisión sigue pendiente y no se presenta la wallet como activa. **KYC-05:** con `REJECTED`, se informa el rechazo y `walletActive` no es `true`. |
| Resolver revisión manual | **KYC-06**, **KYC-07** | Flujo en `PENDING`; mock instrumentado para registrar decisión y consulta final. | **KYC-06:** desde la vista de resultado enviar decisión de demo `ACTIVE`; verificar que el backend la remite al mock, vuelve a consultar y solo muestra wallet activa si el estado final autoritativo es `ACTIVE`. **KYC-07:** repetir con `REJECTED`; comprobar consulta final, rechazo visible y wallet inactiva. Verificar que la resolución está en la misma vista y no aparece una consola independiente. |
| Indisponibilidad y reintento | **KYC-08** | Flujo OTP verificado; mock configurado para responder `503 KYC_UNAVAILABLE` y permitir después un resultado recuperable. | Enviar el flujo. Comprobar mensaje de error recuperable, ausencia de resultado KYC afirmado y wallet inactiva. Reintentar tras el `503` explícito y comprobar que se permite, sin duplicar altas ni activar antes de una respuesta autoritativa. |
| Eventos de ciclo y cierre | **EVT-01**, **EVT-02** | Entorno de prueba con acceso a los eventos persistidos y logs; flujo con ID sintético. OTP `123456` y documento ficticio para pruebas de escaneo. | **EVT-01:** iniciar, completar pasos, enviar y cerrar; verificar ID de flujo, tipo de evento y timestamps UTC suficientes para reconstruir el recorrido. **EVT-02:** cerrar antes del envío exitoso; verificar cierre `INCOMPLETE` y exclusión de flujos incompletos de la métrica de finalización. En ambos, confirmar que OTP, teléfono y documento no aparecen en eventos ni logs. |
| Duración, mediana y referencia de producto | **MET-01**, **MET-02** | Reloj controlable en pruebas; flujos completados e incompletos con timestamps sintéticos. Contrato de `/report` confirmado. | **MET-01:** fijar inicio en T0 y envío exitoso en T1; simular espera KYC y activación posteriores. La duración de onboarding debe ser T1−T0; KYC y activación se reportan aparte. **MET-02:** verificar mediana solo sobre flujos completados, comportamiento cuando no hay muestra y referencia de 3 minutos claramente identificada como referencia de producto, no resultado medido. |
| Sin pagos, MAU ni CAC | **LIM-01** | Aplicación y mock de prueba; observabilidad de rutas y llamadas salientes disponible. | Completar un flujo aprobado. Comprobar que no se invocan sistemas ni endpoints de pagos y que el resultado/reporte no incluye métricas MAU o CAC. |
| Transiciones, reintentos y concurrencia | **INT-01**, **INT-02** | Backend, H2 aislada y mock que cuente creaciones, consultas y decisiones. | **INT-01:** enviar simultáneamente dos solicitudes de envío para el mismo flujo; se espera una sola creación KYC y un estado consistente. Simular resultado de red ambiguo en creación; comprobar `SUBMISSION_UNKNOWN` y que no se repite automáticamente el POST. **INT-02:** probar decisiones desde estados distintos de `PENDING`; se espera rechazo de transición sin activar wallet ni llamar indebidamente al mock. |

## Cobertura por nivel

- **Unitaria:** validar OTP, tipo/prefijo de documento, transiciones, cálculo de duración y mediana con reloj controlado; comprobar serialización segura de eventos. La implementación y los nombres de clases no se proporcionaron, por lo que no se especifican clases de prueba unitarias.
- **Integración backend:** endpoints REST, H2 aislada, llamadas al mock, errores `503` y protección ante duplicados/concurrencia. Requiere confirmar los DTO del mock y el esquema de eventos.
- **Frontend:** pruebas de componente para navegación, validaciones, estados, accesibilidad y llamadas al API propio. El runner Angular no está confirmado.
- **Extremo a extremo/manual:** recorrido completo con escenarios aprobados, pendientes, rechazados e indisponibles; pruebas responsive, teclado, foco, mensajes y estado visible.
- **Evidencia negativa:** las verificaciones de ausencia de SMS, pagos, datos sensibles en logs/eventos y ausencia de llamadas duplicadas requieren observación del mock, logs o almacenamiento de prueba. No se pueden inferir solo a partir del texto de la interfaz.

## Código automatizado propuesto

El siguiente smoke test usa Bash, `curl` y `jq`; ejercita únicamente el contrato de API propuesto para OTP y validación local del documento. No envía un KYC válido. No comprueba por sí mismo los contadores del mock, logs, eventos, UI ni concurrencia.

```bash
# tests/onboarding_api_smoke.sh
#!/usr/bin/env bash
set -euo pipefail

# Smoke test de contrato propuesto. Ejecutar solo contra una instancia de pruebas.
BASE_URL="${BASE_URL:-http://localhost:8080}"
BASE_URL="${BASE_URL%/}"
TMP_DIR="$(mktemp -d)"
BODY="${TMP_DIR}/response.json"
trap 'rm -rf "$TMP_DIR"' EXIT

request() {
  local method="$1"
  local path="$2"
  local payload="${3-}"

  if [[ -n "$payload" ]]; then
    curl -sS -o "$BODY" -w '%{http_code}' \
      -X "$method" "${BASE_URL}${path}" \
      -H 'Content-Type: application/json' \
      --data "$payload"
  else
    curl -sS -o "$BODY" -w '%{http_code}' \
      -X "$method" "${BASE_URL}${path}"
  fi
}

assert_status() {
  local actual="$1"
  local expected="$2"
  local label="$3"

  if [[ "$actual" != "$expected" ]]; then
    printf 'FAIL: %s — esperado HTTP %s, recibido %s\n' \
      "$label" "$expected" "$actual" >&2
    cat "$BODY" >&2 || true
    exit 1
  fi
  printf 'PASS: %s — HTTP %s\n' "$label" "$actual"
}

assert_2xx() {
  local actual="$1"
  local label="$2"

  if [[ ! "$actual" =~ ^2[0-9][0-9]$ ]]; then
    printf 'FAIL: %s — esperado HTTP 2xx, recibido %s\n' \
      "$label" "$actual" >&2
    cat "$BODY" >&2 || true
    exit 1
  fi
  printf 'PASS: %s — HTTP %s\n' "$label" "$actual"
}

assert_state() {
  local expected="$1"
  local label="$2"
  local actual

  actual="$(jq -er '.state // empty' "$BODY")"
  if [[ "$actual" != "$expected" ]]; then
    printf 'FAIL: %s — esperado state=%s, recibido state=%s\n' \
      "$label" "$expected" "$actual" >&2
    cat "$BODY" >&2 || true
    exit 1
  fi
  printf 'PASS: %s — state=%s\n' "$label" "$actual"
}

# Inicio del flujo
status="$(request POST '/api/onboarding/flows' '{}')"
assert_2xx "$status" 'iniciar flujo'

FLOW_ID="$(jq -er '.flowId | strings | select(length > 0)' "$BODY")"
FLOW_PATH="/api/onboarding/flows/${FLOW_ID}"

# Códigos incorrectos: ninguno debe permitir avanzar.
for code in '000000' '123457' '12345'; do
  status="$(request POST "${FLOW_PATH}/otp" "{\"code\":\"${code}\"}")"
  assert_status "$status" '422' "rechazar OTP incorrecto (${code})"

  status="$(request GET "$FLOW_PATH")"
  assert_2xx "$status" "consultar flujo después de OTP incorrecto (${code})"
  assert_state 'STARTED' "no avanzar después de OTP incorrecto (${code})"
done

# OTP correcto de demostración.
status="$(request POST "${FLOW_PATH}/otp" '{"code":"123456"}')"
assert_2xx "$status" 'aceptar OTP de demostración'

status="$(request GET "$FLOW_PATH")"
assert_2xx "$status" 'consultar flujo después de OTP correcto'
assert_state 'OTP_VERIFIED' 'avanzar después del OTP correcto'

# Datos inválidos: cada intento debe ser rechazado localmente.
status="$(request POST "${FLOW_PATH}/submit" \
  '{"documentType":"OTHER","document":"TEST-DEMO-001"}')"
assert_status "$status" '422' 'rechazar tipo distinto de TEST'

status="$(request POST "${FLOW_PATH}/submit" \
  '{"documentType":"TEST","document":"DEMO-001"}')"
assert_status "$status" '422' 'rechazar documento sin prefijo TEST-'

status="$(request POST "${FLOW_PATH}/submit" \
  '{"documentType":"TEST","document":"TEST-"}')"
assert_status "$status" '422' 'rechazar documento sin sufijo'

status="$(request GET "$FLOW_PATH")"
assert_2xx "$status" 'consultar flujo después de documentos inválidos'
assert_state 'OTP_VERIFIED' 'no avanzar después de documento inválido'

# Cierre explícito anterior al envío exitoso: el contrato espera cierre 2xx.
status="$(request POST "${FLOW_PATH}/close" '{}')"
assert_2xx "$status" 'cerrar flujo incompleto'

printf 'Smoke test finalizado. Estas aserciones no verifican llamadas al mock, logs ni eventos.\n'
```

**Comando propuesto para ejecutarlo**, desde la raíz del repositorio y con el backend de pruebas ya iniciado:

```bash
BASE_URL=http://localhost:8080 bash tests/onboarding_api_smoke.sh
```

Criterio de aprobación: todas las aserciones terminan en `PASS` y el proceso sale con código `0`. Cualquier aserción fallida, error de conexión o JSON incompatible supone fallo del smoke test. El resultado real está **NO EJECUTADO**.

## Comandos reproducibles y estado de evidencia

Los comandos se proponen para los directorios indicados en el contexto; la existencia y configuración de esos directorios no fue verificada.

| Conjunto | Comando | Resultado esperado para aprobar | Estado |
|---|---|---|---|
| Backend, unitarias e integración existentes | `cd output/backend-quarkus && mvn test` | Finalización exitosa y todas las pruebas reportadas como exitosas; investigar y corregir cualquier fallo. | **NO EJECUTADO** |
| Frontend, pruebas | `cd output/frontend-angular && npm test` | Runner Angular confirmado y suite exitosa sin depender del backend ni del mock. La compatibilidad del runner sigue pendiente. | **NO EJECUTADO** |
| Frontend, build | `cd output/frontend-angular && npm run build` | Build exitoso, sin errores de compilación. | **NO EJECUTADO** |
| Smoke API propuesto | Backend de pruebas iniciado; después, `BASE_URL=http://localhost:8080 bash tests/onboarding_api_smoke.sh` desde la raíz | Todas las aserciones del script pasan. Requiere `curl` y `jq`. | **NO EJECUTADO** |
| Backend para una sesión manual/de pruebas | `cd output/backend-quarkus && ONBOARDING_DEMO_ENABLED=true MOCK_BASE_URL="http://localhost:8081" ONBOARDING_KYC_SCENARIO=APPROVED mvn quarkus:dev` | Arranque correcto en entorno local/de prueba con un mock aislado y una URL de mock configurada para ese entorno. No es una prueba por sí sola. | **NO EJECUTADO** |
| E2E de OTP, resultados y reintento | No se proporcionó comando ni runner E2E. | Definir runner, fixtures y contrato del mock; después ejecutar escenarios de UI y verificar respuestas y llamadas observadas. | **NO EJECUTADO / pendiente** |
| Responsive y accesibilidad | Revisión manual en navegador según la matriz **UI-01/UI-02**; herramienta/comando no especificado. | Sin pérdida de contenido, navegación por teclado funcional, etiquetas y errores accesibles, estados comprensibles y sin scroll horizontal inesperado. | **NO EJECUTADO** |

La configuración del comando de desarrollo es solo para pruebas locales y debe usar un mock aislado. No se debe ejecutar contra producción.

## Riesgos, limitaciones y pendientes

1. **Contrato incompleto:** confirmar esquemas exactos de respuesta del mock, errores propios y `/report`; no automatizar aserciones sobre campos no acordados.
2. **Protección de demo:** definir autenticación/autorización y verificar que OTP fijo, decisiones de demo y mock no estén habilitados en perfiles productivos.
3. **Observabilidad de seguridad:** facilitar acceso a logs y eventos de prueba para verificar que no contienen OTP, teléfono ni documento, sin exponer datos reales.
4. **Duplicados y concurrencia:** instrumentar el mock para contar verificaciones y probar solicitudes concurrentes del mismo flujo, reintentos tras `503` explícito y resultado de red ambiguo. El smoke test incluido no cubre estos casos.
5. **Eventos y métricas:** confirmar esquema H2, nombres de eventos, idempotencia de cierre y DTO del reporte. Probar con reloj controlado; no presentar medianas sin muestra observada.
6. **Frontend:** falta confirmar el runner y el comando E2E. No se proporcionaron archivos de componentes, contratos implementados ni evidencia de revisión visual.
7. **Abandono del flujo:** el cierre por pérdida abrupta de pestaña o conectividad no puede garantizarse; la medición debe depender de eventos confirmados, como especifica el diseño.
8. **Límites de datos de prueba:** falta definir el formato permitido del sufijo `TEST-`; no añadir límites arbitrarios a las aserciones.
9. **Sin evidencia de ejecución:** no se observó salida de Maven, npm, navegador ni mock. Por ello, ninguna prueba se declara ejecutada ni se afirma cobertura obtenida.

**Conclusión:** el plan cubre los criterios de aceptación a nivel de diseño y aporta un smoke test propuesto para una parte del contrato backend. HU-01 no se considera validada hasta ejecutar las suites en entornos aislados, cubrir los casos pendientes y conservar evidencia verificable.