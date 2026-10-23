# backend_spec.md

## Alcance y decisión de contrato

La implementación usa Quarkus 3 y Java 17. El backend es el único componente que llama al mock KYC; OTP se valida localmente y no se solicita ni envía SMS. La configuración de demo está deshabilitada por defecto.

Rutas propias:

| Método y ruta | Función |
|---|---|
| `POST /api/onboarding/flows` | Iniciar un flujo. |
| `POST /api/onboarding/flows/{flowId}/otp` | Verificar el OTP local. |
| `POST /api/onboarding/flows/{flowId}/submit` | Enviar datos de prueba al mock KYC. |
| `GET /api/onboarding/flows/{flowId}` | Consultar el estado local del flujo. |
| `POST /api/onboarding/flows/{flowId}/decision` | Resolver una revisión pendiente con `ACTIVE` o `REJECTED`, y consultar el resultado final. |
| `POST /api/onboarding/flows/{flowId}/close` | Registrar el cierre, como `SUBMITTED` o `INCOMPLETE`. |
| `GET /api/onboarding/report` | Consultar medianas de duración observadas en H2. |

El cuerpo de `submit` solo admite `documentType` y `document`. El escenario KYC es configuración de backend, no una opción del usuario. Los contratos del mock consumidos son `POST /kyc/verifications`, `GET /kyc/verifications/{id}` y `POST /kyc/verifications/{id}/decision`.

## Criterios de aceptación y su implementación

| Criterio | Contrato, validación e implementación | Errores y acceso a datos |
|---|---|---|
| Secuencia de pasos, avance bloqueado y errores accionables | La respuesta incluye los tres pasos `PHONE_OTP`, `KYC_DATA`, `RESULT` y `currentStep`. El servicio impide avanzar desde un estado distinto al requerido. | HTTP `409 INVALID_STATE` para una transición no permitida. El estado del flujo se guarda en H2. |
| OTP fijo, local y sin SMS | `POST .../{flowId}/otp`, cuerpo `{"code":"123456"}`. Se acepta exclusivamente el string de seis dígitos `123456`. No se persisten el código ni el teléfono ni se registran en eventos. | `422 OTP_INVALID`; el estado continúa en `STARTED` y no se llama al mock. Se puede deshabilitar toda la demo mediante configuración. |
| Envío del KYC de prueba | `POST .../{flowId}/submit`, cuerpo `{"documentType":"TEST","document":"TEST-DEMO-001"}`. Se valida tipo exacto `TEST` y prefijo `TEST-` con sufijo no vacío antes de llamar al mock. | `422 TEST_DOCUMENT_REQUIRED` o `422 TEST_DOCUMENT_INVALID`; no se llama al mock. El documento solo vive en memoria durante la llamada y no se guarda en H2 ni eventos. |
| `APPROVED/ACTIVE`, `MANUAL_REVIEW/PENDING` y `REJECTED` | El estado autoritativo del mock se traduce a `ACTIVE`, `PENDING` o `REJECTED`. La respuesta propia incluye `walletActive`; solo es `true` para `ACTIVE`. | El estado y los timestamps se persisten. Una respuesta no reconocida del proveedor no activa la wallet y se trata como error de integración. |
| Resolver revisión manual | `POST .../{flowId}/decision`, cuerpo `{"decision":"ACTIVE"}` o `{"decision":"REJECTED"}`. Solo se admite para `PENDING`; el backend envía la decisión y consulta el mock de nuevo. | `409 INVALID_STATE` para otros estados. Solo la respuesta final autoritativa puede activar la wallet. |
| Mock no disponible | Un `503` explícito en la creación se devuelve como `503 KYC_UNAVAILABLE`, se restaura el flujo a `OTP_VERIFIED` y se permite reintentar. | No se declara resultado KYC ni se activa la wallet. Un timeout o resultado ambiguo de creación se marca `SUBMISSION_UNKNOWN` y no se repite el `POST`. |
| Eventos de ciclo y cierre incompleto | Se guardan `FLOW_STARTED`, `STEP_COMPLETED`, `FLOW_SUBMITTED`, `KYC_SUBMISSION_STARTED` y `FLOW_CLOSED` con ID, paso, resultado y timestamp UTC. | La tabla de eventos no contiene OTP, celular ni documento. Cerrar sin `submittedAt` produce `INCOMPLETE`; no entra en la métrica de finalización. |
| Duración y medianas | `submittedAt - startedAt` define duración del onboarding. `kycStartedAt`/`kycCompletedAt` y `submittedAt`/`activatedAt` permiten reportar por separado KYC y activación. | `GET /api/onboarding/report` devuelve medianas y tamaño de muestra únicamente de H2 en memoria. La referencia de producto es `180000` ms; no se afirma que el MVP valide impacto. |
| Documento o tipo inválido | Validación local antes de la llamada HTTP; `documentType` debe ser exactamente `TEST`; documento debe empezar por `TEST-` y tener sufijo. | Error `422`; el mock no recibe datos inválidos. |
| Sin pagos, MAU o CAC | No existen endpoints ni servicios de pagos. El reporte solo incluye duraciones y tamaño de muestra. | No se crean ni procesan pagos; no hay campos de MAU o CAC. |

## Estados y transacciones

Estados persistidos: `STARTED`, `OTP_VERIFIED`, `SUBMITTING`, `PENDING`, `ACTIVE`, `REJECTED` y `SUBMISSION_UNKNOWN`.

Cada escritura de estado y sus eventos correspondientes se realiza en una transacción JDBC local. El estado `SUBMITTING` se confirma en H2 **antes** de llamar al mock; no se deja abierta una transacción durante la llamada remota. Una comparación de estado en la actualización impide que dos solicitudes del mismo flujo creen verificaciones duplicadas.

- Un `503` explícito al crear significa que no se creó una verificación: se puede reintentar.
- Una respuesta de red ambigua al crear no se reintenta automáticamente: queda `SUBMISSION_UNKNOWN`.
- Si ya se guardó un ID KYC pero falló la consulta posterior, se puede consultar ese ID al reintentar; no se crea otra verificación.
- H2 en memoria contiene únicamente la sesión, el ID de verificación KYC, timestamps y eventos mínimos. No se guardan documento, OTP ni celular.
- No se propone migración productiva. El esquema se crea al iniciar la aplicación. No se presupone un contrato de Datos activo.

