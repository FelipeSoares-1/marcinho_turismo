import asyncio
import os
from fastapi.testclient import TestClient
from main import app
from app.services.meta_handler import handle_whatsapp_event, handle_instagram_event

# Configurar variável de ambiente para teste
os.environ["WEBHOOK_VERIFY_TOKEN"] = "meu_token_secreto_123"

client = TestClient(app)

def test_webhook_verification():
    print("\n--- Testando Verificação do Webhook (GET) ---")
    response = client.get("/webhook", params={
        "hub.mode": "subscribe",
        "hub.verify_token": "meu_token_secreto_123",
        "hub.challenge": "CHALLENGE_ACCEPTED"
    })
    if response.status_code == 200 and response.text == "CHALLENGE_ACCEPTED":
        print("✅ Verificação do Webhook: SUCESSO")
    else:
        print(f"❌ Verificação do Webhook: FALHA (Status: {response.status_code}, Body: {response.text})")

def test_whatsapp_event():
    print("\n--- Testando Evento WhatsApp (POST) ---")
    payload = {
        "object": "whatsapp_business_account",
        "entry": [{
            "changes": [{
                "value": {
                    "messages": [{
                        "from": "5511999999999",
                        "text": {"body": "Olá, gostaria de um pacote para Disney"}
                    }]
                }
            }]
        }]
    }
    response = client.post("/webhook", json=payload)
    if response.status_code == 200:
        print("✅ Evento WhatsApp: SUCESSO")
    else:
        print(f"❌ Evento WhatsApp: FALHA (Status: {response.status_code})")

def test_instagram_dm_event():
    print("\n--- Testando Evento Instagram DM (POST) ---")
    payload = {
        "object": "instagram",
        "entry": [{
            "messaging": [{
                "sender": {"id": "123456789"},
                "message": {"text": "Qual o valor da passagem?"}
            }]
        }]
    }
    response = client.post("/webhook", json=payload)
    if response.status_code == 200:
        print("✅ Evento Instagram DM: SUCESSO")
    else:
        print(f"❌ Evento Instagram DM: FALHA (Status: {response.status_code})")

def test_instagram_comment_event():
    print("\n--- Testando Evento Instagram Comentário (POST) ---")
    payload = {
        "object": "instagram",
        "entry": [{
            "changes": [{
                "field": "comments",
                "value": {
                    "from": {"id": "987654321"},
                    "text": "Eu quero saber o preço!"
                }
            }]
        }]
    }
    response = client.post("/webhook", json=payload)
    if response.status_code == 200:
        print("✅ Evento Instagram Comentário: SUCESSO")
    else:
        print(f"❌ Evento Instagram Comentário: FALHA (Status: {response.status_code})")

if __name__ == "__main__":
    try:
        test_webhook_verification()
        test_whatsapp_event()
        test_instagram_dm_event()
        test_instagram_comment_event()
    except ImportError:
        print("❌ Erro: Dependências (fastapi, httpx) não encontradas. Instale-as para rodar o teste.")
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
