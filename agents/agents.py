from langgraph.prebuilt import create_react_agent
import yaml

from .tools import get_tools, TOOLS
from .states import *
from .models import llm


with open("agents/configs.yaml", "r", encoding='utf-8') as f:
    configs = yaml.safe_load(f)

AGENTS = {}
for name in configs.keys():
    agent = create_react_agent(
        model=llm,
        name=configs[name]["name"],
        prompt=configs[name]["system_prompt"],
        tools=get_tools(
            configs[name]["tools"]
        ),
        response_format=configs[name].get("output_schema")
    )
    AGENTS.update({name: agent})

AGENTS = AGENTS | TOOLS
