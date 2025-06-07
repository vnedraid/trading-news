from langfuse import Langfuse
from langfuse.langchain import CallbackHandler
import os

LANGFUSE_URL = os.environ["LANGFUSE_URL"]
LANGFUSE_PK = os.environ["LANGFUSE_PK"]
LANGFUSE_SK = os.environ["LANGFUSE_SK"]

langfuse = Langfuse(
    secret_key=LANGFUSE_SK,
    public_key=LANGFUSE_PK,
    host=LANGFUSE_URL,
)

langfuse_handler = CallbackHandler()