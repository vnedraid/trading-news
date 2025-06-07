from dataclasses import dataclass
from temporalio import activity

from default_agent import llm
from langchain.prompts import ChatPromptTemplate


@dataclass
class TranslateParams:
    phrase: str
    language: str


@activity.defn
async def translate_phrase(params: TranslateParams) -> dict:
    # LangChain setup
    template = """You are a helpful assistant who translates between languages.
    Translate the following phrase into the specified language: {phrase}
    Language: {language}"""
    chat_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", template),
            ("human", "Translate"),
        ]
    )
    chain = chat_prompt | llm
    # Use the asynchronous invoke method
    return dict(
        await chain.ainvoke({"phrase": params.phrase, "language": params.language})
    )
