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

class Agent:
    """Универсальный класс Агента"""

    nodes = [
        get_answer_node,
        structure_generation_node,
        reflection_node,
        generation_node,
    ]
    condition_edges = [
        should_continue_edge,
        should_call_tool_edge,
    ]
    
    _last_message_index = -1
    tools = None
    tool_node = None
    graph = None

    def __init__(
        self,
        llm: str,
        role: str,
        name: str | None = None,
        tools: Sequence[BaseTool] | None = None,
        output: dict | None = None,
        reflection: bool = False,
        reflection_role: str | None = None,
        cut_message_history: bool = True,
    ) -> None:
        self.llm = llm
        self.role = role
        self.output = output
        self.reflection = reflection
        self.name = name
        self.cut_message_history = cut_message_history

        for func in self.nodes + self.condition_edges:
            self.register_function(func)

        if bool(tools):
            self.bind_tools()

        if reflection:
            self.reflection_role = (
                reflection_role
                if (reflection_role is not None)
                else generate_reflection_role(llm, role)
            )

        if output:
            self.UserModel = create_user_output_pydantic(self.output)
            self.output_message = create_user_format_message(self.output)

        self.build_graph()

    def register_function(self, func):
        """Регистрируем функцию в агенте"""
        self.graph.register_function(func)
        
    async def __call__(self, *args, **kwds):
        return await self.graph.ainvoke(*args, **kwds)
    
    def bind_tools(self):
        """Добавляем инструменты к агенту"""
        logging.debug(f"Tools: {self.tools}")
        if isinstance(self.tools, ToolNode):
            tool_classes = list(self.tools.tools_by_name.values())
            self.tool_node = self.tools
        else:
            self.tool_node = ToolNode(self.tools)
            tool_classes = list(self.tool_node.tools_by_name.values())
        tool_calling_enabled = len(tool_classes) > 0
        logging.debug(f"Tools: {tool_classes}")
        if tool_calling_enabled:
            self.llm = cast(BaseChatModel, self.llm).bind_tools(tool_classes)
            logging.debug(f"LLM: {self.llm}")

    def build_graph(self):
        builder = StateGraph(
            State,
            # input=InputState,
            # output=OutputState if self.output is not None else State,
        )
        builder.add_node("get_answer", self.get_answer_node)
        # Структурированный вывод
        generation_func = (
            self.structure_generation_node if self.output else self.generation_node
        )
        builder.add_node("generate", generation_func)
        if self.tools:  # Инструменты
            builder.add_node("tools", self.tool_node)
            builder.add_conditional_edges("generate", self.should_call_tool_edge)
            builder.add_edge("tools", "generate")
        if self.reflection:  # Рефлекция
            builder.add_node("reflect", self.reflection_node)
            builder.add_edge("generate", "reflect")
            builder.add_conditional_edges("reflect", self.should_continue_edge)
        if not (self.reflection | bool(self.tools)):  # Обычный случай
            builder.add_edge("generate", "get_answer")
        builder.add_edge("get_answer", END)
        builder.set_entry_point("generate")
        graph = builder.compile(name=self.name)
        self.graph = graph