## Configuración

Propiedades usadas por el código (también configurables como variables de entorno):

- `ONBOARDING_DEMO_ENABLED=false` por defecto. Activar solo para el perfil de demo.
- `MOCK_BASE_URL=http://localhost:8081` por defecto; sustituir por la URL del mock asignada al grupo. No hay una URL de grupo codificada.
- `ONBOARDING_KYC_SCENARIO=APPROVED` por defecto. Valores admitidos: `APPROVED`, `REJECTED`, `MANUAL_REVIEW`, `UNAVAILABLE`. El usuario no elige el escenario.

La configuración de despliegue debe mantener la demo deshabilitada en perfiles productivos y proteger estos endpoints con los controles de acceso disponibles en la aplicación. El contexto no define un proveedor de identidad o rol que permita implementar autorización adicional aquí.

## Recorridos de comprobación

**Caso válido:** iniciar flujo, validar OTP y enviar un documento ficticio. Con el escenario `APPROVED`, la respuesta de envío debe indicar `state: ACTIVE` y `walletActive: true`.

**Caso de error:** iniciar otro flujo y enviar `000000` como OTP. Debe responder `422 OTP_INVALID`, conservar el estado `STARTED` y no llamar al mock.

Comandos para ejecutar desde `output/backend-quarkus`:

```bash
mvn test
```

Iniciar con el mock del grupo configurado:

```bash
ONBOARDING_DEMO_ENABLED=true \
MOCK_BASE_URL="http://localhost:8081" \
ONBOARDING_KYC_SCENARIO=APPROVED \
mvn quarkus:dev
```

En otra terminal, iniciar y guardar un flujo:

```bash
FLOW_ID=$(curl -sS -X POST http://localhost:8080/api/onboarding/flows \
  -H 'Content-Type: application/json' \
  -d '{}' | jq -r '.flowId')
echo "$FLOW_ID"
```

Caso válido:

```bash
curl -i -X POST "http://localhost:8080/api/onboarding/flows/$FLOW_ID/otp" \
  -H 'Content-Type: application/json' \
  -d '{"code":"123456"}'

curl -i -X POST "http://localhost:8080/api/onboarding/flows/$FLOW_ID/submit" \
  -H 'Content-Type: application/json' \
  -d '{"documentType":"TEST","document":"TEST-DEMO-001"}'

curl -i "http://localhost:8080/api/onboarding/flows/$FLOW_ID"
```

Caso OTP inválido:

```bash
ERROR_FLOW_ID=$(curl -sS -X POST http://localhost:8080/api/onboarding/flows \
  -H 'Content-Type: application/json' \
  -d '{}' | jq -r '.flowId')

curl -i -X POST "http://localhost:8080/api/onboarding/flows/$ERROR_FLOW_ID/otp" \
  -H 'Content-Type: application/json' \
  -d '{"code":"000000"}'
```

Reporte:

```bash
curl -i http://localhost:8080/api/onboarding/report
```

Los comandos son pasos de comprobación reproducibles; no se afirma que se hayan ejecutado.

## Código Java

```java
// FlowState.java
package model;

public enum FlowState {
    STARTED,
    OTP_VERIFIED,
    SUBMITTING,
    PENDING,
    ACTIVE,
    REJECTED,
    SUBMISSION_UNKNOWN
}
```

```java
// FlowEventType.java
package model;

public enum FlowEventType {
    FLOW_STARTED,
    STEP_COMPLETED,
    FLOW_SUBMITTED,
    KYC_SUBMISSION_STARTED,
    KYC_VERIFICATION_CREATED,
    KYC_UNAVAILABLE,
    KYC_RESULT,
    SUBMISSION_UNKNOWN,
    FLOW_CLOSED
}
```

```java
// OnboardingFlow.java
package model;

import java.time.Instant;
import java.util.UUID;

public record OnboardingFlow(
        UUID flowId,
        FlowState state,
        Instant startedAt,
        Instant submittedAt,
        Instant kycStartedAt,
        Instant kycCompletedAt,
        Instant activatedAt,
        String kycVerificationId,
        String closeResult,
        Instant closedAt) {
}
```

```java
// OnboardingEvent.java
package model;

import java.time.Instant;
import java.util.UUID;

public record OnboardingEvent(
        UUID flowId,
        FlowEventType type,
        String step,
        String result,
        Instant occurredAt) {
}
```

```java
// FlowMetrics.java
package model;

import java.time.Instant;

public record FlowMetrics(
        Instant startedAt,
        Instant submittedAt,
        Instant kycStartedAt,
        Instant kycCompletedAt,
        Instant activatedAt) {
}
```

```java
// KycOutcome.java
package model;

public record KycOutcome(String status, String walletStatus) {
}
```

```java
// FlowResponse.java
package dto;

import java.time.Instant;
import java.util.List;

public record FlowResponse(
        String flowId,
        String state,
        String currentStep,
        List<String> requiredSteps,
        String kycStatus,
        String walletStatus,
        boolean walletActive,
        boolean retryable,
        Instant submittedAt,
        String closeResult,
        String message) {
}
```

```java
// OtpRequest.java
package dto;

public record OtpRequest(String code) {
}
```

```java
// SubmitRequest.java
package dto;

public record SubmitRequest(String documentType, String document) {
}
```

```java
// DecisionRequest.java
package dto;

public record DecisionRequest(String decision) {
}
```

```java
// ErrorResponse.java
package dto;

public record ErrorResponse(String code, String message, boolean retryable) {
}
```

```java
// ReportResponse.java
package dto;

public record ReportResponse(
        long sampleCount,
        Long medianObservedOnboardingMs,
        Long medianKycMs,
        Long medianActivationMs,
        long productReferenceMs,
        String measurementDefinition) {
}
```

```java
// OnboardingException.java
package service;

public class OnboardingException extends RuntimeException {
    private final int httpStatus;
    private final String code;
    private final boolean retryable;

    public OnboardingException(int httpStatus, String code, String message, boolean retryable) {
        super(message);
        this.httpStatus = httpStatus;
        this.code = code;
        this.retryable = retryable;
    }

    public int getHttpStatus() {
        return httpStatus;
    }

    public String getCode() {
        return code;
    }

    public boolean isRetryable() {
        return retryable;
    }

    public static OnboardingException badRequest(String code, String message) {
        return new OnboardingException(400, code, message, false);
    }

    public static OnboardingException notFound() {
        return new OnboardingException(404, "FLOW_NOT_FOUND", "No se encontró el flujo.", false);
    }

    public static OnboardingException invalidState(String message) {
        return new OnboardingException(409, "INVALID_STATE", message, false);
    }

    public static OnboardingException validation(String code, String message) {
        return new OnboardingException(422, code, message, false);
    }
}
```

