from .load_content import load_content
from .reduce_documents import reduce_documents
from .retrive_documents import retrive_documents
from .store_documents import store_documents

TOOLS = {
    "load_content": load_content,
    "reduce_documents": reduce_documents,
    "retrive_documents": retrive_documents,
    "store_documents": store_documents,
}


def get_tools(names: list) -> list:
    return [TOOLS[tool] for tool in TOOLS if tool in names]
