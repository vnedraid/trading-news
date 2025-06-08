from langchain_core.tools import tool
from langgraph.types import Command
from .scripts.store import get_vectorstore


@tool
def retrive_documents(
    query: str,
) -> Command:
    "Search similar documents in Vector Store if earlier documents was Loaded and Sored. Query - text search query to get similar documents not URL."
    vectorstore = get_vectorstore()
    retriver = vectorstore.as_retriever(k=3)
    documents = retriver.invoke(query)
    if bool(documents):
        return {"documents": documents}
    else:
        return {"documents": []}
