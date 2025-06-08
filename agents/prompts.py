PROMPTS = {
    "summary": [
        (
            "human",
            "Напиши саммари следующей новости : {context}",
        ),
    ],
    "rag_summary": [
        (
            "human",
            "Твоя задача выаолинть следующие действия"
            "1. Запросить информацию из Базы данных для ответа на вопрос : {question}"
            "2. Удалить дублирующую информацию из полученной информации и составить саммари",
        ),
    ],
}

from langchain_core.messages import BaseMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from pydantic import BaseModel, create_model
import json
import typing as t


@t.runtime_checkable
class HasSJONShema(t.Protocol):
    def model_json_schema(self) -> dict: ...


def _get_message_type(msg):
    match msg:
        case list():
            return msg[0]
        case BaseMessage():
            return msg.type


def _get_message_content(msg):
    match msg:
        case list():
            return msg[1]
        case BaseMessage():
            return msg.content


def create_user_output_pydantic(output: dict) -> BaseModel:
    """Создает модель Pydantic по примеру JSON"""
    UserModel = create_model(
        "UserModel", **{k: (v.__class__, ...) for k, v in output.items()}
    )
    return UserModel


def get_structure_messages():
    return [
        (
            "human",
            """Вывод должен быть отформатирован как экземпляр JSON, соответствующий приведённой ниже схеме JSON.
            Например, для схемы {{"properties": {{"foo": {{"title": "Foo", "description": "список строк", "type": "array", "items": {{"type": "string"}}}}}}, "required": ["foo"]}}
            объект {{"foo": ["bar", "baz"]}} является правильно отформатированным экземпляром схемы.
            объект {{"foo": []}} является правильно отформатированным экземпляром схемы, если нам недоступна информация об ключе foo
            Объект {{"properties": {{"foo": ["bar", "baz"]}}}} плохо отформатирован.
            Объект {{"properties": {{"foo": ["bar", "baz", "" // комментарий]}}}} не является правильно отформатированным экземпляром схемы, т.к. JSON объект не должен содержать пояснения и комментарии в своем теле, кроме этого в непустой список добавлена пустая строка.
            Объект {{"properties": {{"foo": ["bar", "baz"] // комментарий}}}} не является правильно отформатированным экземпляром схемы, т.к. JSON объект не должен содержать пояснения и комментарии в своем теле.
            Ты не должен придумывать инфомрацию, если инфомрация не содержится в описании и ключ имеет значения типа строка, то верни пустую строку ```""```, если информация отсутствует и тип занчения список, то верни пустой список ```[]```
            
            Вот схема вывода:```\n {schema} \n```""",
        )
    ]


def create_chat_prompt_template(msgs):
    return ChatPromptTemplate.from_messages(msgs)


def create_user_format_message(schema: BaseModel | dict):
    """Создание сообщения для промпта с пояснением относительно формата генерации JSON"""
    match schema:
        case schema if isinstance(schema, HasSJONShema):
            schema = json.dumps(schema.model_json_schema())
        case dict():
            schema = json.dumps(schema)

    structure_message = get_structure_messages().format(schema=schema)
    return HumanMessage(content=structure_message)


def get_base_generation_messages():
    return [
        (
            "system",
            "{role}",
        ),
        MessagesPlaceholder(variable_name="messages"),
    ]


def get_generate_reflection_role_messages():
    return [
        (
            "system",
            "Напиши максимально краткую инструкцию для контроля эксперта - исполнителя."
            "В инструкции должны быть описаны критерии удовлеворительного выполнения экспертом своей работы."
            "Инструкция не должна быть длиннее 2 предложений.",
        ),
        ("human", "Роль эксперта исполнителя: {role}"),
    ]


def get_reflection_role_messages():
    return [
        (
            "system",
            "Вы начальник эксперта. Ваша задача - проверить корректность выполнения заданий пользвателя экспертом на предыдущем этапе."
            "{reflection_role}"
            "Предоставьте подробные рекомендации для исправления экспертом своей работы в стелудующем формате:"
            "`Редомендации`: ..."
            "Если существенные исправления не требуются, то ответь без дополнительного текста следущим образом:"
            "`Задача решена.`",
        ),
        MessagesPlaceholder(variable_name="messages"),
    ]


def get_initial_summary_messages():
    return [
        (
            "human",
            "Write a concise summary of the following: {context}",
        ),
    ]


def get_refine_summary_messages():
    return [
        (
            "human",
            "Produce a final summary."
            "Existing summary up to this point:"
            "{existing_answer}"
            "New context:"
            "------------"
            "{context}"
            "------------"
            "Given the new context, refine the original summary.",
        ),
    ]
