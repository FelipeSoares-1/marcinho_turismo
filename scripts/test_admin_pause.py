import asyncio
import sys
import os
from fastapi.testclient import TestClient
from app.core.brain import process_user_intent

# Add project root to path
sys.path.append(os.getcwd())

from main import app

client = TestClient(app)

async def test_pause_flow():
    user_id = "test_pause_user"
    channel = "whatsapp"
    
    print(f"--- 1. Testando conversa NORMAL com {user_id} ---")
    # 1. Normal interaction
    result = await process_user_intent("Oi, tudo bem?", user_id, channel)
    print(f"Bot respondeu: {result['messages']}")
    if not result['messages']:
        print("❌ FALHA: Bot deveria ter respondido.")
        return

    print(f"\n--- 2. PAUSANDO usuário via API ---")
    # 2. Pause user
    response = client.post(f"/admin/api/pause?user_id={user_id}&pause=true")
    print(f"Status API: {response.status_code}")
    print(f"Response API: {response.json()}")
    
    print(f"\n--- 3. Testando conversa PAUSADA ---")
    # 3. Paused interaction
    result = await process_user_intent("Tem alguém aí?", user_id, channel)
    print(f"Bot respondeu: {result['messages']}")
    if result['messages']:
        print("❌ FALHA: Bot NÃO deveria ter respondido.")
    else:
        print("✅ SUCESSO: Bot ficou mudo conforme esperado.")

    print(f"\n--- 4. RETOMANDO usuário via API ---")
    # 4. Resume user
    response = client.post(f"/admin/api/pause?user_id={user_id}&pause=false")
    
    print(f"\n--- 5. Testando conversa RETOMADA ---")
    # 5. Resumed interaction
    result = await process_user_intent("Voltou?", user_id, channel)
    print(f"Bot respondeu: {result['messages']}")
    if not result['messages']:
        print("❌ FALHA: Bot deveria ter voltado a responder.")
    else:
        print("✅ SUCESSO: Bot voltou a responder.")

if __name__ == "__main__":
    asyncio.run(test_pause_flow())
