
import os
from langchain_postgres.vectorstores import PGVector
from langchain_core.vectorstores import VectorStore
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams


from ...models import embeddings

def get_vectorstore() -> VectorStore:
    # """Создание векторного хранилища"""
    COLLECTION_NAME = "user_docs"
    """PGVector store"""
    URI = os.environ["PGVECTOR_URI"]

    vectorstore = PGVector(
        embeddings=embeddings,
        collection_name=COLLECTION_NAME,
        connection=URI,
        use_jsonb=True,
    )
    
    # client = QdrantClient(url="http://localhost:6333")

    # client.create_collection(
    #     collection_name=COLLECTION_NAME,
    #     vectors_config=VectorParams(size=3072, distance=Distance.COSINE),
    # )

    # vectorstore = QdrantVectorStore(
    #     client=client,
    #     collection_name="COLLECTION_NAME",
    #     embedding=embeddings,
    # )
    return vectorstore
