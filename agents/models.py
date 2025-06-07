
import os
from langchain_gigachat import GigaChat
from langchain_gigachat.embeddings import GigaChatEmbeddings
from yandex_cloud_ml_sdk import YCloudML

sdk = YCloudML(
    folder_id=os.getenv("YC_FOLDER_ID"), 
    auth=os.getenv("YC_API_KEY")
)

# llm = sdk.models.completions("yandexgpt", model_version="rc").langchain()
llm = GigaChat(
    credentials=os.getenv("GIGA_KEY"),
    model="GigaChat-2-Pro",  # GigaChat-2-Pro
    verify_ssl_certs=False,
    streaming=False,
)

embeddings = GigaChatEmbeddings(
    model="EmbeddingsGigaR",
    credentials=os.getenv("GIGA_KEY"), scope="GIGACHAT_API_PERS", verify_ssl_certs=False
)
