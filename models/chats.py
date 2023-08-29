from pydantic import BaseModel


class MessageChat(BaseModel):
    question: str