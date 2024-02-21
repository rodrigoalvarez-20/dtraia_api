from pydantic import BaseModel


class RateMessage(BaseModel):
    qmessage_id: str
    amessage_id: str
    rating: int