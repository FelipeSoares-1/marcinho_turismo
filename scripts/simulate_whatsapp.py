import asyncio
import sys
import os

# Adiciona o diretório raiz ao path para importar 'app'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.brain import process_user_intent

# Cores para o terminal
GREEN = "\033[92m"
CYAN = "\033[96m"
YELLOW = "\033[93m"
RESET = "\033[0m"

async def simulate_conversation():
    print(f"{YELLOW}--- SIMULADOR DO MARCINHO (Modo de Demonstração) ---{RESET}")
    print("Este script testa a inteligência do bot sem depender do WhatsApp.")
    print("Digite 'sair' para encerrar.\n")
    
    user_id = "demo_user_123"
    
    while True:
        user_input = input(f"{CYAN}Você: {RESET}")
        
        if user_input.lower() in ["sair", "exit", "quit"]:
            break
            
        print(f"{YELLOW}Marcinho está digitando...{RESET}")
        
        try:
            # Chama a mesma função que o Webhook chama
            result = await process_user_intent(user_input, user_id, "whatsapp_simulado")
            
            messages = result.get("messages", [])
            
            for msg in messages:
                print(f"{GREEN}Marcinho: {msg}{RESET}")
                
        except Exception as e:
            print(f"❌ Erro: {e}")

if __name__ == "__main__":
    # Configura o loop de eventos para Windows
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        
    asyncio.run(simulate_conversation())
