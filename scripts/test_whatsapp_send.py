import asyncio
import os
import sys

# Adiciona o diretório raiz ao path para importar 'app'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dotenv import load_dotenv
from app.services.meta_client import MetaClient

# Carrega variáveis de ambiente
load_dotenv()

async def test_send():
    print("--- Teste de Envio WhatsApp ---")
    
    # Verifica credenciais
    token = os.getenv("WHATSAPP_API_TOKEN")
    phone_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
    
    if not token or not phone_id:
        print("❌ ERRO: Credenciais não encontradas no .env")
        return

    print(f"✅ Token encontrado: {token[:10]}...")
    print(f"✅ Phone ID encontrado: {phone_id}")
    
    import sys
    
    # Pede o número de destino
    if len(sys.argv) > 1:
        to_number = sys.argv[1]
    else:
        print("\nDigite o número de destino (o mesmo que você cadastrou no painel da Meta).")
        print("Formato: 55 + DDD + Número (Ex: 5511999999999)")
        to_number = input("Número: ").strip()
    
    if not to_number:
        print("❌ Número inválido.")
        return

    client = MetaClient()
    
    print(f"\nEnviando TEMPLATE de teste para {to_number}...")
    
    # Tenta enviar mensagem de TEMPLATE (obrigatório para iniciar conversa)
    # Payload manual para garantir que seja um template
    import httpx
    url = f"https://graph.facebook.com/v21.0/{phone_id}/messages"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to_number,
        "type": "template",
        "template": {
            "name": "hello_world",
            "language": {
                "code": "en_US"
            }
        }
    }
    
    async with httpx.AsyncClient() as http_client:
        try:
            response = await http_client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            result = response.json()
            print(f"\n✅ API Response: {result}")
        except httpx.HTTPStatusError as e:
            print(f"\n❌ HTTP Error {e.response.status_code}")
            try:
                error_detail = e.response.json()
                print(f"Error Details: {error_detail}")
                if "error" in error_detail:
                    error_info = error_detail["error"]
                    print(f"\nCódigo: {error_info.get('code')}")
                    print(f"Mensagem: {error_info.get('message')}")
                    print(f"Tipo: {error_info.get('type')}")
                    print(f"Subtipo: {error_info.get('error_subcode')}")
            except:
                print(f"Response text: {e.response.text}")
            result = None
        except Exception as e:
            print(f"\n❌ Erro no envio: {e}")
            result = None
    
    with open("test_result.txt", "w", encoding="utf-8") as f:
        if result:
            print("\n✅ SUCESSO! Mensagem enviada.")
            f.write(f"SUCESSO\n{result}")
        else:
            print("\n❌ FALHA ao enviar mensagem.")
            f.write("FALHA")

if __name__ == "__main__":
    asyncio.run(test_send())