```java
// KycException.java
package service;

public class KycException extends RuntimeException {
    public enum Phase {
        CREATE,
        GET,
        DECISION
    }

    private final Phase phase;
    private final int httpStatus;

    public KycException(Phase phase, int httpStatus, String message) {
        super(message);
        this.phase = phase;
        this.httpStatus = httpStatus;
    }

    public Phase getPhase() {
        return phase;
    }

    public int getHttpStatus() {
        return httpStatus;
    }
}
```

```java
// KycGateway.java
package service;

import model.KycOutcome;

public interface KycGateway {
    String createVerification(String documentType, String document);

    KycOutcome getVerification(String verificationId);

    void decide(String verificationId, String decision);
}
```

```java
// HttpKycGateway.java
package service;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import jakarta.enterprise.context.ApplicationScoped;
import jakarta.inject.Inject;
import java.io.IOException;
import java.net.URI;
import java.net.URLEncoder;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.charset.StandardCharsets;
import java.time.Duration;
import java.util.Locale;
import java.util.Map;
import org.eclipse.microprofile.config.inject.ConfigProperty;
import model.KycOutcome;

@ApplicationScoped
public class HttpKycGateway implements KycGateway {
    private final ObjectMapper mapper;
    private final HttpClient client;
    private final String baseUrl;
    private final String scenario;

    @Inject
    public HttpKycGateway(
            ObjectMapper mapper,
            @ConfigProperty(name = "mock.base-url", defaultValue = "http://localhost:8081")
            String baseUrl,
            @ConfigProperty(name = "onboarding.kyc-scenario", defaultValue = "APPROVED")
            String scenario) {
        this.mapper = mapper;
        this.client = HttpClient.newBuilder()
                .connectTimeout(Duration.ofSeconds(5))
                .build();

        String normalizedUrl = baseUrl == null ? "" : baseUrl.trim();
        while (normalizedUrl.endsWith("/")) {
            normalizedUrl = normalizedUrl.substring(0, normalizedUrl.length() - 1);
        }
        if (!(normalizedUrl.startsWith("http://") || normalizedUrl.startsWith("https://"))) {
            throw new IllegalArgumentException("mock.base-url debe ser una URL HTTP o HTTPS.");
        }
        this.baseUrl = normalizedUrl;

        String normalizedScenario = scenario == null ? "APPROVED"
                : scenario.trim().toUpperCase(Locale.ROOT);
        if (!normalizedScenario.equals("APPROVED")
                && !normalizedScenario.equals("REJECTED")
                && !normalizedScenario.equals("MANUAL_REVIEW")
                && !normalizedScenario.equals("UNAVAILABLE")) {
            throw new IllegalArgumentException("Escenario KYC de demo no válido.");
        }
        this.scenario = normalizedScenario;
    }

    @Override
    public String createVerification(String documentType, String document) {
        String body = writeJson(Map.of(
                "documentType", documentType,
                "document", document,
                "scenario", scenario));

        HttpResponse<String> response = send(
                HttpRequest.newBuilder(URI.create(baseUrl + "/kyc/verifications"))
                        .timeout(Duration.ofSeconds(10))
                        .header("Content-Type", "application/json")
                        .POST(HttpRequest.BodyPublishers.ofString(body))
                        .build(),
                KycException.Phase.CREATE);

        try {
            JsonNode root = mapper.readTree(response.body());
            String id = text(root, "id", "verificationId");
            if (id == null || id.isBlank()) {
                throw new KycException(
                        KycException.Phase.CREATE, 502, "Respuesta KYC sin identificador.");
            }
            return id;
        } catch (IOException e) {
            throw new KycException(
                    KycException.Phase.CREATE, 502, "Respuesta KYC no válida.");
        }
    }

    @Override
    public KycOutcome getVerification(String verificationId) {
        String encodedId = URLEncoder.encode(verificationId, StandardCharsets.UTF_8)
                .replace("+", "%20");
        HttpResponse<String> response = send(
                HttpRequest.newBuilder(URI.create(
                                baseUrl + "/kyc/verifications/" + encodedId))
                        .timeout(Duration.ofSeconds(10))
                        .GET()
                        .build(),
                KycException.Phase.GET);

        try {
            JsonNode root = mapper.readTree(response.body());
            String status = text(root, "status", "kycStatus", "result");
            String walletStatus = text(root, "walletStatus", "wallet_state");
            return new KycOutcome(normalize(status), normalize(walletStatus));
        } catch (IOException e) {
            throw new KycException(
                    KycException.Phase.GET, 502, "Respuesta KYC no válida.");
        }
    }

    @Override
    public void decide(String verificationId, String decision) {
        String encodedId = URLEncoder.encode(verificationId, StandardCharsets.UTF_8)
                .replace("+", "%20");
        String body = writeJson(Map.of("decision", decision));

        send(
                HttpRequest.newBuilder(URI.create(
                                baseUrl + "/kyc/verifications/" + encodedId + "/decision"))
                        .timeout(Duration.ofSeconds(10))
                        .header("Content-Type", "application/json")
                        .POST(HttpRequest.BodyPublishers.ofString(body))
                        .build(),
                KycException.Phase.DECISION);
    }

    private HttpResponse<String> send(HttpRequest request, KycException.Phase phase) {
        try {
            HttpResponse<String> response = client.send(
                    request, HttpResponse.BodyHandlers.ofString(StandardCharsets.UTF_8));
            if (response.statusCode() < 200 || response.statusCode() >= 300) {
                throw new KycException(
                        phase, response.statusCode(), "El proveedor KYC devolvió un error.");
            }
            return response;
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            throw new KycException(phase, 0, "La solicitud KYC fue interrumpida.");
        } catch (IOException e) {
            throw new KycException(phase, 0, "No se pudo confirmar la respuesta KYC.");
        }
    }

    private String writeJson(Object value) {
        try {
            return mapper.writeValueAsString(value);
        } catch (IOException e) {
            throw new KycException(
                    KycException.Phase.CREATE, 502, "No se pudo construir la solicitud KYC.");
        }
    }

    private static String text(JsonNode root, String... fields) {
        for (String field : fields) {
            JsonNode value = root.get(field);
            if (value != null && value.isValueNode() && !value.isNull()) {
                return value.asText();
            }
        }
        return null;
    }

    private static String normalize(String value) {
        return value == null ? null : value.trim().toUpperCase(Locale.ROOT);
    }
}
```

