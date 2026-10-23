```markdown
// frontend_spec.md

# HU-01 — Onboarding guiado de wallet para el MVP

## Alcance

Interfaz Angular 17 para una demo con tres etapas: celular/OTP de prueba, datos KYC ficticios y resultado. El backend valida el OTP, integra el mock KYC y determina el estado de la wallet. La interfaz nunca activa una wallet por inferencia.

No se solicitan celulares reales, no se envían SMS y no se procesan pagos. No se incluyen KYC productivo, MAU ni CAC.

## Diseño visual y responsive

- **Mobile-first:** fondo gris azulado suave, contenido en una columna y controles de ancho completo. En pantallas pequeñas se priorizan instrucciones, formulario y acción principal.
- **Tablet:** el contenido se centra; el indicador de tres pasos se distribuye horizontalmente cuando hay espacio.
- **Escritorio:** contexto y aviso de demo en una columna lateral; recorrido en una tarjeta principal.
- **Anchos de contenido:** tarjetas fluidas con `min-width: 0`, `max-width` y texto adaptable; sin anchos fijos que fuerzen scroll horizontal.
- **Tipografía:** familia de sistema, texto base de 16 px para facilitar lectura y evitar zoom automático en móviles.
- **Jerarquía:** título de la demo, secuencia y paso actual, estado de la etapa, campos con ayuda persistente, errores accionables y acción principal.
- **Colores:** fondo `#F3F6FA`, texto `#182538`, texto secundario `#475569`, tarjeta blanca, acción `#075E54`, foco `#005FCC`, error `#B42318` y aviso `#8A4B00`. El estado se acompaña siempre con texto; no depende solo del color.
- **Espaciado:** escala basada en múltiplos de 4 px; tarjetas y campos con separación amplia para uso táctil.
- **Puntos de quiebre:** hasta 47.99 rem, móvil; desde 48 rem, tablet; desde 64 rem, escritorio.

Las reglas usan contenido flexible, `overflow-wrap` y campos de 100% de ancho. La hoja de estilos contempla 320, 768 y 1280 px y zoom al 200%; la revisión visual en navegador queda pendiente.

## Recorrido y contrato frontend

1. **Celular de prueba y OTP:** el usuario ingresa un código de seis dígitos. La ayuda aclara que no se solicita un número real ni se envía SMS. Código de demo: `123456`. El backend es la autoridad para aceptarlo.
2. **Datos KYC ficticios:** `documentType` se fija en `TEST`; el único documento de prueba editable debe comenzar con `TEST-` y tener contenido después del prefijo. Ejemplo ficticio: `TEST-DEMO-001`. No se infiere ni solicita información KYC adicional.
3. **Resultado:** se representa el estado devuelto por el backend. Solo `ACTIVE` habilita el mensaje de wallet activa; esta feature no habilita pagos.

La secuencia permanece visible. No se avanza si un formulario está inválido, pendiente o en envío. Los intentos inválidos marcan controles como tocados, enfocan el primero inválido y no llaman a la API.

## Campos, ayudas y validaciones

| Etapa | Campo | Requerido | Validación frontend | Ayuda persistente |
|---|---|---:|---|---|
| OTP | Código de demo | Sí | `Validators.required`; exactamente seis dígitos. El backend comprueba que sea `123456`. | “Código de demostración: 123456. No se envía SMS ni se requiere un celular real.” |
| KYC | Tipo de documento | Sí, valor fijo | Control de formulario con `Validators.required`; solo lectura, valor `TEST`. | “Tipo fijado por esta demo; no es una categoría de documento real.” |
| KYC | Documento de prueba | Sí | `Validators.required`, rechazo de solo espacios y prefijo exacto `TEST-` con sufijo no vacío. | “Usa un identificador ficticio, por ejemplo TEST-DEMO-001. No uses datos personales.” |

No se inventan límites de longitud para el documento, ni se transforma el campo en un documento real. El documento se valida localmente antes de la solicitud y el backend vuelve a validarlo.

## Mensajes y estados

- **Carga:** indica qué operación se está realizando y bloquea acciones duplicadas.
- **Vacío/inicio:** explica la demo y ofrece iniciar el flujo.
- **Error OTP:** “El código no coincide. Revisa el código de demostración e inténtalo de nuevo.”
- **Documento inválido:** explica que debe empezar con `TEST-` y contener un sufijo ficticio.
- **`KYC_UNAVAILABLE`/503:** informa que la verificación no se completó; mantiene wallet inactiva y permite reintentar.
- **`SUBMISSION_UNKNOWN`:** informa que no se pudo confirmar el envío; ofrece consultar el estado. No repite automáticamente la creación KYC.
- **`PENDING`:** explica que sigue pendiente y que la wallet no está activa. Ofrece las decisiones de demo `ACTIVE` o `REJECTED` desde la misma vista.
- **`REJECTED`:** comunica el rechazo y que la wallet no está activa.
- **`ACTIVE`:** comunica que el backend confirmó la activación. Aclara que pagos no están habilitados en esta feature.
- **Error de cierre:** no se oculta; permite salir sin afirmar que el cierre quedó confirmado.

Los mensajes de aplicación no muestran cuerpos técnicos, documentos, OTP ni valores personales.

## Accesibilidad

- Formularios Reactive Forms; cada control tiene `label` asociado, indicación textual de requerido, ayuda persistente y errores asociados mediante `aria-describedby`.
- `aria-invalid` refleja errores visibles. Errores de envío se anuncian con `role="alert"`; cambios de estado y carga usan regiones `aria-live`.
- El primer control inválido recibe foco al intentar avanzar.
- Acciones operables por teclado, foco visible de alto contraste, estados expresados en texto y botones con nombres comprensibles.
- No se usa placeholder como etiqueta o única instrucción.

## Integración API

El servicio frontend usa las rutas descritas por `backend_spec.md`:

- `POST /api/onboarding/flows`, cuerpo `{}`.
- `POST /api/onboarding/flows/{flowId}/otp`, cuerpo `{ "code": "123456" }`.
- `POST /api/onboarding/flows/{flowId}/submit`, cuerpo `{ "documentType": "TEST", "document": "TEST-DEMO-001" }`.
- `GET /api/onboarding/flows/{flowId}`.
- `POST /api/onboarding/flows/{flowId}/decision`, cuerpo con `ACTIVE` o `REJECTED`.
- `POST /api/onboarding/flows/{flowId}/close`, cuerpo `{}`.
- `GET /api/onboarding/report`.

El frontend solo consume la API propia. No llama directamente al mock KYC. Las respuestas de estado usan `state` y `walletActive` como describe el backend.

**Pendiente de confirmación de contrato:** `backend_spec.md` no fija los nombres de propiedades de la respuesta de `/report`; el código espera `medianOnboardingDurationMs`, `sampleSize`, `medianKycDurationMs` y `medianActivationDurationMs`. Confirmar y ajustar ese DTO antes de integrar.

