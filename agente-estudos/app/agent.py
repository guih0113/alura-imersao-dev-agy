# ruff: noqa
import datetime
import os
from pathlib import Path
from typing import Optional

from google.adk.agents import Agent
from google.adk.agents.readonly_context import ReadonlyContext
from google.adk.apps import App
from google.adk.environment import LocalEnvironment
from google.adk.models import Gemini
from google.adk.skills import load_skill_from_dir
from google.adk.tools.base_tool import BaseTool
from google.adk.tools.environment import EnvironmentToolset
from google.adk.tools.skill_toolset import SkillToolset
from google.genai import types

MODEL = os.environ.get("MODEL", "gemini-3.8-flash")

CURRENT_DIR = Path(__file__).resolve().parent
PLANOS_DIR = (CURRENT_DIR.parent / "planos").resolve()
SKILL_DIR = (CURRENT_DIR / "skills" / "plano-de-estudos").resolve()

# Garante que o diretório de planos exista
PLANOS_DIR.mkdir(parents=True, exist_ok=True)


class FerramentasDeArquivo(EnvironmentToolset):
    """Toolset de ambiente restrito apenas para leitura e escrita de arquivos."""

    async def get_tools(
        self, readonly_context: Optional[ReadonlyContext] = None
    ) -> list[BaseTool]:
        tools = await super().get_tools(readonly_context)
        return [t for t in tools if t.name in ("ReadFile", "WriteFile")]


def instruction_provider(context: Optional[ReadonlyContext] = None) -> str:
    hoje = datetime.date.today().strftime("%Y-%m-%d")
    return (
        f"Hoje é {hoje}. "
        "Você é um mentor de estudos especialista. "
        "Seu papel é orientar o estudante e criar planos personalizados com base na skill plano-de-estudos. "
        "Respeite estritamente a regra de ativação (gating rule) da skill antes de planejar ou carregar recursos."
    )


skill = load_skill_from_dir(SKILL_DIR)
skill_toolset = SkillToolset(skills=[skill])
file_toolset = FerramentasDeArquivo(
    environment=LocalEnvironment(working_dir=str(PLANOS_DIR))
)

root_agent = Agent(
    name="agente_estudos",
    model=Gemini(
        model=MODEL,
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=instruction_provider,
    tools=[skill_toolset, file_toolset],
)

app = App(
    root_agent=root_agent,
    name="app",
)
