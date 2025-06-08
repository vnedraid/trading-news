from langchain_core.documents import Document
from langchain_unstructured import UnstructuredLoader


class DocumentLoader(UnstructuredLoader):
    def __init__(self, **kwargs):
        """
        # TODO написать примеры
        chunking_strategy="basic",
        max_characters=1000000,
        """
        super().__init__(**kwargs)

    def __call__(self) -> list[Document]:
        docs = []
        for doc in self.lazy_load():
            docs.append(doc)
        return docs
