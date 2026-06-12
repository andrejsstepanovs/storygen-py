from pydantic import BaseModel
from typing import List
from langchain_openai import ChatOpenAI
from storygen.config import settings

llm = ChatOpenAI(
    base_url=settings.llm_base_url,
    api_key=settings.llm_api_key,
    model=settings.model_name,
    temperature=0.7
)

class StringListOutput(BaseModel):
    items: List[str]

try:
    chain = llm.with_structured_output(StringListOutput, method="json_mode")
    res = chain.invoke("Give me 2 colors. Output as JSON with key 'items'.")
    print(res)
except Exception as e:
    print(f"Failed with json_mode: {e}")

try:
    chain = llm.with_structured_output(StringListOutput, method="function_calling")
    res = chain.invoke("Give me 2 colors. Output as JSON with key 'items'.")
    print(res)
except Exception as e:
    print(f"Failed with function_calling: {e}")

