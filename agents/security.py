"""Agente inicial del taller. Mejora sus instrucciones sin cambiar su contrato."""
from crewai import Agent, Task
from agents.feature_scope import scoped_instructions
from crew.llm_config import llm

KEY = 'security'
LABEL = 'Revisor de seguridad'
SPEC_FILE = 'security_report.md'
EXTRACT_CODE = False

INSTRUCTIONS = """
Revisa la funcionalidad recibida para detectar riesgos de seguridad y privacidad
relacionados con sus entradas, salidas, contratos y manejo de datos. Recomienda
controles concretos y proporcionales al alcance. No incluyas secretos ni datos
personales reales y no afirmes cumplimiento normativo sin evidencia.
"""

ONBOARDING_GUIDANCE = """
Para onboarding, exige exclusivamente documentos y numeros de celular TEST.
Confirma que el OTP fijo 123456 se genera y valida localmente en frontend, sin
API ni SMS, y que se identifica como simulacion, no como verificacion real de
titularidad. Evita registrar OTP y datos personales en logs o analitica. No
introduzcas funciones de pago, QR, historial, soporte, MAU, CAC o checkout.
"""
agent = Agent(role='Revisor de seguridad', goal="Completar la tarea asignada.",
              backstory="Eres un integrante del equipo.", llm=llm,
              verbose=True, allow_delegation=False)


def build_task(feature: dict) -> Task:
    instructions = scoped_instructions(
        feature,
        INSTRUCTIONS,
        onboarding=ONBOARDING_GUIDANCE,
    )
    return Task(description=instructions + "\nFeature: " + str(feature.get("title", ""))
                + "\n" + str(feature.get("description", ""))
                + "\n" + str(feature.get("acceptance_criteria", [])),
                expected_output='Un informe de seguridad.', agent=agent)
