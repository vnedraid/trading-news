from dataclasses import dataclass
from temporalio import activity

from agents.agents import *


@dataclass
class AgentParams:
    payload: dict
    agent: str


@activity.defn
async def run_agent(params: AgentParams) -> dict:
    agent = AGENTS.get(params.agent)
    response = await agent.ainvoke(
        params.payload,
    )
    return response