```java
// JdbcOnboardingRepository.java
package repository;

import jakarta.annotation.PostConstruct;
import jakarta.enterprise.context.ApplicationScoped;
import jakarta.inject.Inject;
import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.sql.Statement;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.UUID;
import javax.sql.DataSource;
import model.FlowEventType;
import model.FlowMetrics;
import model.FlowState;
import model.OnboardingEvent;
import model.OnboardingFlow;

@ApplicationScoped
public class JdbcOnboardingRepository {
    private final DataSource dataSource;

    @Inject
    public JdbcOnboardingRepository(DataSource dataSource) {
        this.dataSource = dataSource;
    }

    @PostConstruct
    void initializeSchema() {
        try (Connection connection = dataSource.getConnection();
             Statement statement = connection.createStatement()) {
            statement.execute("""
                    CREATE TABLE IF NOT EXISTS wallet_onboarding_flow (
                        flow_id VARCHAR(36) PRIMARY KEY,
                        state VARCHAR(32) NOT NULL,
                        started_at VARCHAR(40) NOT NULL,
                        submitted_at VARCHAR(40),
                        kyc_started_at VARCHAR(40),
                        kyc_completed_at VARCHAR(40),
                        activated_at VARCHAR(40),
                        kyc_verification_id VARCHAR(200),
                        close_result VARCHAR(20),
                        closed_at VARCHAR(40)
                    )
                    """);
            statement.execute("""
                    CREATE TABLE IF NOT EXISTS wallet_onboarding_event (
                        event_id BIGINT GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
                        flow_id VARCHAR(36) NOT NULL,
                        event_type VARCHAR(40) NOT NULL,
                        step_name VARCHAR(40),
                        result VARCHAR(40),
                        occurred_at VARCHAR(40) NOT NULL,
                        CONSTRAINT fk_onboarding_event_flow
                            FOREIGN KEY (flow_id)
                            REFERENCES wallet_onboarding_flow(flow_id)
                    )
                    """);
        } catch (SQLException e) {
            throw storageFailure(e);
        }
    }

    public void create(OnboardingFlow flow, OnboardingEvent event) {
        try (Connection connection = dataSource.getConnection()) {
            connection.setAutoCommit(false);
            try {
                insertFlow(connection, flow);
                insertEvents(connection, List.of(event));
                connection.commit();
            } catch (SQLException e) {
                rollback(connection);
                throw storageFailure(e);
            }
        } catch (SQLException e) {
            throw storageFailure(e);
        }
    }

    public OnboardingFlow findById(UUID flowId) {
        try (Connection connection = dataSource.getConnection();
             PreparedStatement statement = connection.prepareStatement(
                     "SELECT * FROM wallet_onboarding_flow WHERE flow_id = ?")) {
            statement.setString(1, flowId.toString());
            try (ResultSet rs = statement.executeQuery()) {
                return rs.next() ? readFlow(rs) : null;
            }
        } catch (SQLException e) {
            throw storageFailure(e);
        }
    }

    public boolean transition(
            OnboardingFlow updated,
            FlowState expectedState,
            List<OnboardingEvent> events) {
        try (Connection connection = dataSource.getConnection()) {
            connection.setAutoCommit(false);
            try {
                int changed = updateFlow(connection, updated, expectedState);
                if (changed != 1) {
                    connection.rollback();
                    return false;
                }
                insertEvents(connection, events);
                connection.commit();
                return true;
            } catch (SQLException e) {
                rollback(connection);
                throw storageFailure(e);
            }
        } catch (SQLException e) {
            throw storageFailure(e);
        }
    }

    public boolean claimSubmission(UUID flowId, Instant now) {
        try (Connection connection = dataSource.getConnection()) {
            connection.setAutoCommit(false);
            try {
                OnboardingFlow current;
                try (PreparedStatement select = connection.prepareStatement(
                        "SELECT * FROM wallet_onboarding_flow WHERE flow_id = ? FOR UPDATE")) {
                    select.setString(1, flowId.toString());
                    try (ResultSet rs = select.executeQuery()) {
                        if (!rs.next()) {
                            connection.rollback();
                            return false;
                        }
                        current = readFlow(rs);
                    }
                }

                if (current.state() != FlowState.OTP_VERIFIED || current.closedAt() != null) {
                    connection.rollback();
                    return false;
                }

                boolean firstSubmission = current.submittedAt() == null;
                Instant submittedAt = firstSubmission ? now : current.submittedAt();
                OnboardingFlow updated = new OnboardingFlow(
                        current.flowId(),
                        FlowState.SUBMITTING,
                        current.startedAt(),
                        submittedAt,
                        now,
                        null,
                        current.activatedAt(),
                        null,
                        current.closeResult(),
                        current.closedAt());

                if (updateFlow(connection, updated, FlowState.OTP_VERIFIED) != 1) {
                    connection.rollback();
                    return false;
                }

                List<OnboardingEvent> events = new ArrayList<>();
                if (firstSubmission) {
                    events.add(new OnboardingEvent(
                            flowId, FlowEventType.FLOW_SUBMITTED, "KYC_DATA",
                            "SUBMITTED", now));
                }
                events.add(new OnboardingEvent(
                        flowId, FlowEventType.KYC_SUBMISSION_STARTED, "KYC_DATA",
                        "STARTED", now));
                insertEvents(connection, events);
                connection.commit();
                return true;
            } catch (SQLException e) {
                rollback(connection);
                throw storageFailure(e);
            }
        } catch (SQLException e) {
            throw storageFailure(e);
        }
    }

    public List<FlowMetrics> findMetrics() {
        List<FlowMetrics> metrics = new ArrayList<>();
        try (Connection connection = dataSource.getConnection();
             PreparedStatement statement = connection.prepareStatement("""
                     SELECT started_at, submitted_at, kyc_started_at,
                            kyc_completed_at, activated_at
                     FROM wallet_onboarding_flow
                     WHERE submitted_at IS NOT NULL
                     """);
             ResultSet rs = statement.executeQuery()) {
            while (rs.next()) {
                metrics.add(new FlowMetrics(
                        instant(rs.getString("started_at")),
                        instant(rs.getString("submitted_at")),
                        instant(rs.getString("kyc_started_at")),
                        instant(rs.getString("kyc_completed_at")),
                        instant(rs.getString("activated_at"))));
            }
            return metrics;
        } catch (SQLException e) {
            throw storageFailure(e);
        }
    }

    private static int updateFlow(
            Connection connection, OnboardingFlow flow, FlowState expectedState)
            throws SQLException {
        try (PreparedStatement statement = connection.prepareStatement("""
                UPDATE wallet_onboarding_flow
                SET state = ?, started_at = ?, submitted_at = ?, kyc_started_at = ?,
                    kyc_completed_at = ?, activated_at = ?, kyc_verification_id = ?,
                    close_result = ?, closed_at = ?
                WHERE flow_id = ? AND state = ?
                """)) {
            bindFlowUpdate(statement, flow);
            statement.setString(10, flow.flowId().toString());
            statement.setString(11, expectedState.name());
            return statement.executeUpdate();
        }
    }

    private static void insertFlow(Connection connection, OnboardingFlow flow)
            throws SQLException {
        try (PreparedStatement statement = connection.prepareStatement("""
                INSERT INTO wallet_onboarding_flow
                (flow_id, state, started_at, submitted_at, kyc_started_at,
                 kyc_completed_at, activated_at, kyc_verification_id, close_result, closed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """)) {
            statement.setString(1, flow.flowId().toString());
            statement.setString(2, flow.state().name());
            statement.setString(3, text(flow.startedAt()));
            statement.setString(4, text(flow.submittedAt()));
            statement.setString(5, text(flow.kycStartedAt()));
            statement.setString(6, text(flow.kycCompletedAt()));
            statement.setString(7, text(flow.activatedAt()));
            statement.setString(8, flow.kycVerificationId());
            statement.setString(9, flow.closeResult());
            statement.setString(10, text(flow.closedAt()));
            statement.executeUpdate();
        }
    }

    private static void bindFlowUpdate(PreparedStatement statement, OnboardingFlow flow)
            throws SQLException {
        statement.setString(1, flow.state().name());
        statement.setString(2, text(flow.startedAt()));
        statement.setString(3, text(flow.submittedAt()));
        statement.setString(4, text(flow.kycStartedAt()));
        statement.setString(5, text(flow.kycCompletedAt()));
        statement.setString(6, text(flow.activatedAt()));
        statement.setString(7, flow.kycVerificationId());
        statement.setString(8, flow.closeResult());
        statement.setString(9, text(flow.closedAt()));
    }

    private static void insertEvents(
            Connection connection, List<OnboardingEvent> events) throws SQLException {
        try (PreparedStatement statement = connection.prepareStatement("""
                INSERT INTO wallet_onboarding_event
                    (flow_id, event_type, step_name, result, occurred_at)
                VALUES (?, ?, ?, ?, ?)
                """)) {
            for (OnboardingEvent event : events) {
                statement.setString(1, event.flowId().toString());
                statement.setString(2, event.type().name());
                statement.setString(3, event.step());
                statement.setString(4, event.result());
                statement.setString(5, text(event.occurredAt()));
                statement.addBatch();
            }
            statement.executeBatch();
        }
    }

    private static OnboardingFlow readFlow(ResultSet rs) throws SQLException {
        return new OnboardingFlow(
                UUID.fromString(rs.getString("flow_id")),
                FlowState.valueOf(rs.getString("state")),
                instant(rs.getString("started_at")),
                instant(rs.getString("submitted_at")),
                instant(rs.getString("kyc_started_at")),
                instant(rs.getString("kyc_completed_at")),
                instant(rs.getString("activated_at")),
                rs.getString("kyc_verification_id"),
                rs.getString("close_result"),
                instant(rs.getString("closed_at")));
    }

    private static String text(Instant instant) {
        return instant == null ? null : instant.toString();
    }

    private static Instant instant(String value) {
        return value == null ? null : Instant.parse(value);
    }

    private static void rollback(Connection connection) {
        try {
            connection.rollback();
        } catch (SQLException ignored) {
            // Se conserva el error original.
        }
    }

    private static IllegalStateException storageFailure(SQLException cause) {
        return new IllegalStateException("Error de persistencia del onboarding.", cause);
    }
}
```

