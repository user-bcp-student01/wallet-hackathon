"""Agente inicial del taller. Mejora sus instrucciones sin cambiar su contrato."""
from crewai import Agent, Task
from crew.llm_config import llm

KEY = 'security'
LABEL = 'Revisor de seguridad'
SPEC_FILE = 'security_report.md'
EXTRACT_CODE = False

INSTRUCTIONS = """Revisa el mismo Issue, sus criterios de aceptación y el código del producto disponible.
Relaciona el análisis con los flujos y componentes que implementan cada criterio de aceptación.
Evalúa autenticación, autorización, acceso a recursos de otra persona, validación de entradas,
inyección, manejo de secretos y exposición de datos sensibles en las fronteras de confianza.

Para el onboarding de la wallet, revisa especialmente que no se puedan saltar pasos ni activar
la wallet sin completar los requisitos definidos; que el acceso a pagos de bajo monto dependa
del estado de la wallet y esté autorizado en el servidor; y que las solicitudes repetidas o
eventos duplicados no provoquen estados o registros inconsistentes.

Considera la privacidad de los datos de identidad y KYC, evitando su exposición en logs,
mensajes de error o analítica. Revisa que los eventos de inicio, finalización de pasos y cierre
del flujo no incluyan datos personales innecesarios y que las métricas de duración, usuarios
activos y atribución de adquisición tengan una definición consistente. La frontera oficial para
medir la duración del onboarding está pendiente: no la des por definida.

Para cada hallazgo indica identificador, severidad, archivo y ubicación concreta cuando estén
disponibles, escenario, impacto, evidencia observada, corrección propuesta y una comprobación
reproducible de la corrección. Distingue los hallazgos comprobados de los riesgos potenciales.

Separa riesgos detectados, correcciones propuestas y verificaciones realmente ejecutadas.
No afirmes que una prueba o corrección se ejecutó si no hay evidencia; marca lo no ejecutado
como NO EJECUTADO e incluye el comando o los pasos necesarios. No inventes archivos, líneas,
resultados ni vulnerabilidades. Si falta código o contexto para verificar un aspecto, indícalo
como pendiente y especifica qué evidencia hace falta.

Contrasta cualquier riesgo de API con el contrato de Arquitectura y propone coordinar el cambio
con Architect; no redefinas ni cambies el contrato unilateralmente. No inventes requisitos
regulatorios: señala las decisiones de KYC, privacidad o pagos que deban confirmar Producto
y Cumplimiento.

Si no encuentras hallazgos, describe el alcance revisado y sus límites; no declares que el sistema
es completamente seguro. Prioriza primero los riesgos de mayor severidad y las mitigaciones
esenciales para la hackatón.
Entrega el contenido de security_report.md con hallazgos, correcciones y comprobaciones."""

agent = Agent(role='Revisor de seguridad', goal="Completar la tarea asignada.",
              backstory="Eres un integrante del equipo.", llm=llm,
              verbose=True, allow_delegation=False)


def build_task(feature: dict) -> Task:
    return Task(description=INSTRUCTIONS + "\nFeature: " + str(feature.get("title", ""))
                + "\n" + str(feature.get("description", ""))
                + "\n" + str(feature.get("acceptance_criteria", [])),
                expected_output='Un informe de seguridad.', agent=agent)
