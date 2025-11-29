import asyncio
import os
import sys
import io
from dotenv import load_dotenv
from app.core.brain import process_user_intent

# Forçar UTF-8 no Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

load_dotenv()

async def test_brain():
    print("--- Testando Cérebro (Simulação Real) ---")
    
    # Verifica se tem chave
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("❌ ERRO: Configure a GOOGLE_API_KEY no arquivo .env antes de testar.")
        return

    # Simulação de conversa contínua
    user_id = "test_user_123"
    
    conversation = [
        "Oi, tudo bem?",
        "Quero saber sobre o Réveillon em Arraial do Cabo",
        "Qual o horário de saída?",
        "Me manda o link de pagamento"
    ]

    print(f"--- Iniciando Conversa com {user_id} ---")
    for text in conversation:
        print(f"\n👤 Usuário: {text}")
        result = await process_user_intent(text, user_id, "whatsapp")
        
        for msg in result["messages"]:
            print(f"🤖 Marcinho: {msg}")
        
        if result.get("images"):
            print(f"📸 [IMAGEM ENVIADA]: {result['images'][0]}")

if __name__ == "__main__":
    asyncio.run(test_brain())
