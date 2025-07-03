from typing import Optional
from pydantic import BaseModel


class ChatMessageDto(BaseModel):
    message: str
    chat_id: str
    persona_id: str