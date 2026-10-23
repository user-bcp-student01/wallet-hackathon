"""Agente inicial del taller. Mejora sus instrucciones sin cambiar su contrato."""
from crewai import Agent, Task
from agents.feature_scope import scoped_instructions
from crew.llm_config import llm

KEY = 'testing'
LABEL = 'Ingeniero de pruebas'
SPEC_FILE = 'testing_report.md'
EXTRACT_CODE = True

INSTRUCTIONS = """
Deriva casos de prueba de la descripcion y los criterios de aceptacion de la
funcionalidad. Incluye recorridos validos, entradas invalidas y estados de error.
Propone comandos reproducibles y distingue claramente pruebas ejecutadas de
pruebas pendientes. No inventes resultados ni llames servicios externos.
"""

ONBOARDING_GUIDANCE = """
Para funcionalidades de onboarding, cubre pasos y validaciones, mensajes
accionables, OTP fijo 123456 ingresado manualmente y generado/comparado solo en
frontend sin API ni SMS, estados KYC ACTIVE/PENDING/REJECTED, datos TEST,
eventos y frontera de duracion hasta el envio exitoso de todos los datos.
Verifica que revision KYC y activacion se reporten aparte y que no se agreguen
pagos, QR, historial, soporte de pagos, MAU, CAC ni medicion de checkout.
"""
agent = Agent(role='Ingeniero de pruebas', goal="Completar la tarea asignada.",
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
                expected_output='Un informe de pruebas.', agent=agent)
