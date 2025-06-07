from langchain_gigachat import GigaChat
from langchain_gigachat.embeddings import GigaChatEmbeddings

import os

llm = GigaChat(
    credentials=os.getenv("GIGA_KEY"),
    model="GigaChat-2-Pro", # GigaChat-2-Pro
    verify_ssl_certs=False,
    streaming=False,
)

embeddings = GigaChatEmbeddings(
    credentials=os.getenv("GIGA_KEY"),
    scope="GIGACHAT_API_PERS",
    verify_ssl_certs=False
)