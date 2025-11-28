"""
Script para testar a API do WhatsApp diretamente
Mostra a resposta completa da Meta (sucesso ou erro)
"""
import requests
import json
from dotenv import load_dotenv
import os

load_dotenv()

# Credenciais
token = os.getenv("WHATSAPP_API_TOKEN")
phone_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
to_number = "5511972856203"  # Mude aqui se quiser testar outro número

print("=" * 60)
print("TESTE DIRETO DA API DO WHATSAPP")
print("=" * 60)
print(f"\nToken: {token[:20]}...")
print(f"Phone ID: {phone_id}")
print(f"Destinatário: {to_number}")
print("\n" + "=" * 60)

# URL e headers
url = f"https://graph.facebook.com/v21.0/{phone_id}/messages"
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

# Payload do template hello_world
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

print("\n📤 Enviando requisição para a Meta...\n")

# Faz a requisição
response = requests.post(url, headers=headers, json=payload)

print(f"Status Code: {response.status_code}")
print("\n" + "=" * 60)
print("RESPOSTA COMPLETA DA API:")
print("=" * 60)

# Mostra a resposta formatada
try:
    response_json = response.json()
    print(json.dumps(response_json, indent=2, ensure_ascii=False))
    
    # Analisa a resposta
    if response.status_code == 200:
        print("\n✅ SUCESSO! A API aceitou a mensagem.")
        if "messages" in response_json:
            msg_id = response_json["messages"][0]["id"]
            print(f"ID da mensagem: {msg_id}")
    else:
        print(f"\n❌ ERRO {response.status_code}")
        if "error" in response_json:
            error = response_json["error"]
            print(f"\nCódigo do erro: {error.get('code')}")
            print(f"Mensagem: {error.get('message')}")
            print(f"Tipo: {error.get('type')}")
            if 'error_subcode' in error:
                print(f"Subcódigo: {error.get('error_subcode')}")
            
            # Link para documentação
            print(f"\n📚 Consulte: https://developers.facebook.com/docs/whatsapp/cloud-api/support/error-codes")
            
except Exception as e:
    print(f"Erro ao processar resposta: {e}")
    print(f"Resposta bruta: {response.text}")

print("\n" + "=" * 60)
