from langchain_gigachat.embeddings import GigaChatEmbeddings
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
from langchain_core.vectorstores import VectorStore
from ...models import embeddings
from langchain_chroma import Chroma
import os



def get_vectorstore() -> VectorStore:
    """Создание векторного хранилища"""
    vectorstore = Chroma(
        collection_name="example_collection",
        embedding_function=embeddings,
        persist_directory="./chroma_langchain_db",  # Where to save data locally, remove if not necessary
    )
    return vectorstore