```java
// OnboardingService.java
package service;

import dto.FlowResponse;
import dto.ReportResponse;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.Locale;
import java.util.UUID;
import java.util.stream.Collectors;
import jakarta.enterprise.context.ApplicationScoped;
import jakarta.inject.Inject;
import model.FlowEventType;
import model.FlowMetrics;
import model.FlowState;
import model.KycOutcome;
import model.OnboardingEvent;
import model.OnboardingFlow;
import org.eclipse.microprofile.config.inject.ConfigProperty;
import repository.JdbcOnboardingRepository;

@ApplicationScoped
public class OnboardingService {
    private static final List<String> REQUIRED_STEPS =
            List.of("PHONE_OTP", "KYC_DATA", "RESULT");
    private static final long PRODUCT_REFERENCE_MS = 180_000L;

    private final JdbcOnboardingRepository repository;
    private final KycGateway kycGateway;
    private final boolean demoEnabled;

    @Inject
    public OnboardingService(
            JdbcOnboardingRepository repository,
            KycGateway kycGateway,
            @ConfigProperty(name = "onboarding.demo-enabled", defaultValue = "false")
            boolean demoEnabled) {
        this.repository = repository;
        this.kycGateway = kycGateway;
        this.demoEnabled = demoEnabled;
    }

    public FlowResponse start() {
        requireDemoEnabled();
        Instant now = Instant.now();
        UUID id = UUID.randomUUID();
        OnboardingFlow flow = new OnboardingFlow(
                id, FlowState.STARTED, now, null, null, null, null, null, null, null);
        repository.create(flow, event(
                id, FlowEventType.FLOW_STARTED, "PHONE_OTP", "STARTED", now));
        return response(flow);
    }

    public FlowResponse verifyOtp(String flowId, String code) {
        requireDemoEnabled();
        OnboardingFlow current = findRequired(flowId);
        ensureOpen(current);

        if (current.state() != FlowState.STARTED) {
            throw OnboardingException.invalidState("El flujo no está esperando la verificación OTP.");
        }
        if (code == null || !code.matches("[0-9]{6}") || !"123456".equals(code)) {
            throw OnboardingException.validation(
                    "OTP_INVALID", "Código no válido. Para la demo, ingresa el código de seis dígitos.");
        }

        Instant now = Instant.now();
        OnboardingFlow updated = new OnboardingFlow(
                current.flowId(), FlowState.OTP_VERIFIED, current.startedAt(),
                current.submittedAt(), current.kycStartedAt(), current.kycCompletedAt(),
                current.activatedAt(), current.kycVerificationId(),
                current.closeResult(), current.closedAt());

        boolean saved = repository.transition(
                updated,
                FlowState.STARTED,
                List.of(
                        event(current.flowId(), FlowEventType.STEP_COMPLETED,
                                "PHONE_OTP", "COMPLETED", now)));
        if (!saved) {
            throw OnboardingException.invalidState("El flujo cambió; consulta su estado e inténtalo de nuevo.");
        }
        return response(updated);
    }

    public FlowResponse submit(String flowId, String documentType, String document) {
        requireDemoEnabled();
        validateTestDocument(documentType, document);

        OnboardingFlow current = findRequired(flowId);
        ensureOpen(current);

        if (current.state() == FlowState.SUBMISSION_UNKNOWN
                && current.kycVerificationId() != null) {
            return refreshUnknown(current);
        }
        if (current.state() != FlowState.OTP_VERIFIED) {
            if (current.state() == FlowState.SUBMISSION_UNKNOWN) {
                throw new OnboardingException(
                        409, "SUBMISSION_UNKNOWN",
                        "No se pudo confirmar el envío. No se repetirá la creación automáticamente.",
                        false);
            }
            throw OnboardingException.invalidState("Completa primero la verificación OTP.");
        }

        Instant now = Instant.now();
        if (!repository.claimSubmission(current.flowId(), now)) {
            throw OnboardingException.invalidState("El flujo ya se está procesando o cambió de estado.");
        }

        try {
            String kycId = kycGateway.createVerification("TEST", document);
            OnboardingFlow submitting = findRequired(flowId);
            OnboardingFlow withKycId = new OnboardingFlow(
                    submitting.flowId(), FlowState.SUBMITTING, submitting.startedAt(),
                    submitting.submittedAt(), submitting.kycStartedAt(),
                    submitting.kycCompletedAt(), submitting.activatedAt(),
                    kycId, submitting.closeResult(), submitting.closedAt());

            if (!repository.transition(
                    withKycId,
                    FlowState.SUBMITTING,
                    List.of(event(current.flowId(), FlowEventType.KYC_VERIFICATION_CREATED,
                            "KYC_DATA", "CREATED", Instant.now())))) {
                throw OnboardingException.invalidState("No se pudo guardar el estado de la verificación.");
            }

            KycOutcome outcome = kycGateway.getVerification(kycId);
            return applyOutcome(findRequired(flowId), outcome);
        } catch (KycException e) {
            return handleSubmissionFailure(flowId, e);
        }
    }

    public FlowResponse get(String flowId) {
        requireDemoEnabled();
        return response(findRequired(flowId));
    }

    public FlowResponse decide(String flowId, String decision) {
        requireDemoEnabled();
        OnboardingFlow current = findRequired(flowId);
        ensureOpen(current);

        String normalized = decision == null ? "" : decision.trim().toUpperCase(Locale.ROOT);
        if (!normalized.equals("ACTIVE") && !normalized.equals("REJECTED")) {
            throw OnboardingException.validation(
                    "INVALID_DECISION", "La decisión debe ser ACTIVE o REJECTED.");
        }
        if (current.state() != FlowState.PENDING || current.kycVerificationId() == null) {
            throw OnboardingException.invalidState("Solo se puede resolver una revisión pendiente.");
        }

        try {
            kycGateway.decide(current.kycVerificationId(), normalized);
            KycOutcome outcome = kycGateway.getVerification(current.kycVerificationId());
            FlowState finalState = outcomeState(outcome);
            if (finalState == FlowState.PENDING) {
                throw OnboardingException.invalidState(
                        "El mock todavía informa una revisión pendiente.");
            }
            return applyOutcome(findRequired(flowId), outcome);
        } catch (KycException e) {
            throw mappedKycError(e);
        }
    }

    public FlowResponse close(String flowId) {
        requireDemoEnabled();
        OnboardingFlow current = findRequired(flowId);
        if (current.closedAt() != null) {
            return response(current);
        }

        Instant now = Instant.now();
        String result = current.submittedAt() == null ? "INCOMPLETE" : "SUBMITTED";
        OnboardingFlow updated = new OnboardingFlow(
                current.flowId(), current.state(), current.startedAt(),
                current.submittedAt(), current.kycStartedAt(), current.kycCompletedAt(),
                current.activatedAt(), current.kycVerificationId(), result, now);

        boolean saved = repository.transition(
                updated, current.state(),
                List.of(event(current.flowId(), FlowEventType.FLOW_CLOSED,
                        null, result, now)));
        if (!saved) {
            throw OnboardingException.invalidState("El flujo cambió; consulta su estado.");
        }
        return response(updated);
    }

    public ReportResponse report() {
        requireDemoEnabled();
        List<FlowMetrics> rows = repository.findMetrics();

        List<Long> onboarding = rows.stream()
                .filter(row -> row.startedAt() != null && row.submittedAt() != null)
                .map(row -> Math.max(0L,
                        row.submittedAt().toEpochMilli() - row.startedAt().toEpochMilli()))
                .toList();

        List<Long> kyc = rows.stream()
                .filter(row -> row.kycStartedAt() != null && row.kycCompletedAt() != null)
                .map(row -> Math.max(0L,
                        row.kycCompletedAt().toEpochMilli() - row.kycStartedAt().toEpochMilli()))
                .toList();

        List<Long> activation = rows.stream()
                .filter(row -> row.submittedAt() != null && row.activatedAt() != null)
                .map(row -> Math.max(0L,
                        row.activatedAt().toEpochMilli() - row.submittedAt().toEpochMilli()))
                .toList();

        return new ReportResponse(
                onboarding.size(),
                median(onboarding),
                median(kyc),
                median(activation),
                PRODUCT_REFERENCE_MS,
                "Duración de onboarding = envío de pasos menos inicio; KYC y activación se reportan aparte. "
                        + "H2 es efímero; la referencia de 3 minutos no es un resultado validado.");
    }

    private FlowResponse refreshUnknown(OnboardingFlow current) {
        try {
            KycOutcome outcome = kycGateway.getVerification(current.kycVerificationId());
            return applyOutcome(findRequired(current.flowId().toString()), outcome);
        } catch (KycException e) {
            throw mappedKycError(e);
        }
    }

    private FlowResponse handleSubmissionFailure(String flowId, KycException failure) {
        OnboardingFlow current = findRequired(flowId);
        Instant now = Instant.now();

        if (failure.getPhase() == KycException.Phase.CREATE
                && failure.getHttpStatus() == 503) {
            OnboardingFlow retryable = new OnboardingFlow(
                    current.flowId(), FlowState.OTP_VERIFIED, current.startedAt(),
                    current.submittedAt(), null, null, null, null,
                    current.closeResult(), current.closedAt());
            repository.transition(
                    retryable, FlowState.SUBMITTING,
                    List.of(event(current.flowId(), FlowEventType.KYC_UNAVAILABLE,
                            "KYC_DATA", "RETRYABLE", now)));
            throw new OnboardingException(
                    503, "KYC_UNAVAILABLE",
                    "No se pudo completar la verificación. Puedes reintentar.",
                    true);
        }

        FlowState state = failure.getPhase() == KycException.Phase.CREATE
                && failure.getHttpStatus() == 400
                ? FlowState.OTP_VERIFIED
                : FlowState.SUBMISSION_UNKNOWN;

        OnboardingFlow updated = new OnboardingFlow(
                current.flowId(), state, current.startedAt(), current.submittedAt(),
                current.kycStartedAt(), current.kycCompletedAt(), current.activatedAt(),
                current.kycVerificationId(), current.closeResult(), current.closedAt());

        FlowEventType eventType = state == FlowState.SUBMISSION_UNKNOWN
                ? FlowEventType.SUBMISSION_UNKNOWN : FlowEventType.KYC_RESULT;
        repository.transition(
                updated, FlowState.SUBMITTING,
                List.of(event(current.flowId(), eventType, "KYC_DATA",
                        state.name(), now)));

        if (failure.getPhase() == KycException.Phase.CREATE
                && failure.getHttpStatus() == 400) {
            throw new OnboardingException(
                    502, "KYC_REQUEST_REJECTED",
                    "El proveedor no aceptó la solicitud de prueba.", false);
        }
        throw mappedKycError(failure);
    }

    private FlowResponse applyOutcome(OnboardingFlow current, KycOutcome outcome) {
        FlowState next = outcomeState(outcome);
        Instant now = Instant.now();
        Instant completedAt = next == FlowState.PENDING ? null : now;
        Instant activatedAt = next == FlowState.ACTIVE ? now : null;

        OnboardingFlow updated = new OnboardingFlow(
                current.flowId(), next, current.startedAt(), current.submittedAt(),
                current.kycStartedAt(), completedAt, activatedAt,
                current.kycVerificationId(), current.closeResult(), current.closedAt());

        boolean saved = repository.transition(
                updated,
                current.state(),
                List.of(
                        event(current.flowId(), FlowEventType.STEP_COMPLETED,
                                "KYC_DATA", "COMPLETED", now),
                        event(current.flowId(), FlowEventType.KYC_RESULT,
                                "RESULT", next.name(), now)));
        if (!saved) {
            throw OnboardingException.invalidState("El flujo cambió durante la respuesta KYC.");
        }
        return response(updated);
    }

    private static FlowState outcomeState(KycOutcome outcome) {
        String status = normalize(outcome.status());
        String wallet = normalize(outcome.walletStatus());

        if ("REJECTED".equals(status) || "REJECTED".equals(wallet)) {
            return FlowState.REJECTED;
        }
        if ("MANUAL_REVIEW".equals(status)
                || "PENDING".equals(status)
                || "PENDING".equals(wallet)) {
            return FlowState.PENDING;
        }
        if (("APPROVED".equals(status) || "ACTIVE".equals(status))
                && (wallet == null || "ACTIVE".equals(wallet))) {
            return FlowState.ACTIVE;
        }
        throw new OnboardingException(
                502, "KYC_INVALID_RESPONSE",
                "El proveedor devolvió un estado que no se pudo confirmar.", false);
    }

    private static OnboardingException mappedKycError(KycException failure) {
        if (failure.getHttpStatus() == 503) {
            return new OnboardingException(
                    503, "KYC_UNAVAILABLE",
                    "No se pudo completar la verificación. Puedes reintentar la consulta.",
                    true);
        }
        if (failure.getHttpStatus() == 409) {
            return new OnboardingException(
                    409, "KYC_CONFLICT",
                    "El proveedor no pudo aplicar la operación solicitada.", false);
        }
        if (failure.getHttpStatus() == 404) {
            return new OnboardingException(
                    502, "KYC_VERIFICATION_NOT_FOUND",
                    "No se pudo confirmar la verificación con el proveedor.", false);
        }
        return new OnboardingException(
                502, "KYC_PROVIDER_ERROR",
                "No se pudo confirmar la respuesta del proveedor KYC.", false);
    }

    private static void validateTestDocument(String documentType, String document) {
        if (!"TEST".equals(documentType)) {
            throw OnboardingException.validation(
                    "TEST_DOCUMENT_REQUIRED", "Usa el tipo de documento de prueba TEST.");
        }
        if (document == null || !document.startsWith("TEST-")
                || document.length() <= "TEST-".length()
                || document.length() > 128
                || !document.equals(document.trim())) {
            throw OnboardingException.validation(
                    "TEST_DOCUMENT_INVALID",
                    "Usa un documento ficticio con prefijo TEST- y un sufijo no vacío.");
        }
    }

    private OnboardingFlow findRequired(String flowId) {
        UUID id;
        try {
            id = UUID.fromString(flowId);
        } catch (RuntimeException e) {
            throw OnboardingException.badRequest("INVALID_FLOW_ID", "El identificador del flujo no es válido.");
        }
        OnboardingFlow flow = repository.findById(id);
        if (flow == null) {
            throw OnboardingException.notFound();
        }
        return flow;
    }

    private static void ensureOpen(OnboardingFlow flow) {
        if (flow.closedAt() != null) {
            throw OnboardingException.invalidState("El flujo ya está cerrado.");
        }
    }

    private void requireDemoEnabled() {
        if (!demoEnabled) {
            throw new OnboardingException(
                    403, "DEMO_DISABLED", "El onboarding de demo no está habilitado.", false);
        }
    }

    private static OnboardingEvent event(
            UUID id, FlowEventType type, String step, String result, Instant at) {
        return new OnboardingEvent(id, type, step, result, at);
    }

    private static String normalize(String value) {
        return value == null ? null : value.trim().toUpperCase(Locale.ROOT);
    }

    private static Long median(List<Long> values) {
        if (values.isEmpty()) {
            return null;
        }
        List<Long> sorted = values.stream().sorted(Comparator.naturalOrder())
                .collect(Collectors.toCollection(ArrayList::new));
        int middle = sorted.size() / 2;
        if (sorted.size() % 2 == 1) {
            return sorted.get(middle);
        }
        return Math.round((sorted.get(middle - 1) + sorted.get(middle)) / 2.0);
    }

    private static FlowResponse response(OnboardingFlow flow) {
        String currentStep = switch (flow.state()) {
            case STARTED -> "PHONE_OTP";
            case OTP_VERIFIED -> "KYC_DATA";
            case SUBMITTING, PENDING, ACTIVE, REJECTED, SUBMISSION_UNKNOWN -> "RESULT";
        };

        String kycStatus = switch (flow.state()) {
            case PENDING -> "MANUAL_REVIEW";
            case ACTIVE -> "APPROVED";
            case REJECTED -> "REJECTED";
            default -> null;
        };
        String walletStatus = switch (flow.state()) {
            case PENDING -> "PENDING";
            case ACTIVE -> "ACTIVE";
            case REJECTED -> "REJECTED";
            default -> null;
        };
        boolean retryable = flow.state() == FlowState.OTP_VERIFIED;
        String message = switch (flow.state()) {
            case STARTED -> "Ingresa el código de prueba para continuar.";
            case OTP_VERIFIED -> "Verificación local completada. Ingresa los datos ficticios TEST.";
            case SUBMITTING -> "La verificación está en proceso.";
            case PENDING -> "La revisión de demo sigue pendiente.";
            case ACTIVE -> "Verificación aprobada; la wallet está activa.";
            case REJECTED -> "La verificación fue rechazada; la wallet no está activa.";
            case SUBMISSION_UNKNOWN -> "No se pudo confirmar el resultado. No se repetirá la creación automáticamente.";
        };

        return new FlowResponse(
                flow.flowId().toString(),
                flow.state().name(),
                currentStep,
                REQUIRED_STEPS,
                kycStatus,
                walletStatus,
                flow.state() == FlowState.ACTIVE,
                retryable,
                flow.submittedAt(),
                flow.closeResult(),
                message);
    }
}
```

