
import os
from langchain_gigachat import GigaChat
from langchain_gigachat.embeddings import GigaChatEmbeddings
from yandex_cloud_ml_sdk import YCloudML
from langchain_openai import ChatOpenAI

sdk = YCloudML(
    folder_id=os.getenv("YC_FOLDER_ID"), 
    auth=os.getenv("YC_API_KEY")
)

# llm = sdk.models.completions("yandexgpt", model_version="rc").langchain()
# llm = GigaChat(
#     credentials=os.getenv("GIGA_KEY"),
#     model="GigaChat-2-Max",  # GigaChat-2-Pro
#     verify_ssl_certs=False,
#     streaming=False,
# )

llm = ChatOpenAI(
  api_key=os.getenv("OPENROUTER_API_KEY"),
  base_url=os.getenv("OPENROUTER_BASE_URL"),
  model="openai/gpt-4o-mini",
)

embeddings = GigaChatEmbeddings(
    model="EmbeddingsGigaR",
    credentials=os.getenv("GIGA_KEY"), scope="GIGACHAT_API_PERS", verify_ssl_certs=False
)
