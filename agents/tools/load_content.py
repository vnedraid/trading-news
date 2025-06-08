from langchain_core.tools import tool
from langchain_core.documents import Document
from .scripts.loader import DocumentLoader
from typing import List


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
        return {"documents": documents}
    except Exception as e:
        raise e
