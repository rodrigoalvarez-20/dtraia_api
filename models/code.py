from pydantic import BaseModel

class CodeExecution(BaseModel):
    code_fragments: list[str]