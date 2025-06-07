from langchain_core.tools import tool
from langgraph.prebuilt import InjectedState
from typing_extensions import Annotated


@tool
def reduce_documents(
    state: Annotated[dict, InjectedState],
) -> str:
    """Reduce Document List from Agent State to a single string for LLM input"""
    doc = "\n".join(doc.page_content for doc in state["documents"])
    return f"Reduced document: \n {doc}"
