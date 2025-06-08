from langchain_core.tools import tool
from langgraph.types import Command
import uuid
import json
from langchain_core.documents import Document
from .scripts.store import get_vectorstore


@tool
def store_document(page_content: str, metadata: dict|None = {}) -> Command:
    "Store Documents from AgentState to VectorStore"
    
    match metadata:
        case n if isinstance(n, str):
            try:
                metadata = json.loads(metadata)
            except:
                metadata = {}
                # raise Exception("metadata is not a json string")
        case n if isinstance(n, dict):
            pass
        case _:
            metadata = {}
    documents = [Document(page_content=page_content, metadata=metadata)]
    vectorstore = get_vectorstore()
    uuids = [str(uuid.uuid4()) for _ in range(len(documents))]
    vectorstore.add_documents(documents=documents, ids=uuids)
