import asyncio
import os
import sys
import io
from dotenv import load_dotenv
from app.core.brain import process_user_intent

import sys
import io

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

    scenarios = [
        ("Olá, quais as próximas viagens disponíveis para novembro?", "whatsapp"),
        ("Me conta mais sobre esse de Arraial do Cabo. O que está incluso? E o preço?", "instagram_dm"),
        ("Estou em dúvida entre Porto Seguro e Beto Carrero. Qual é mais barato? O de Porto Seguro tem avião?", "whatsapp"),
        ("Quero fechar o pacote de Campos do Jordão para duas pessoas. Como funciona?", "instagram_dm"),
        ("Vocês fazem pacote para a Disney? Quanto custa em média?", "whatsapp"),
        ("O pacote de Ilha Bela é só transporte ou tem hotel também? E aceita criança?", "instagram_comment")
    ]

    for text, channel in scenarios:
        print(f"\n👤 Usuário ({channel}): {text}")
        result = await process_user_intent(text, "cliente_real_01", channel)
        print(f"🤖 Marcinho: {result['response_text']}")

if __name__ == "__main__":
    asyncio.run(test_brain())