## Analítica y duración

El frontend no emite eventos analíticos duplicados. El inicio se registra al crear el flujo; el backend registra pasos completados, envío y cierre con ID aleatorio y timestamps UTC. No se envían OTP, celular ni documento a los eventos.

- Duración del onboarding: inicio hasta envío exitoso de los pasos, excluyendo KYC y activación.
- KYC y activación se informan por separado si el reporte los proporciona.
- El reporte presenta la mediana y tamaño de muestra observados, o un estado vacío si no hay envíos. **3 minutos** se presenta solo como referencia de producto.
- El cierre por acción explícita usa el endpoint de cierre. El cierre por `pagehide` intenta enviar un beacon de mejor esfuerzo; no se puede garantizar si el navegador o la conectividad terminan abruptamente.

**Pendiente:** confirmar la frontera temporal y el comportamiento idempotente del endpoint de cierre con backend. La entrega no afirma métricas obtenidas.

## Dependencias pendientes de producto y cumplimiento

- Confirmar autorización, sesión y protección de la demo; no se presupone un rol ni proveedor de identidad.
- Confirmar el contrato JSON exacto de respuestas de flujo, decisiones, errores y reporte.
- Confirmar que el OTP fijo y el mock permanezcan restringidos a demo y desactivados en perfiles productivos.
- Confirmar la política para abandonar flujos y la retención de H2 efímero.
- No se implementan pagos, límites de proveedores de pago, idempotencia de operaciones financieras ni cancelación P2P: están fuera de HU-01.
- No se incorporan documentos reales ni requisitos KYC adicionales.

## Relación con metas de negocio

Los objetivos proporcionados —onboarding de 8 a 3 minutos, abandono de checkout de 30% a 8%, MAU de 1.000 a 2.000 y CAC de PEN 10 en meses 1 a 3— son objetivos de negocio, no resultados garantizados por esta interfaz. Checkout, MAU y CAC quedan fuera de la demo y de su reporte.

## Comprobación y evidencia

### Pruebas incluidas

`onboarding.component.spec.ts` cubre formulario vacío, espacios, formatos inválidos, datos válidos, bloqueo de solicitudes inválidas, errores del servidor, reintento y prevención de envío duplicado. Incluye comprobación de asociación accesible de ayuda y error.

### Estado de ejecución

**No ejecutado:** no se dispuso de repositorio ni entorno de ejecución en esta entrega. No se afirma que las pruebas, build o integración hayan pasado.

### Comandos sugeridos

Desde el proyecto Angular, con Angular 17 y runner Jasmine/Karma configurados:

```bash
npm test -- --watch=false
npm run build
```

### Revisión manual pendiente

En navegador, probar anchos de 320, 768 y 1280 px, además de zoom al 200%, en inicio, formularios, ayuda persistente, errores, carga y resultado. Verificar ausencia de scroll horizontal, texto o acciones recortados, foco por teclado, lector de pantalla y que un envío inválido no genere llamadas API.
```

```typescript
// onboarding-api.service.ts
import { inject, Injectable, InjectionToken } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

export const ONBOARDING_API_BASE_URL = new InjectionToken<string>(
  'ONBOARDING_API_BASE_URL',
  {
    providedIn: 'root',
    factory: () => '/api/onboarding'
  }
);

export interface OnboardingFlow {
  flowId: string;
  state: string;
  currentStep?: 'PHONE_OTP' | 'KYC_DATA' | 'RESULT';
  walletActive?: boolean;
}

export interface OnboardingReport {
  // Confirmar estos nombres con el DTO definitivo de GET /report.
  medianOnboardingDurationMs?: number | null;
  medianKycDurationMs?: number | null;
  medianActivationDurationMs?: number | null;
  sampleSize?: number;
}

@Injectable({ providedIn: 'root' })
export class OnboardingApiService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = inject(ONBOARDING_API_BASE_URL);

  startFlow(): Observable<OnboardingFlow> {
    return this.http.post<OnboardingFlow>(`${this.baseUrl}/flows`, {});
  }

  verifyOtp(flowId: string, code: string): Observable<OnboardingFlow> {
    return this.http.post<OnboardingFlow>(
      `${this.flowUrl(flowId)}/otp`,
      { code }
    );
  }

  submitKyc(
    flowId: string,
    documentType: 'TEST',
    document: string
  ): Observable<OnboardingFlow> {
    return this.http.post<OnboardingFlow>(
      `${this.flowUrl(flowId)}/submit`,
      { documentType, document }
    );
  }

  getFlow(flowId: string): Observable<OnboardingFlow> {
    return this.http.get<OnboardingFlow>(this.flowUrl(flowId));
  }

  resolveDecision(
    flowId: string,
    decision: 'ACTIVE' | 'REJECTED'
  ): Observable<OnboardingFlow> {
    return this.http.post<OnboardingFlow>(
      `${this.flowUrl(flowId)}/decision`,
      { decision }
    );
  }

  closeFlow(flowId: string): Observable<unknown> {
    return this.http.post(`${this.flowUrl(flowId)}/close`, {});
  }

  getReport(): Observable<OnboardingReport> {
    return this.http.get<OnboardingReport>(`${this.baseUrl}/report`);
  }

  /**
   * Mejor esfuerzo para cerrar una pestaña. El backend debe aceptar el mismo
   * cuerpo vacío usado por closeFlow. No sustituye el cierre confirmado.
   */
  closeWithBeacon(flowId: string): boolean {
    if (typeof navigator === 'undefined' || !navigator.sendBeacon) {
      return false;
    }

    const body = new Blob(['{}'], { type: 'application/json' });
    return navigator.sendBeacon(
      `${this.flowUrl(flowId)}/close`,
      body
    );
  }

  private flowUrl(flowId: string): string {
    return `${this.baseUrl}/flows/${encodeURIComponent(flowId)}`;
  }
}
```

```typescript
// onboarding.component.ts
import {
  Component,
  ElementRef,
  HostListener,
  ViewChild
} from '@angular/core';
import {
  AbstractControl,
  FormControl,
  FormGroup,
  ReactiveFormsModule,
  ValidationErrors,
  Validators
} from '@angular/forms';
import { CommonModule } from '@angular/common';
import { HttpErrorResponse } from '@angular/common/http';
import { OnboardingApiService, OnboardingFlow, OnboardingReport } from './onboarding-api.service';

type Stage = 'intro' | 'otp' | 'kyc' | 'result' | 'finished';
type ResultState =
  | 'ACTIVE'
  | 'PENDING'
  | 'REJECTED'
  | 'SUBMISSION_UNKNOWN'
  | 'CHECKING'
  | null;

type ReportState = 'idle' | 'loading' | 'available' | 'empty' | 'error';

