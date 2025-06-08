from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_experimental.text_splitter import SemanticChunker
from langchain_text_splitters import SpacyTextSplitter
from langchain_core.documents import Document
from typing import Literal


class TextSplitter:
    def __init__(self, mode: Literal["structure", "semantic", "lenght"], **kwargs):
        match mode:
            case "structure":
                self.splitter = RecursiveCharacterTextSplitter(
                    chunk_size=kwargs.get("chunk_size", 1000),
                    overlap=kwargs.get("chunk_overlap", 0),
                )
            case "semantic":
                self.splitter = SemanticChunker(
                    embeddings=kwargs.get("embeddings", None)
                )
            case "lenght":
                self.splitter = SpacyTextSplitter(kwargs.get("chunk_size", 1000))

    def split_text(self, text: str) -> list[Document]:
        return self.splitter.split_text(text)
