from fastapi import APIRouter, Request, HTTPException, Query, BackgroundTasks
from fastapi.responses import PlainTextResponse
import os
from dotenv import load_dotenv
from app.services.meta_handler import handle_whatsapp_event, handle_instagram_event

load_dotenv()

router = APIRouter()

VERIFY_TOKEN = os.getenv("WEBHOOK_VERIFY_TOKEN")

@router.get("/webhook")
async def verify_webhook(
    mode: str = Query(..., alias="hub.mode"),
    token: str = Query(..., alias="hub.verify_token"),
    challenge: str = Query(..., alias="hub.challenge")
):
    """
    Verificação do Webhook exigida pela Meta.
    """
    if mode == "subscribe" and token == VERIFY_TOKEN:
        print("WEBHOOK_VERIFIED")
        return PlainTextResponse(content=challenge, status_code=200)
    
    raise HTTPException(status_code=403, detail="Verification failed")


@router.post("/webhook")
async def webhook_handler(request: Request, background_tasks: BackgroundTasks):
    """
    Recebe eventos da Meta e despacha para o handler correto em background.
    """
    payload = await request.json()
    
    object_type = payload.get("object")

    if object_type == "whatsapp_business_account":
        background_tasks.add_task(handle_whatsapp_event, payload)
        return {"status": "EVENT_RECEIVED"}
    
    elif object_type == "instagram":
        background_tasks.add_task(handle_instagram_event, payload)
        return {"status": "EVENT_RECEIVED"}
    
    else:
        # Retorna 404 para eventos não suportados, conforme docs da Meta
        raise HTTPException(status_code=404, detail="Event not supported")