@Component({
  selector: 'app-onboarding',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  templateUrl: './onboarding.component.html',
  styleUrl: './onboarding.component.scss'
})
export class OnboardingComponent {
  @ViewChild('otpInput') otpInput?: ElementRef<HTMLInputElement>;
  @ViewChild('documentInput') documentInput?: ElementRef<HTMLInputElement>;

  readonly otpForm = new FormGroup({
    code: new FormControl('', {
      nonNullable: true,
      validators: [Validators.required, Validators.pattern(/^\d{6}$/)]
    })
  });

  readonly kycForm = new FormGroup({
    documentType: new FormControl('TEST', {
      nonNullable: true,
      validators: [Validators.required]
    }),
    document: new FormControl('', {
      nonNullable: true,
      validators: [
        Validators.required,
        rejectWhitespaceOnly,
        testDocumentValidator
      ]
    })
  });

  stage: Stage = 'intro';
  flowId: string | null = null;
  flowState = '';
  resultState: ResultState = null;
  walletActive = false;

  requestInProgress = false;
  globalError = '';
  otpApiError = '';
  documentApiError = '';
  closeError = '';
  closeAttempted = false;

  reportState: ReportState = 'idle';
  report: OnboardingReport | null = null;

  otpAttempted = false;
  kycAttempted = false;
  finishedMessage = '';

  constructor(private readonly api: OnboardingApiService) {}

  get currentStep(): number {
    if (this.stage === 'kyc') return 2;
    if (this.stage === 'result' || this.stage === 'finished') return 3;
    return 1;
  }

  get otpControl(): FormControl<string> {
    return this.otpForm.controls.code;
  }

  get documentControl(): FormControl<string> {
    return this.kycForm.controls.document;
  }

  get documentTypeControl(): FormControl<string> {
    return this.kycForm.controls.documentType;
  }

  get showOtpError(): boolean {
    return (this.otpControl.touched || this.otpAttempted) &&
      this.otpControl.invalid;
  }

  get otpErrorText(): string {
    if (this.otpApiError) return this.otpApiError;
    if (this.otpControl.hasError('required')) {
      return 'Ingresa el código de demostración.';
    }
    if (this.otpControl.hasError('pattern')) {
      return 'El código debe tener exactamente seis dígitos.';
    }
    return 'Revisa el código e inténtalo de nuevo.';
  }

  get showDocumentError(): boolean {
    return (this.documentControl.touched || this.kycAttempted) &&
      this.documentControl.invalid;
  }

  get documentErrorText(): string {
    if (this.documentApiError) return this.documentApiError;
    if (this.documentControl.hasError('required')) {
      return 'Ingresa un identificador ficticio de prueba.';
    }
    if (this.documentControl.hasError('whitespaceOnly')) {
      return 'El dato no puede contener solo espacios. Ingresa un identificador de prueba.';
    }
    if (this.documentControl.hasError('testDocument')) {
      return 'Debe comenzar exactamente con TEST- y tener un valor ficticio después del guion.';
    }
    return 'Revisa el identificador ficticio.';
  }

  startFlow(): void {
    if (this.requestInProgress || this.flowId) return;

    this.resetMessages();
    this.requestInProgress = true;

    this.api.startFlow().subscribe({
      next: flow => {
        this.flowId = flow.flowId;
        this.flowState = flow.state;
        this.stage = 'otp';
        this.requestInProgress = false;
      },
      error: error => {
        this.globalError = this.messageForError(error, 'No pudimos iniciar el recorrido. Inténtalo nuevamente.');
        this.requestInProgress = false;
      }
    });
  }

  verifyOtp(): void {
    this.otpAttempted = true;
    this.otpForm.markAllAsTouched();
    this.otpApiError = '';

    if (this.otpForm.invalid || this.otpForm.pending) {
      this.focusFirstInvalid('otp');
      return;
    }
    if (!this.flowId || this.requestInProgress) return;

    this.resetMessages();
    this.requestInProgress = true;

    this.api.verifyOtp(this.flowId, this.otpControl.value).subscribe({
      next: flow => {
        this.flowState = flow.state;
        this.stage = 'kyc';
        this.requestInProgress = false;
      },
      error: error => {
        const code = this.errorCode(error);
        if (code === 'OTP_INVALID') {
          this.otpApiError = 'El código no coincide. Revisa el código de demostración e inténtalo de nuevo.';
          this.otpControl.setErrors({
            ...(this.otpControl.errors ?? {}),
            server: true
          });
        } else {
          this.globalError = this.messageForError(error, 'No pudimos validar el código. Inténtalo nuevamente.');
        }
        this.requestInProgress = false;
      }
    });
  }

  clearOtpServerError(): void {
    this.otpApiError = '';
    const errors = this.otpControl.errors;
    if (!errors?.['server']) return;

    const { server: _server, ...remaining } = errors;
    this.otpControl.setErrors(Object.keys(remaining).length ? remaining : null);
  }

  submitKyc(): void {
    this.kycAttempted = true;
    this.kycForm.markAllAsTouched();
    this.documentApiError = '';

    if (this.kycForm.invalid || this.kycForm.pending) {
      this.focusFirstInvalid('kyc');
      return;
    }
    if (!this.flowId || this.requestInProgress) return;

    this.resetMessages();
    this.requestInProgress = true;
    const document = this.documentControl.value.trim();

    this.api.submitKyc(this.flowId, 'TEST', document).subscribe({
      next: flow => {
        this.requestInProgress = false;
        this.applyFlowResult(flow);
      },
      error: error => {
        const code = this.errorCode(error);
        this.requestInProgress = false;

        if (code === 'TEST_DOCUMENT_REQUIRED' || code === 'TEST_DOCUMENT_INVALID') {
          this.documentApiError = code === 'TEST_DOCUMENT_REQUIRED'
            ? 'Ingresa un identificador ficticio de prueba.'
            : 'El identificador debe comenzar con TEST- y tener un valor ficticio después del guion.';
          this.documentControl.setErrors({
            ...(this.documentControl.errors ?? {}),
            server: true
          });
        } else if (code === 'KYC_UNAVAILABLE' || this.statusCode(error) === 503) {
          this.stage = 'kyc';
          this.globalError = 'No pudimos completar la verificación de demo. Tu wallet no está activa. Puedes reintentar.';
        } else if (code === 'SUBMISSION_UNKNOWN') {
          this.stage = 'result';
          this.resultState = 'SUBMISSION_UNKNOWN';
          this.walletActive = false;
          this.flowState = 'SUBMISSION_UNKNOWN';
        } else {
          this.globalError = this.messageForError(error, 'No pudimos enviar los datos de prueba. Revisa el dato e inténtalo nuevamente.');
        }
      }
    });
  }

