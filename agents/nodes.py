from langchain_core.output_parsers import StrOutputParser
from langchain_core.output_parsers import JsonOutputParser
from langgraph.graph import END, START
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.prompts import MessagesPlaceholder
from langchain_core.messages import AIMessage
from langchain_core.messages import HumanMessage
import logging
import json
from langgraph.types import Command
from copy import deepcopy
from .prompts import _get_message_type, _get_message_content
from .prompts import *


def build_simple_chain(llm, prompt, output: None | BaseModel | str = None):
    """
    Создание простой цепочки Prompt -> LLM -> Parser(есть указан output)
    Если указана схема с форматом ответа или пример словаря, то цепочка при вызове будет отдавать объект по схеме,
    если указана строка, например 'string', то - AIMessage.content,
    если ничего не указано, то - AIMessage со всеми метаданными.
    """
    # TODO  можно переписать через декоратор functools.singledispatch
    match output:
        case None:
            return prompt | llm
        case dict():  # словаь с форматом ответа
            output = create_user_output_pydantic(output)
            return prompt | llm | JsonOutputParser(pydantic_object=output)
        case schema if isinstance(schema, HasSJONShema):  # схема с форматом ответа
            return prompt | llm | JsonOutputParser(pydantic_object=output)
        case str():  # просто строка (AIMessage.content без прочих данных)
            return prompt | llm | StrOutputParser()


def reduce_docs_node(self, state):
    documents = state["documents"]
    match documents:
        case str():
            return {"messages": ["human", self.role.format(context=documents)]}
        case _:
            docs_content = "\n".join(doc.page_content for doc in documents)
            return {"messages": ["human", self.role.format(context=docs_content)]}


def structure_generation_node(self, state):
    messages = deepcopy(state["messages"])

    prompt_messages = get_base_generation_messages()
    prompt = ChatPromptTemplate.from_messages(prompt_messages)
    prompt.append(self.output_message)
    prompt.partial(role=self.role)

    chain = build_simple_chain(self.llm, prompt, self.UserModel)

    result = chain.invoke(messages)
    return {
        "messages": [AIMessage(content=json.dumps(result))],
        "structure_output": result,
    }


def generation_node(self, state):
    messages = deepcopy(state["messages"])

    prompt_messages = get_base_generation_messages(self.role)
    prompt = ChatPromptTemplate.from_messages(prompt_messages)

    chain = build_simple_chain(self.llm, prompt)

    return {"messages": [chain.invoke(messages)]}


def generate_reflection_role(llm: str, role: str):
    prompt_messages = get_generate_reflection_role_messages()
    prompt = ChatPromptTemplate.from_messages(prompt_messages)

    chain = build_simple_chain(llm, prompt, "string")

    return chain.invoke({"role": role})


def reflection_node(self, state):
    messages = deepcopy(state["messages"])

    prompt_messages = get_reflection_role_messages()
    prompt = ChatPromptTemplate.from_messages(prompt_messages)
    prompt.partial(reflection_role=self.reflection_role)

    chain = build_simple_chain(self.llm, prompt)

    cls_map = {"ai": HumanMessage, "human": AIMessage}
    translated = [messages[0]] + [
        cls_map[_get_message_type(msg)](content=_get_message_content(msg))
        for msg in messages[1:]
        if _get_message_type(msg) != "tool"
    ]
    result = chain.invoke(translated)

    return {"messages": [HumanMessage(content=result.content)]}


def get_answer_node(self, state):
    messages = deepcopy(state["messages"])

    messages.reverse()
    if self.reflection:
        for i, msg in enumerate(messages):
            if msg.type == "ai":
                self._last_message_index = -i - 1
                break
    updates = {"answer": state["messages"][self._last_message_index]}
    if self.cut_message_history:
        to = None if self._last_message_index + 1 == 0 else self._last_message_index + 1
        updates.update(
            {"messages": {"type": "keep", "from": self._last_message_index, "to": to}}
        )
    return updates


def generate_initial_summary_node(self, state):
    messages = get_initial_summary_messages()
    prompt = ChatPromptTemplate.from_messages(messages)
    chain = build_simple_chain(self.llm, prompt, "string")
    summary = chain.invoke(
        {"context": state["documents"][0].page_content},
    )
    return {"summary": summary, "index": 1}


def refine_summary_node(self, state):
    messages = get_refine_summary_messages()
    prompt = ChatPromptTemplate.from_messages(messages)
    chain = build_simple_chain(self.llm, prompt) | StrOutputParser()
    content = state["documents"][state["index"]]
    summary = chain.invoke(
        {"existing_answer": state["summary"], "context": content},
    )
    return {"summary": summary, "index": state["index"] + 1}


def supervisor_node(self, state) -> Command:
    messages = state["messages"]
    # TODO вынести форматирование в раздел промптов
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                self.supervisor_role_start,
            ),
            MessagesPlaceholder(variable_name="messages"),
            (
                "human",
                self.supervisor_role_end,
            ),
        ]
    )
    chain = build_simple_chain(self.llm, prompt) | StrOutputParser()
    goto = chain.invoke(messages)
    # TODO можно вынести логику в дугу с условием и кбрать goto
    if goto == "FINISH":
        goto = END
    return Command(goto=goto, update={"next": goto})
