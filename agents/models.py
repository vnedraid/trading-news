import os
from langchain_gigachat.embeddings import GigaChatEmbeddings
from langchain_openai import ChatOpenAI


llm = ChatOpenAI(
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url=os.getenv("OPENROUTER_BASE_URL"),
    model="openai/gpt-4o-mini",
)

embeddings = GigaChatEmbeddings(
    model="EmbeddingsGigaR",
    credentials=os.getenv("GIGA_KEY"),
    scope="GIGACHAT_API_PERS",
    verify_ssl_certs=False,
)
