from langgraph.prebuilt import create_react_agent
from langgraph_supervisor import create_supervisor
import os
from .tools import get_tools
from .prompts import PROMPTS
from .models import llm
from typing import Sequence
from langchain_core.messages import AIMessage
from langchain_core.tools import BaseTool
from langgraph.graph import END, StateGraph
from langgraph.prebuilt.tool_node import ToolNode
from typing import cast
from langchain_core.language_models import BaseChatModel
import logging
from langchain_core.runnables import RunnableConfig
from .monitoring import langfuse_handler
from .nodes import *
from .edges import *
from .states import *
from .prompts import *

"""
1. Саммаризатор - создание краткого саммари



2. Теггер - добавление тегов 


3. Редублер сообщений - 
Саммарзация
Лента
Алерты

"""




summary_agent = create_react_agent(
    model=llm,
    tools=get_tools(["load_content", "reduce_documents", "store_documents"]),
    prompt="Пожалуйста, создайте краткое описание текста",
    name="summary_agent"
)

rag_agent = create_react_agent(
    model=llm,
    tools=get_tools(["retrive_documents"]),
    prompt="You are a RAG assistant",
    name="rag_agent"
)

# supervisor = create_supervisor(
#     agents=[flight_assistant, hotel_assistant],
#     model=llm,
#     prompt=(
#         "You manage a hotel booking assistant and a"
#         "flight booking assistant. Assign work to them."
#     )
# ).compile()

AGENTS = {
    'summary': summary_agent, 
    'rag': rag_agent,
    'saver': get_tools(["store_documents"])[0]
    # 'supervisor': supervisor
}