from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field, WithJsonSchema, create_model
from langchain_core.tools import tool


@tool
def parse_structure_outputs(
    input_string: str, 
    output_json_example: dict
    ) -> dict:
    "Извлекает данные из строки по предоставленному шаблону словаря"
    tool_call_id = ""
    UserModel = create_model(
        "UserModel", **{k: (v.__class__, ...) for k, v in output_json_example.items()}
    )
    parser = JsonOutputParser(pydantic_object=UserModel)
    return parser.invoke(input_string)
