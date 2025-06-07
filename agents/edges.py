from typing import Literal
from langgraph.graph import END, START
import logging


def should_refine_edge(self, state) -> Literal["refine_summary", END]:  # type: ignore
    if state["index"] >= len(state["documents"]):
        return END
    else:
        return "refine_summary"


def should_call_tool_edge(self, state):
    last_message = state["messages"][-1]
    if last_message.tool_calls:
        return "tools"
    elif not last_message.tool_calls:
        return "reflect" if self.reflection else "get_answer"


def should_continue_edge(self, state):
    last_message = state["messages"][-1]
    if "Задача решена" in last_message.content or len(state["messages"]) > 6:
        return "get_answer"
    else:
        return "generate"