  resolveDecision(decision: 'ACTIVE' | 'REJECTED'): void {
    if (!this.flowId || this.requestInProgress || this.resultState !== 'PENDING') return;

    this.resetMessages();
    this.requestInProgress = true;
    this.api.resolveDecision(this.flowId, decision).subscribe({
      next: flow => {
        this.requestInProgress = false;
        this.applyFlowResult(flow);
      },
      error: error => {
        this.globalError = this.messageForError(error, 'No pudimos confirmar la decisión de demo. El estado sigue sin cambiar.');
        this.requestInProgress = false;
      }
    });
  }

  refreshStatus(): void {
    if (!this.flowId || this.requestInProgress) return;

    this.resetMessages();
    this.requestInProgress = true;
    this.api.getFlow(this.flowId).subscribe({
      next: flow => {
        this.requestInProgress = false;
        this.applyFlowResult(flow);
      },
      error: error => {
        this.globalError = this.messageForError(error, 'No pudimos consultar el estado. Inténtalo nuevamente.');
        this.requestInProgress = false;
      }
    });
  }

  finishFlow(): void {
    if (!this.flowId || this.requestInProgress || this.closeAttempted) return;

    this.closeAttempted = true;
    this.closeError = '';
    this.requestInProgress = true;
    this.api.closeFlow(this.flowId).subscribe({
      next: () => {
        this.requestInProgress = false;
        this.stage = 'finished';
        this.finishedMessage = 'El cierre del recorrido fue confirmado.';
      },
      error: () => {
        this.requestInProgress = false;
        this.closeError = 'No pudimos confirmar el cierre. Puedes salir, pero no afirmaremos que quedó registrado.';
      }
    });
  }

  leaveWithoutConfirmedClose(): void {
    this.stage = 'finished';
    this.finishedMessage = 'Saliste sin confirmación del cierre del recorrido.';
  }

  @HostListener('window:pagehide')
  onPageHide(): void {
    if (this.flowId && !this.closeAttempted && this.stage !== 'finished') {
      this.closeAttempted = true;
      this.api.closeWithBeacon(this.flowId);
    }
  }

  stepStatus(step: number): 'current' | 'complete' | 'upcoming' {
    if (step < this.currentStep) return 'complete';
    if (step === this.currentStep) return 'current';
    return 'upcoming';
  }

  formatDuration(milliseconds?: number | null): string {
    if (milliseconds == null || !Number.isFinite(milliseconds) || milliseconds < 0) {
      return 'No disponible';
    }
    const totalSeconds = Math.round(milliseconds / 1000);
    const minutes = Math.floor(totalSeconds / 60);
    const seconds = totalSeconds % 60;
    return minutes > 0 ? `${minutes} min ${seconds} s` : `${seconds} s`;
  }

  private applyFlowResult(flow: OnboardingFlow): void {
    this.flowState = flow.state;
    this.stage = 'result';

    switch (flow.state) {
      case 'ACTIVE':
        this.resultState = 'ACTIVE';
        this.walletActive = flow.walletActive === true || flow.state === 'ACTIVE';
        break;
      case 'PENDING':
        this.resultState = 'PENDING';
        this.walletActive = false;
        break;
      case 'REJECTED':
        this.resultState = 'REJECTED';
        this.walletActive = false;
        break;
      case 'SUBMISSION_UNKNOWN':
        this.resultState = 'SUBMISSION_UNKNOWN';
        this.walletActive = false;
        break;
      default:
        this.resultState = 'CHECKING';
        this.walletActive = false;
        break;
    }

    this.loadReport();
  }

  private loadReport(): void {
    this.reportState = 'loading';
    this.report = null;
    this.api.getReport().subscribe({
      next: report => {
        this.report = report;
        this.reportState = (report.sampleSize ?? 0) > 0 ? 'available' : 'empty';
      },
      error: () => {
        this.reportState = 'error';
      }
    });
  }

  private focusFirstInvalid(form: 'otp' | 'kyc'): void {
    setTimeout(() => {
      if (form === 'otp') {
        this.otpInput?.nativeElement.focus();
      } else {
        this.documentInput?.nativeElement.focus();
      }
    });
  }

  private resetMessages(): void {
    this.globalError = '';
    this.closeError = '';
  }

  private errorCode(error: unknown): string {
    if (!(error instanceof HttpErrorResponse)) return '';
    const body = error.error as { code?: string; error?: string } | null;
    return body?.code ?? body?.error ?? '';
  }

  private statusCode(error: unknown): number {
    return error instanceof HttpErrorResponse ? error.status : 0;
  }

  private messageForError(error: unknown, fallback: string): string {
    const code = this.errorCode(error);
    const safeMessages: Record<string, string> = {
      INVALID_STATE: 'No se puede avanzar desde este estado. Consulta el estado del recorrido.',
      OTP_INVALID: 'El código no coincide. Revisa el código de demostración.',
      TEST_DOCUMENT_REQUIRED: 'Ingresa un identificador ficticio de prueba.',
      TEST_DOCUMENT_INVALID: 'El identificador debe comenzar con TEST- y tener contenido ficticio después del guion.',
      KYC_UNAVAILABLE: 'La verificación de demo no está disponible por ahora. Tu wallet no está activa.'
    };
    return safeMessages[code] ?? fallback;
  }
}

function rejectWhitespaceOnly(control: AbstractControl): ValidationErrors | null {
  const value = control.value;
  if (typeof value !== 'string' || value.length === 0) return null;
  return value.trim().length === 0 ? { whitespaceOnly: true } : null;
}

