from typing import Annotated, List
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict
from langchain_core.messages import BaseMessage
from typing_extensions import Annotated, TypedDict
from langchain_core.documents import Document


def manage_list(existing: list, updates: list | dict):
    if isinstance(updates, list):
        # Normal case, add to the history
        return existing + updates
    elif isinstance(updates, dict) and updates["type"] == "keep":
        # You get to decide what this looks like.
        # For example, you could simplify and just accept a string "DELETE"
        # and clear the entire list.
        return existing[updates["from"] : updates["to"]]

class State(TypedDict):
    messages: Annotated[list, manage_list]
    structure_output: dict | None = None
    documents: List[Document] | None = None
    answer: BaseMessage | str | None = None
