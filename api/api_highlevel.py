from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks

from structs.chat_message_dto import ChatMessageDto
from api.api_background import process_chat_message

load_dotenv(override=True)
router = APIRouter()

@router.post("/async")
async def process_message_from_chat(input: ChatMessageDto, background_tasks: BackgroundTasks):
    # process a chat message from the frontend in the background.
    
    background_tasks.add_task(process_chat_message, input)
    
    return {"status": "sucess"}