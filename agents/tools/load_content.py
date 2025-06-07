from langchain_core.tools import tool
import re
from langchain_core.documents import Document
from .scripts.loader import DocumentLoader
from typing import Literal, List
from langgraph.types import Command
from langchain_core.tools import InjectedToolArg
from langchain_core.messages import ToolMessage
from typing_extensions import Annotated
from langchain_core.messages import ToolMessage
from langgraph.prebuilt import InjectedState
from langchain_core.tools.base import InjectedToolCallId


@tool
def load_content(
    url: str,
    max_characters: int = 4e5,
    overlap: int = 5e4,
) -> List[Document]:
    """Load content by URL as List of Documents to State"""

    try:
        loader = DocumentLoader(
            web_url=url,
            chunking_strategy="basic",
            max_characters=max_characters,
            overlap=overlap,
        )
        documents = loader()

        if len(documents) == 1:
            next_message = "Use Reduce Tool next!"
        else:
            next_message = "Use StoreDocuments Tool next!"
        return {"documents": documents}
    except Exception as e:
        raise e