```java
// OnboardingResource.java
package resource;

import dto.DecisionRequest;
import dto.FlowResponse;
import dto.OtpRequest;
import dto.ReportResponse;
import dto.SubmitRequest;
import jakarta.enterprise.context.ApplicationScoped;
import jakarta.ws.rs.Consumes;
import jakarta.ws.rs.GET;
import jakarta.ws.rs.POST;
import jakarta.ws.rs.Path;
import jakarta.ws.rs.PathParam;
import jakarta.ws.rs.Produces;
import jakarta.ws.rs.core.MediaType;
import jakarta.ws.rs.core.Response;
import service.OnboardingService;

@Path("/api/onboarding")
@ApplicationScoped
@Consumes(MediaType.APPLICATION_JSON)
@Produces(MediaType.APPLICATION_JSON)
public class OnboardingResource {
    private final OnboardingService service;

    public OnboardingResource(OnboardingService service) {
        this.service = service;
    }

    @POST
    @Path("/flows")
    public Response start() {
        FlowResponse response = service.start();
        return Response.status(Response.Status.CREATED).entity(response).build();
    }

    @POST
    @Path("/flows/{flowId}/otp")
    public FlowResponse verifyOtp(
            @PathParam("flowId") String flowId,
            OtpRequest request) {
        return service.verifyOtp(flowId, request == null ? null : request.code());
    }

    @POST
    @Path("/flows/{flowId}/submit")
    public FlowResponse submit(
            @PathParam("flowId") String flowId,
            SubmitRequest request) {
        if (request == null) {
            throw service.OnboardingException.validation(
                    "REQUEST_REQUIRED", "Se requiere el cuerpo de la solicitud.");
        }
        return service.submit(flowId, request.documentType(), request.document());
    }

    @GET
    @Path("/flows/{flowId}")
    public FlowResponse get(@PathParam("flowId") String flowId) {
        return service.get(flowId);
    }

    @POST
    @Path("/flows/{flowId}/decision")
    public FlowResponse decide(
            @PathParam("flowId") String flowId,
            DecisionRequest request) {
        return service.decide(flowId, request == null ? null : request.decision());
    }

    @POST
    @Path("/flows/{flowId}/close")
    public FlowResponse close(@PathParam("flowId") String flowId) {
        return service.close(flowId);
    }

    @GET
    @Path("/report")
    public ReportResponse report() {
        return service.report();
    }
}
```

```java
// OnboardingExceptionMapper.java
package resource;

import dto.ErrorResponse;
import jakarta.ws.rs.core.Response;
import jakarta.ws.rs.ext.ExceptionMapper;
import jakarta.ws.rs.ext.Provider;
import service.OnboardingException;

@Provider
public class OnboardingExceptionMapper implements ExceptionMapper<OnboardingException> {
    @Override
    public Response toResponse(OnboardingException exception) {
        ErrorResponse body = new ErrorResponse(
                exception.getCode(),
                exception.getMessage(),
                exception.isRetryable());
        return Response.status(exception.getHttpStatus()).entity(body).build();
    }
}
```