function testDocumentValidator(control: AbstractControl): ValidationErrors | null {
  const value = control.value;
  if (typeof value !== 'string' || value.trim().length === 0) return null;

  const normalized = value.trim();
  return normalized.startsWith('TEST-') && normalized.length > 'TEST-'.length
    ? null
    : { testDocument: true };
}
```

```html
// onboarding.component.html
<div class="page-shell">
  <header class="site-header">
    <p class="brand">Wallet <span aria-hidden="true">·</span> demo Perú</p>
    <p class="demo-tag">Recorrido de prueba</p>
  </header>

  <div class="onboarding-layout">
    <aside class="intro-panel" aria-labelledby="page-title">
      <p class="eyebrow">Registro guiado</p>
      <h1 id="page-title">Prepara tu wallet de demo</h1>
      <p>
        Completa los pasos con datos ficticios y consulta el resultado del
        verificador simulado.
      </p>

      <section class="privacy-note" aria-label="Importante sobre esta demo">
        <h2>Solo datos de prueba</h2>
        <p>
          No ingreses información personal. Esta demo no envía SMS, no realiza
          pagos y no representa una verificación KYC productiva.
        </p>
      </section>
    </aside>

    <main class="flow-card" aria-labelledby="flow-title">
      <div class="card-heading">
        <div>
          <p class="eyebrow">Onboarding</p>
          <h2 id="flow-title">Tu recorrido</h2>
        </div>
        <span class="step-count">Paso {{ currentStep }} de 3</span>
      </div>

      <nav class="progress-nav" aria-label="Pasos del onboarding">
        <ol class="progress-list">
          <li [class.complete]="stepStatus(1) === 'complete'"
              [class.current]="stepStatus(1) === 'current'">
            <span class="step-number" aria-hidden="true">1</span>
            <span class="step-label"
              [attr.aria-current]="stepStatus(1) === 'current' ? 'step' : null">
              Celular y código
            </span>
          </li>
          <li [class.complete]="stepStatus(2) === 'complete'"
              [class.current]="stepStatus(2) === 'current'">
            <span class="step-number" aria-hidden="true">2</span>
            <span class="step-label"
              [attr.aria-current]="stepStatus(2) === 'current' ? 'step' : null">
              Datos de prueba
            </span>
          </li>
          <li [class.complete]="stepStatus(3) === 'complete'"
              [class.current]="stepStatus(3) === 'current'">
            <span class="step-number" aria-hidden="true">3</span>
            <span class="step-label"
              [attr.aria-current]="stepStatus(3) === 'current' ? 'step' : null">
              Resultado
            </span>
          </li>
        </ol>
      </nav>

      <div *ngIf="globalError" class="message message-error" role="alert">
        {{ globalError }}
      </div>

      <section *ngIf="stage === 'intro'" class="step-content" aria-labelledby="intro-title">
        <h3 id="intro-title">Comienza cuando estés listo</h3>
        <p>
          Usarás un código fijo de demostración y un identificador KYC ficticio.
          Puedes salir antes de enviar los datos.
        </p>
        <button class="button button-primary"
                type="button"
                [disabled]="requestInProgress"
                (click)="startFlow()">
          <span *ngIf="requestInProgress" class="spinner" aria-hidden="true"></span>
          {{ requestInProgress ? 'Iniciando…' : 'Comenzar onboarding' }}
        </button>
      </section>

      <section *ngIf="stage === 'otp'" class="step-content" aria-labelledby="otp-title">
        <h3 id="otp-title">Celular de prueba y código</h3>
        <p>
          No ingreses un número de celular real. Esta demo no solicita ni envía
          SMS; valida el código localmente en el backend.
        </p>

        <form [formGroup]="otpForm" (ngSubmit)="verifyOtp()" novalidate>
          <div class="field">
            <label for="demo-code">
              Código de demostración <span class="required-mark" aria-hidden="true">*</span>
              <span class="visually-hidden"> obligatorio</span>
            </label>
            <p id="otp-help" class="field-help">
              Usa el código fijo <strong>123456</strong>. No se envía SMS.
            </p>
            <input #otpInput
                   id="demo-code"
                   type="text"
                   inputmode="numeric"
                   autocomplete="one-time-code"
                   formControlName="code"
                   maxlength="6"
                   aria-required="true"
                   [attr.aria-invalid]="showOtpError ? 'true' : 'false'"
                   [attr.aria-describedby]="showOtpError ? 'otp-help otp-error' : 'otp-help'"
                   (input)="clearOtpServerError()">
            <p *ngIf="showOtpError" id="otp-error" class="field-error" role="alert">
              {{ otpErrorText }}
            </p>
          </div>

          <button class="button button-primary"
                  type="submit"
                  [disabled]="requestInProgress">
            <span *ngIf="requestInProgress" class="spinner" aria-hidden="true"></span>
            {{ requestInProgress ? 'Validando…' : 'Continuar' }}
          </button>
        </form>
      </section>

      <section *ngIf="stage === 'kyc'" class="step-content" aria-labelledby="kyc-title">
        <h3 id="kyc-title">Datos KYC ficticios</h3>
        <p>
          Esta etapa usa exclusivamente datos de prueba. No se solicitan
          documentos reales ni información personal.
        </p>

        <form [formGroup]="kycForm" (ngSubmit)="submitKyc()" novalidate>
          <div class="field">
            <label for="document-type">
              Tipo de documento <span class="required-mark" aria-hidden="true">*</span>
              <span class="visually-hidden"> obligatorio</span>
            </label>
            <p id="document-type-help" class="field-help">
              Valor fijo requerido por el contrato de demo; no es un tipo de
              documento real.
            </p>
            <input id="document-type"
                   type="text"
                   formControlName="documentType"
                   readonly
                   aria-required="true"
                   aria-describedby="document-type-help">
          </div>

          <div class="field">
            <label for="test-document">
              Identificador de prueba <span class="required-mark" aria-hidden="true">*</span>
              <span class="visually-hidden"> obligatorio</span>
            </label>
            <p id="document-help" class="field-help">
              Usa un valor ficticio que empiece con <strong>TEST-</strong>,
              por ejemplo <strong>TEST-DEMO-001</strong>. No uses datos personales.
            </p>
            <input #documentInput
                   id="test-document"
                   type="text"
                   formControlName="document"
                   autocomplete="off"
                   autocapitalize="characters"
                   spellcheck="false"
                   aria-required="true"
                   [attr.aria-invalid]="showDocumentError ? 'true' : 'false'"
                   [attr.aria-describedby]="showDocumentError ? 'document-help document-error' : 'document-help'">
            <p *ngIf="showDocumentError"
               id="document-error"
               class="field-error"
               role="alert">
              {{ documentErrorText }}
            </p>
          </div>

          <button class="button button-primary"
                  type="submit"
                  [disabled]="requestInProgress">
            <span *ngIf="requestInProgress" class="spinner" aria-hidden="true"></span>
            {{ requestInProgress ? 'Enviando a verificación…' : 'Enviar datos de prueba' }}
          </button>
        </form>
      </section>

      <section *ngIf="stage === 'result'" class="step-content result-content"
               aria-labelledby="result-title" aria-live="polite">
        <h3 id="result-title">Resultado del recorrido</h3>

        <div *ngIf="resultState === 'ACTIVE'" class="status-card status-success">
          <h4>Wallet activa confirmada</h4>
          <p>
            El backend confirmó el estado activo. Esta demo no habilita pagos.
          </p>
        </div>

        <div *ngIf="resultState === 'PENDING'" class="status-card status-pending">
          <h4>Verificación pendiente</h4>
          <p>
            La revisión continúa pendiente. La wallet no está activa mientras
            el backend no confirme un estado activo.
          </p>
        </div>

        <div *ngIf="resultState === 'REJECTED'" class="status-card status-error">
          <h4>Verificación rechazada</h4>
          <p>El backend informó el rechazo. La wallet no está activa.</p>
        </div>

        <div *ngIf="resultState === 'SUBMISSION_UNKNOWN'" class="status-card status-pending">
          <h4>No se pudo confirmar el envío</h4>
          <p>
            No repitas automáticamente el envío. Consulta el estado para saber
            si el backend pudo confirmar un resultado.
          </p>
          <button class="button button-secondary"
                  type="button"
                  [disabled]="requestInProgress"
                  (click)="refreshStatus()">
            {{ requestInProgress ? 'Consultando…' : 'Consultar estado' }}
          </button>
        </div>

        <div *ngIf="resultState === 'CHECKING'" class="status-card status-pending">
          <h4>Estado aún no confirmado</h4>
          <p>No presentaremos la wallet como activa sin confirmación del backend.</p>
          <button class="button button-secondary"
                  type="button"
                  [disabled]="requestInProgress"
                  (click)="refreshStatus()">
            {{ requestInProgress ? 'Consultando…' : 'Consultar estado' }}
          </button>
        </div>

        <section *ngIf="resultState === 'PENDING'"
                 class="demo-decision"
                 aria-labelledby="decision-title">
          <h4 id="decision-title">Resolver revisión de demo</h4>
          <p>
            Estas decisiones solo resuelven el mock de esta demo; no representan
            una decisión KYC productiva.
          </p>
          <div class="button-row">
            <button class="button button-primary"
                    type="button"
                    [disabled]="requestInProgress"
                    (click)="resolveDecision('ACTIVE')">
              {{ requestInProgress ? 'Procesando…' : 'Simular decisión ACTIVE' }}
            </button>
            <button class="button button-secondary"
                    type="button"
                    [disabled]="requestInProgress"
                    (click)="resolveDecision('REJECTED')">
              Simular decisión REJECTED
            </button>
          </div>
        </section>

        <section class="report-card" aria-labelledby="report-title">
          <h4 id="report-title">Duración de la demo</h4>
          <p>
            Referencia de producto: <strong>3 minutos</strong>. No es un resultado
            garantizado ni una medición del impacto de un lanzamiento.
          </p>

          <p *ngIf="reportState === 'loading'" aria-live="polite">
            Cargando el reporte de duración…
          </p>
          <p *ngIf="reportState === 'empty'">
            Aún no hay recorridos enviados para calcular una mediana observada.
          </p>
          <p *ngIf="reportState === 'error'">
            El reporte no está disponible en este momento.
          </p>
          <div *ngIf="reportState === 'available' && report" class="report-values">
            <p>
              Mediana observada del onboarding:
              <strong>{{ formatDuration(report.medianOnboardingDurationMs) }}</strong>
              ({{ report.sampleSize }} recorridos).
            </p>
            <p *ngIf="report.medianKycDurationMs != null">
              Mediana de revisión KYC:
              <strong>{{ formatDuration(report.medianKycDurationMs) }}</strong>.
            </p>
            <p *ngIf="report.medianActivationDurationMs != null">
              Mediana hasta activación:
              <strong>{{ formatDuration(report.medianActivationDurationMs) }}</strong>.
            </p>
          </div>
          <p class="report-note">
            Los tiempos de revisión y activación se reportan aparte del tiempo
            de onboarding.
          </p>
        </section>

        <button class="button button-secondary"
                type="button"
                [disabled]="requestInProgress || closeAttempted"
                (click)="finishFlow()">
          {{ requestInProgress ? 'Cerrando…' : 'Finalizar recorrido' }}
        </button>

        <div *ngIf="closeError" class="message message-error" role="alert">
          <p>{{ closeError }}</p>
          <button class="text-button" type="button" (click)="leaveWithoutConfirmedClose()">
            Salir sin confirmación
          </button>
        </div>
      </section>

      <section *ngIf="stage === 'finished'" class="step-content" aria-live="polite">
        <h3>Recorrido finalizado</h3>
        <p>{{ finishedMessage }}</p>
        <p *ngIf="walletActive">
          La wallet sigue activa según la última confirmación del backend. No se
          habilitan pagos desde esta demo.
        </p>
        <p *ngIf="!walletActive">
          No se presenta la wallet como activa.
        </p>
      </section>
    </main>
  </div>

  <footer class="site-footer">
    <p>Demo de onboarding. No procesa pagos ni utiliza datos KYC reales.</p>
  </footer>
