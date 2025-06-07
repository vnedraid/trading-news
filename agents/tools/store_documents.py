from langchain_core.tools import tool
from langgraph.types import Command
import uuid
from langchain_core.documents import Document
from .scripts.store import get_vectorstore


@tool
def store_documents(documents: list[dict]) -> Command:
    "Store Documents from AgentState to VectorStore"

    if isinstance(documents[0], dict):
        documents = [Document(**doc) for doc in documents]

    vectorstore = get_vectorstore()

    print("vectorstore", vectorstore)

    uuids = [str(uuid.uuid4()) for _ in range(len(documents))]
    print("start to save documents !!!")
    vectorstore.add_documents(documents=documents, ids=uuids)
    return {"status":"Successfully upload Documents in VectorStore. You can use RetriveDocuments Tool if need to get relevant stored documents"}
