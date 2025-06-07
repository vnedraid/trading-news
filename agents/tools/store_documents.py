from langchain_core.tools import tool
from langgraph.types import Command
from langchain_core.tools import InjectedToolArg
from langchain_core.messages import ToolMessage
from typing import Annotated
from langchain_core.messages import ToolMessage
from langgraph.prebuilt import InjectedState
from langchain_core.tools.base import InjectedToolCallId
import uuid
from langchain_postgres.vectorstores import PGVector
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from ..models import embeddings
from .scripts.store import get_vectorstore
import os


@tool
async def store_documents(
    documents: list[dict]
) -> Command:
    "Store Documents from AgentState to VectorStore"
    print('documents', documents)
    
    if isinstance(documents[0], dict):
        documents = [Document(**doc) for doc in documents]
        
    vectorstore = get_vectorstore()
    
    print('vectorstore', vectorstore)
    
    uuids = [str(uuid.uuid4()) for _ in range(len(documents))]
    print('start to save documents !!!')
    await vectorstore.add_documents(documents=documents, ids=uuids)
    return "Successfully upload Documents in VectorStore. You can use RetriveDocuments Tool if need to get relevant stored documents"
