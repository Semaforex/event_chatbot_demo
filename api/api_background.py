from structs.chat_message_dto import ChatMessageDto
from structs.return_model import ReturnModel
from services.message_processing_service import process_message_service
from dotenv import load_dotenv
load_dotenv(override=True)

import asyncio
import logging
import httpx
import os

logger = logging.getLogger("api_background")

async def send_webhook_response(webhook_url: str, api_response: ReturnModel):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(webhook_url, json=api_response)
            logger.info(f"Webhook response: {response.status_code}, {response.content}")
            response.raise_for_status()
        except httpx.RequestError as exc:
            logger.error(f"An error occurred while requesting {exc.request.url!r}.")
        except httpx.HTTPStatusError as exc:
            logger.error(
                f"Error response {exc.response.status_code} while requesting {exc.request.url!r}."
            )


async def process_chat_message(input: ChatMessageDto):
    loop = asyncio.get_event_loop()
    
    result = await loop.run_in_executor(
        None, process_message_service, input
        )

    await send_webhook_response(
        os.getenv("WEBHOOK_URL") or "",
        result
    )
