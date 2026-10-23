"""Agente inicial del taller. Mejora sus instrucciones sin cambiar su contrato."""
from crewai import Agent, Task
from agents.feature_scope import scoped_instructions
from crew.llm_config import llm

KEY = 'chapter'
LABEL = 'Chapter'
SPEC_FILE = 'chapter_review.md'
EXTRACT_CODE = False

INSTRUCTIONS = """
Compara las entregas de cada rol con la funcionalidad, sus criterios de
aceptacion y contratos aprobados. Identifica omisiones, contradicciones,
ampliaciones de alcance y evidencia no ejecutada presentada como resultado.
Emite VEREDICTO: APROBADO o VEREDICTO: RECHAZADO con razones verificables.
"""

ONBOARDING_GUIDANCE = """
Para onboarding, confirma pasos guiados, validaciones accionables, datos TEST,
OTP fijo 123456 local al frontend sin API ni SMS, mapeo KYC ACTIVE/PENDING/
REJECTED, eventos y duracion hasta el envio exitoso, excluyendo revision KYC y
activacion. Rechaza la inclusion de pagos, QR, historial, soporte de pagos,
MAU, CAC o medicion de checkout en el alcance de onboarding.
"""
agent = Agent(role='Chapter', goal="Completar la tarea asignada.",
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
                expected_output='Un informe con VEREDICTO: APROBADO o RECHAZADO.', agent=agent)
