
import os
from langchain_core.vectorstores import VectorStore
from langchain_chroma import Chroma


from ...models import embeddings

def get_vectorstore() -> VectorStore:
    # """Создание векторного хранилища"""
    vectorstore = Chroma(
        collection_name="example_collection",
        embedding_function=embeddings,
        persist_directory="./chroma_langchain_db",  # Where to save data locally, remove if not necessary
    )
    return vectorstore
