from langchain_core.tools import tool
import re
from langchain_core.documents import Document
from typing import List
from langgraph.types import Command
from langchain_core.messages import ToolMessage
from langgraph.prebuilt import InjectedState
from typing_extensions import Annotated
from langchain_core.tools.base import InjectedToolCallId


@tool
def reduce_documents(
    state: Annotated[dict, InjectedState],
) -> str:
    """Reduce Document List from Agent State to a single string for LLM input"""
    doc = "\n".join(doc.page_content for doc in state["documents"])
    return f"Reduced document: \n {doc}"