</div>
```

```scss
// onboarding.component.scss
:host {
  display: block;
  min-height: 100%;
  color: #182538;
  background: #f3f6fa;
  font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  font-size: 1rem;
  line-height: 1.5;
}

* {
  box-sizing: border-box;
}

.page-shell {
  width: 100%;
  max-width: 90rem;
  margin: 0 auto;
  padding: 1rem;
  overflow-wrap: anywhere;
}

.site-header,
.site-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  flex-wrap: wrap;
}

.site-header {
  margin-bottom: 1.25rem;
}

.brand {
  margin: 0;
  color: #16314a;
  font-size: 1.05rem;
  font-weight: 750;
}

.demo-tag,
.eyebrow {
  color: #475569;
  font-size: 0.875rem;
  font-weight: 650;
}

.demo-tag {
  margin: 0;
  border: 1px solid #cbd5e1;
  border-radius: 999px;
  padding: 0.3rem 0.7rem;
  background: #fff;
}

.onboarding-layout {
  display: grid;
  grid-template-columns: minmax(0, 1fr);
  gap: 1rem;
  align-items: start;
}

.intro-panel,
.flow-card {
  min-width: 0;
}

.intro-panel {
  padding: 0.5rem 0.25rem;
}

.intro-panel h1 {
  max-width: 18ch;
  margin: 0.25rem 0 0.75rem;
  color: #16314a;
  font-size: clamp(1.75rem, 7vw, 2.5rem);
  line-height: 1.12;
  letter-spacing: -0.035em;
}

.intro-panel > p:not(.eyebrow) {
  max-width: 52ch;
  color: #475569;
}

