"""Agente frontend para el MVP de wallet en Peru."""
from crewai import Agent, Task
from agents.feature_scope import is_onboarding_feature, scoped_instructions
from crew.llm_config import llm

KEY = 'frontend'
LABEL = 'Desarrollador frontend'
SPEC_FILE = 'frontend_spec.md'
EXTRACT_CODE = True

INSTRUCTIONS = """
Implementa en Angular la experiencia de usuario de la funcionalidad recibida y
su contrato aprobado. Genera pantallas web, no solo servicios o logica, y
entrega frontend_spec.md junto con HTML, CSS/SCSS y codigo Angular extraible.

Usa diseno responsive mobile-first, componentes reutilizables, jerarquia visual
clara y contraste accesible. Verifica anchos de 320, 768 y 1280 px y zoom al
200%, sin desplazamiento horizontal ni contenido recortado.

Define acciones, validaciones y mensajes claros en espanol. En formularios usa
Reactive Forms y validadores que correspondan al contrato; rechaza texto
compuesto solo por espacios. Identifica campos requeridos, ofrece ayuda
persistente, muestra errores accionables, conserva los datos ingresados y
enfoca el primer campo invalido. Bloquea envios invalidos o duplicados.

Asocia etiquetas, ayuda y errores con label/for y atributos ARIA; conserva
navegacion por teclado y foco visible. Cubre estados de carga, vacio, exito y
error. No inventes requisitos, contratos, datos personales ni resultados de
pruebas. Distingue las comprobaciones propuestas de las ejecutadas.
Limita la implementacion a la funcionalidad y sus criterios de aceptacion.
"""

PAYMENT_GUIDANCE = """
Aplica estas reglas solo a funcionalidades de pago:
- Muestra destinatario e importe antes de confirmar, conforme al contrato.
- No presentes solicitudes aceptadas o pendientes como pagos confirmados.
  Maneja confirmaciones asincronas, limites e idempotencia segun el contrato.
- Toda ejecucion y confirmacion ocurre en backend; el cliente no acredita el
  resultado. No asumas un unico riel ni que un pago P2P puede cancelarse.
- Incluye pruebas de confirmacion, estados pendientes y envios duplicados.
"""

ONBOARDING_GUIDANCE = """
Aplica estas reglas solo porque la funcionalidad seleccionada es onboarding:
- Muestra la secuencia de pasos requeridos y el paso actual. Bloquea el avance
  ante datos obligatorios ausentes o invalidos e indica como corregirlos.
- Usa exclusivamente datos TEST, incluidos documentos TEST- y numeros de
  celular de prueba; no actives operaciones financieras reales.
- Simula el OTP solo en el frontend: genera/compara localmente el codigo fijo
  123456 y permite que el tester lo ingrese manualmente. Documenta o muestra el
  codigo al tester. No hagas llamadas API para OTP ni envies SMS; aclara que no
  verifica realmente la titularidad del numero.
- Usa el mock existente solo para KYC y conforme a su contrato. Mapea
  APPROVED/ACTIVE a wallet activa, MANUAL_REVIEW/PENDING a revision pendiente y
  REJECTED/REJECTED a rechazo. No presentes lo pendiente como aprobado; la
  revision manual se resuelve con la capacidad del mock, sin consola de soporte.
- Instrumenta inicio, finalizacion de cada paso y cierre. Mide hasta el envio
  exitoso de los datos de todos los pasos; reporta aparte revision KYC y tiempo
  hasta activacion. No incluyas MAU, CAC ni checkout.
- No agregues pagos, QR, historial ni soporte de pagos al flujo de onboarding.
Entrega frontend_spec.md y codigo Angular con pruebas de validacion, estados,
OTP local, KYC y eventos; distingue resultados ejecutados de pendientes.
"""

agent = Agent(
    role='Desarrollador frontend Angular de la wallet MVP de Peru',
    goal=(
        "Disenar e implementar interfaces web responsive y accesibles, con "
        "formularios validados segun el contrato aprobado para la funcionalidad."
    ),
    backstory=(
        "Eres especialista en Angular, diseno web responsive mobile-first y "
        "experiencias accesibles. Creas pantallas y formularios que respetan "
        "los contratos, criterios de aceptacion y limites de cada funcionalidad."
    ),
    llm=llm,
    verbose=True,
    allow_delegation=False,
)


def build_task(feature: dict) -> Task:
    instructions = scoped_instructions(
        feature,
        INSTRUCTIONS,
        onboarding=ONBOARDING_GUIDANCE,
        payment=PAYMENT_GUIDANCE,
    )
    onboarding = is_onboarding_feature(feature)
    return Task(description=instructions + "\nFeature: " + str(feature.get("title", ""))
                + "\n" + str(feature.get("description", ""))
                + "\n" + str(feature.get("acceptance_criteria", [])),
                expected_output=(
                    ('Contenido de frontend_spec.md para onboarding con pasos, validaciones, '
                     'OTP local, estados KYC, eventos y exclusiones; ' if onboarding else
                     'Contenido de frontend_spec.md con diseno visual web, ')
                    + 'layouts responsive para movil, tablet y escritorio, '
                    'recorrido, campos requeridos, validaciones, ayuda por campo, '
                    'mensajes de error, estados, accesibilidad, dependencias y '
                    'comprobaciones de aceptacion; codigo Angular '
                    'con Reactive Forms, plantillas HTML, estilos CSS/SCSS '
                    'y pruebas de la funcionalidad con resultados ejecutados '
                    'o pendientes en bloques markdown, cada bloque con primera '
                    'linea // nombre-del-archivo.ext, por ejemplo '
                    '// onboarding.service.ts.'
                ), agent=agent)