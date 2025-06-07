from langchain_core.tools import tool
from langgraph.types import Command
from langchain_core.tools import InjectedToolArg
from langchain_core.messages import ToolMessage
from typing import Annotated
from langchain_core.messages import ToolMessage
from langgraph.prebuilt import InjectedState
from langchain_core.tools.base import InjectedToolCallId
from .scripts.store import get_vectorstore
import os


@tool
def retrive_documents(
    query: str, 
) -> Command:
    "Search similar documents in Vector Store if earlier documents was Loaded and Sored. Query - text search query to get similar documents not URL."
    vectorstore = get_vectorstore()
    retriver = vectorstore.as_retriever(k=3)
    documents = retriver.invoke(query)
    tool_call_id = ""
    if bool(documents):
        return {"documents": documents}
    else:
        return "No documents found. Use Load Content Tool next if you have URL of document!"
