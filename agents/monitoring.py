from langfuse import Langfuse
from langchain_core.callbacks import BaseCallbackHandler


class LangfuseCallbackHandler(BaseCallbackHandler):
    def __init__(self, langfuse_client):
        self.langfuse = langfuse_client
        self.run_inline = True  # or False depending on your needs


langfuse_client = Langfuse(
    secret_key="sk-lf-ad4f7aa9-b61e-45cb-b1a3-c3797d9fbd3b",
    public_key="pk-lf-6cd8b044-cf96-486d-8f8d-7728466de368",
    host="https://cloud.langfuse.com",
)

langfuse_handler = LangfuseCallbackHandler(langfuse_client)
