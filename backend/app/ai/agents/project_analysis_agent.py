from __future__ import annotations

from agents import Agent, ModelSettings

from app.ai.prompts import PROJECT_ANALYSIS_INSTRUCTIONS
from app.ai.schemas import ProjectAnalysisReport


def create_project_analysis_agent(*, model: str, reasoning_effort: str) -> Agent:
    return Agent(
        name="ProjectLens Analysis Agent",
        instructions=PROJECT_ANALYSIS_INSTRUCTIONS,
        model=model,
        model_settings=ModelSettings(
            reasoning={"effort": reasoning_effort},
            include_usage=True,
            store=True,
        ),
        output_type=ProjectAnalysisReport,
    )