.eyebrow {
  margin: 0;
  color: #075e54;
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.privacy-note {
  margin-top: 1rem;
  border-left: 4px solid #075e54;
  border-radius: 0 0.75rem 0.75rem 0;
  padding: 0.75rem 1rem;
  background: #e8f3f1;
}

.privacy-note h2 {
  margin: 0 0 0.25rem;
  font-size: 1rem;
}

.privacy-note p {
  margin: 0;
  color: #263b4d;
}

.flow-card {
  width: 100%;
  border: 1px solid #d7e0ea;
  border-radius: 1rem;
  padding: 1rem;
  background: #fff;
  box-shadow: 0 0.5rem 1.5rem rgb(20 42 65 / 7%);
}

.card-heading {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 0.75rem;
  flex-wrap: wrap;
}

.card-heading h2 {
  margin: 0.2rem 0 0;
  color: #16314a;
  font-size: 1.4rem;
  line-height: 1.2;
}

.step-count {
  border-radius: 999px;
  padding: 0.3rem 0.65rem;
  background: #e8f3f1;
  color: #064e45;
  font-size: 0.875rem;
  font-weight: 700;
}

.progress-nav {
  margin: 1.25rem 0 1.5rem;
}

.progress-list {
  display: grid;
  grid-template-columns: minmax(0, 1fr);
  gap: 0.5rem;
  margin: 0;
  padding: 0;
  list-style: none;
}

.progress-list li {
  display: flex;
  min-width: 0;
  align-items: center;
  gap: 0.6rem;
  border: 1px solid #d7e0ea;
  border-radius: 0.75rem;
  padding: 0.55rem 0.65rem;
  color: #475569;
  background: #fff;
}

.progress-list li.current {
  border-color: #075e54;
  background: #edf7f5;
  color: #064e45;
  font-weight: 700;
}

.progress-list li.complete {
  border-color: #92c9be;
  color: #064e45;
}

.step-number {
  display: inline-grid;
  width: 1.75rem;
  height: 1.75rem;
  flex: 0 0 1.75rem;
  place-items: center;
  border: 1px solid currentColor;
  border-radius: 50%;
  font-size: 0.875rem;
  font-weight: 750;
}

.step-label {
  min-width: 0;
  overflow-wrap: anywhere;
}

.step-content {
  min-width: 0;
}

.step-content h3 {
  margin: 0 0 0.4rem;
  color: #16314a;
  font-size: 1.3rem;
  line-height: 1.25;
}

.step-content > p {
  margin: 0 0 1rem;
  color: #475569;
}

.field {
  min-width: 0;
  margin: 1.1rem 0;
}

.field label {
  display: inline-block;
  margin-bottom: 0.25rem;
  color: #182538;
  font-weight: 700;
}

.required-mark {
  color: #b42318;
}

.field-help {
  margin: 0 0 0.45rem;
  color: #475569;
  font-size: 0.9375rem;
}

.field input {
  display: block;
  width: 100%;
  min-width: 0;
  min-height: 2.9rem;
  border: 1px solid #64748b;
  border-radius: 0.55rem;
  padding: 0.65rem 0.75rem;
  background: #fff;
  color: #182538;
  font: inherit;
  font-size: 1rem;
}

.field input[readonly] {
  background: #f1f5f9;
  color: #334155;
}

.field input[aria-invalid="true"] {
  border: 2px solid #b42318;
}

.field-error {
  margin: 0.4rem 0 0;
  color: #a31d16;
  font-size: 0.9375rem;
  font-weight: 650;
}

.button {
  display: inline-flex;
  max-width: 100%;
  min-height: 2.9rem;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  border: 2px solid transparent;
  border-radius: 0.65rem;
  padding: 0.65rem 1rem;
  font: inherit;
  font-weight: 700;
  line-height: 1.3;
  text-align: center;
  overflow-wrap: anywhere;
  cursor: pointer;
}

.button-primary {
  background: #075e54;
  color: #fff;
}

.button-primary:hover:not(:disabled) {
  background: #064b44;
}

.button-secondary {
  border-color: #075e54;
  background: #fff;
  color: #064e45;
}

.button-secondary:hover:not(:disabled) {
  background: #edf7f5;
}

.button:disabled {
  cursor: not-allowed;
  opacity: 0.68;
}

button:focus-visible,
input:focus-visible,
.text-button:focus-visible {
  outline: 3px solid #005fcc;
  outline-offset: 3px;
}

.message {
  margin: 0 0 1rem;
  border-radius: 0.6rem;
  padding: 0.75rem 0.9rem;
}

.message-error,
.status-error {
  border: 1px solid #e6a09a;
  background: #fff1f0;
  color: #741b16;
}

.status-card {
  margin: 0.75rem 0 1rem;
  border: 1px solid #d7e0ea;
  border-radius: 0.75rem;
  padding: 1rem;
}

.status-card h4,
.demo-decision h4,
.report-card h4 {
  margin: 0 0 0.35rem;
  font-size: 1.05rem;
}

.status-card p {
  margin: 0;
}

.status-success {
  border-color: #81b9a8;
  background: #edf7f2;
  color: #124c3d;
}

.status-pending {
  border-color: #d6ad63;
  background: #fff8e8;
  color: #68420b;
}

.demo-decision,
.report-card {
  margin: 1rem 0;
  border-top: 1px solid #d7e0ea;
  padding-top: 1rem;
}

.demo-decision p,
.report-card p {
  color: #475569;
}

.button-row {
  display: flex;
  flex-wrap: wrap;
  gap: 0.65rem;
}

.report-card {
  border: 1px solid #d7e0ea;
  border-radius: 0.75rem;
  padding: 1rem;
  background: #f8fafc;
}

.report-card p {
  margin: 0.4rem 0;
}

.report-note {
  font-size: 0.9rem;
}

.text-button {
  border: 0;
  padding: 0.4rem 0;
  background: transparent;
  color: #064e45;
  font: inherit;
  font-weight: 700;
  text-decoration: underline;
  cursor: pointer;
}

.spinner {
  width: 1rem;
  height: 1rem;
  flex: 0 0 1rem;
  border: 2px solid currentColor;
  border-right-color: transparent;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.site-footer {
  justify-content: center;
  margin-top: 1rem;
  color: #475569;
  font-size: 0.875rem;
  text-align: center;
}

.site-footer p {
  margin: 0;
}

.visually-hidden {
  position: absolute;
  width: 1px;
  height: 1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  clip-path: inset(50%);
}

@media (min-width: 48rem) {
  .page-shell {
    padding: 1.5rem;
  }

  .onboarding-layout {
    gap: 1.5rem;
  }

  .flow-card {
    padding: 1.5rem;
  }

  .progress-list {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }

  .progress-list li {
    align-items: flex-start;
  }
}

@media (min-width: 64rem) {
  .page-shell {
    padding: 2rem;
  }

  .onboarding-layout {
    grid-template-columns: minmax(15rem, 0.72fr) minmax(0, 1.28fr);
    gap: 2rem;
  }

  .intro-panel {
    position: sticky;
    top: 2rem;
    padding: 1.5rem 0;
  }

  .flow-card {
    padding: 2rem;
  }
}

@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    scroll-behavior: auto !important;
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
```

```typescript
// onboarding.component.spec.ts
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { OnboardingComponent } from './onboarding.component';

describe('OnboardingComponent', () => {
  let fixture: ComponentFixture<OnboardingComponent>;
  let component: OnboardingComponent;
  let httpTesting: HttpTestingController;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [OnboardingComponent, HttpClientTestingModule]
    }).compileComponents();

    fixture = TestBed.createComponent(OnboardingComponent);
    component = fixture.componentInstance;
    httpTesting = TestBed.inject(HttpTestingController);
    fixture.detectChanges();
  });

  afterEach(() => {
    httpTesting.verify();
  });

  it('bloquea OTP vacío sin llamar a la API y marca el campo inválido', () => {
    component.flowId = 'flow-test';
    component.stage = 'otp';

    component.verifyOtp();

    expect(component.otpForm.invalid).toBeTrue();
    expect(component.otpControl.touched).toBeTrue();
    httpTesting.expectNone('/api/onboarding/flows/flow-test/otp');
  });

  it('rechaza un código con formato inválido antes de llamar a la API', () => {
    component.flowId = 'flow-test';
    component.otpControl.setValue('12 456');

    component.verifyOtp();

    expect(component.otpForm.invalid).toBeTrue();
    httpTesting.expectNone('/api/onboarding/flows/flow-test/otp');
  });

  it('envía el OTP con formato válido al backend y avanza solo tras respuesta', () => {
    component.flowId = 'flow-test';
    component.stage = 'otp';
    component.otpControl.setValue('123456');

    component.verifyOtp();

    const request = httpTesting.expectOne('/api/onboarding/flows/flow-test/otp');
    expect(request.request.method).toBe('POST');
    expect(request.request.body).toEqual({ code: '123456' });

    request.flush({
      flowId: 'flow-test',
      state: 'OTP_VERIFIED',
      currentStep: 'KYC_DATA',
      walletActive: false
    });

    expect(component.stage).toBe('kyc');
    expect(component.walletActive).toBeFalse();
  });

  it('rechaza documentos compuestos solo por espacios sin llamar a la API', () => {
    component.flowId = 'flow-test';
    component.stage = 'kyc';
    component.documentControl.setValue('     ');

    component.submitKyc();

    expect(component.kycForm.invalid).toBeTrue();
    expect(component.documentControl.touched).toBeTrue();
    httpTesting.expectNone('/api/onboarding/flows/flow-test/submit');
  });

  it('rechaza un formato de documento que no empieza con TEST-', () => {
    component.flowId = 'flow-test';
    component.documentControl.setValue('DOC-DEMO-001');

    component.submitKyc();

    expect(component.documentControl.hasError('testDocument')).toBeTrue();
    httpTesting.expectNone('/api/onboarding/flows/flow-test/submit');
  });

  it('rechaza TEST- sin un valor ficticio después del prefijo', () => {
    component.flowId = 'flow-test';
    component.documentControl.setValue('TEST-   ');

    component.submitKyc();

    expect(component.documentControl.invalid).toBeTrue();
    httpTesting.expectNone('/api/onboarding/flows/flow-test/submit');
  });

  it('envía los datos ficticios válidos con documentType TEST', () => {
    component.flowId = 'flow-test';
    component.stage = 'kyc';
    component.documentTypeControl.setValue('TEST');
    component.documentControl.setValue('TEST-DEMO-001');

    component.submitKyc();

    const request = httpTesting.expectOne('/api/onboarding/flows/flow-test/submit');
    expect(request.request.method).toBe('POST');
    expect(request.request.body).toEqual({
      documentType: 'TEST',
      document: 'TEST-DEMO-001'
    });

    request.flush({
      flowId: 'flow-test',
      state: 'ACTIVE',
      walletActive: true
    });

    expect(component.stage).toBe('result');
    expect(component.resultState).toBe('ACTIVE');
    expect(component.walletActive).toBeTrue();

    const reportRequest = httpTesting.expectOne('/api/onboarding/report');
    reportRequest.flush({
      medianOnboardingDurationMs: 120000,
      sampleSize: 2
    });

    expect(component.reportState).toBe('available');
  });

  it('mantiene el formulario y permite reintentar ante KYC_UNAVAILABLE', () => {
    component.flowId = 'flow-test';
    component.stage = 'kyc';
    component.documentControl.setValue('TEST-DEMO-001');

    component.submitKyc();

    const request = httpTesting.expectOne('/api/onboarding/flows/flow-test/submit');
    request.flush(
      { code: 'KYC_UNAVAILABLE' },
      { status: 503, statusText: 'Service Unavailable' }
    );

    expect(component.stage).toBe('kyc');
    expect(component.walletActive).toBeFalse();
    expect(component.documentControl.value).toBe('TEST-DEMO-001');
    expect(component.globalError).toContain('no está activa');

    component.globalError = '';
    component.submitKyc();

    const retry = httpTesting.expectOne('/api/onboarding/flows/flow-test/submit');
    expect(retry.request.method).toBe('POST');
    retry.flush({
      flowId: 'flow-test',
      state: 'PENDING',
      walletActive: false
    });

    expect(component.resultState).toBe('PENDING');
    expect(component.walletActive).toBeFalse();

    httpTesting.expectOne('/api/onboarding/report').flush({ sampleSize: 0 });
  });

  it('no emite solicitudes duplicadas mientras la primera sigue pendiente', () => {
    component.stage = 'intro';

    component.startFlow();
    component.startFlow();

    const requests = httpTesting.match('/api/onboarding/flows');
    expect(requests.length).toBe(1);
    requests[0].flush({
      flowId: 'flow-test',
      state: 'STARTED',
      currentStep: 'PHONE_OTP',
      walletActive: false
    });
  });

  it('asocia ayuda y error visibles al campo inválido', () => {
    component.stage = 'kyc';
    component.flowId = 'flow-test';
    fixture.detectChanges();

    component.submitKyc();
    fixture.detectChanges();

    const input: HTMLInputElement | null =
      fixture.nativeElement.querySelector('#test-document');
    const help = fixture.nativeElement.querySelector('#document-help');
    const error = fixture.nativeElement.querySelector('#document-error');

    expect(input?.getAttribute('aria-invalid')).toBe('true');
    expect(input?.getAttribute('aria-describedby')).toContain('document-help');
    expect(input?.getAttribute('aria-describedby')).toContain('document-error');
    expect(help).not.toBeNull();
    expect(error?.textContent).toContain('identificador');
    httpTesting.expectNone('/api/onboarding/flows/flow-test/submit');
  });
});
```

```typescript
// onboarding.component.responsive-checklist.ts
/**
 * Lista de comprobación manual; no es una prueba automatizada de layout.
 *
 * Estado de ejecución de esta entrega: PENDIENTE. No se ejecutó navegador ni
 * se declara verificación visual realizada.
 *
 * En cada viewport revisar:
 * - 320 px: inicio, OTP, KYC con ayuda, KYC con error, carga y resultados.
 * - 768 px: mismos estados; pasos visibles y textos/botones sin recorte.
 * - 1280 px: composición de escritorio y lectura del panel lateral y tarjeta.
 * - Zoom del navegador al 200%: recorrer inicio, formularios y resultado.
 *
 * Criterios de aceptación manual:
 * - Sin scroll horizontal.
 * - Ningún campo, mensaje, etiqueta, paso ni acción queda recortado.
 * - Ayudas y errores permanecen visibles y asociados al control.
 * - Foco de teclado visible; el primer campo inválido recibe foco.
 * - El resultado pendiente o incierto nunca se muestra como wallet activa.
 */
export const RESPONSIVE_CHECKS_STATUS = 'PENDIENTE';
```