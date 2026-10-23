"""Agente inicial del taller. Mejora sus instrucciones sin cambiar su contrato."""
from crewai import Agent, Task
from crew.llm_config import llm

KEY = 'backend'
LABEL = 'Desarrollador backend'
SPEC_FILE = 'backend_spec.md'
EXTRACT_CODE = True

INSTRUCTIONS = """Implementa los endpoints y servicios del plan, respetando el contrato de API.
Valida las entradas y devuelve errores coherentes.
Define acceso a datos y transacciones. En equipos de seis cubre también esquema y migraciones; con Datos, consume su contrato sin duplicar sus migraciones.
Incluye un caso válido, un error y comandos para comprobarlos.
Entrega backend_spec.md y código Java con el formato de extracción que ya exige build_task."""
agent = Agent(
    role='Desarrollador backend',
    goal="Implementar los endpoints y servicios del Issue según sus criterios de aceptación y el contrato de API aprobado.",
    backstory="Eres responsable del backend Java: traduces los contratos aprobados a servicios, endpoints, validaciones y persistencia verificables. Coordinas con Arquitectura los cambios de API y respetas el contrato de Datos cuando ese rol está activo.",
    llm=llm,
    verbose=True,
    allow_delegation=False,
)


def build_task(feature: dict) -> Task:
    title = str(feature.get("title", "sin título"))
    description = str(feature.get("description", ""))
    acceptance_criteria = str(feature.get("acceptance_criteria", []))
    return Task(
        description=(
            INSTRUCTIONS
            + "\nIssue: " + title
            + "\nDescripción: " + description
            + "\nCriterios de aceptación: " + acceptance_criteria
        ),
        expected_output=(
            f'Para el Issue «{title}», entrega primero backend_spec.md relacionando cada criterio de '
            'aceptación con la implementación, el contrato, las validaciones, errores y acceso a datos. '
            'Incluye el recorrido de un caso válido y uno de error, además de comandos reproducibles para '
            'comprobarlos. Después entrega cada archivo Java en un bloque markdown independiente, con '
            '// Nombre.java como primera línea y el package correspondiente a su ubicación de extracción '
            '(service, resource, repository, dto o model).'
        ),
        agent=agent,
    )


