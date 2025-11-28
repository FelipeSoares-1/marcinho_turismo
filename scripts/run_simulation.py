import asyncio
import os
from datetime import datetime
from dotenv import load_dotenv
from app.core.brain import process_user_intent
import time

load_dotenv()

# Dados reais extraídos do site (Simulando o conhecimento do agente)
REAL_PACKAGES_CONTEXT = """
DADOS ATUAIS DO SITE MARCINHOTUR.COM.BR (Use isso para responder):

1. BETO CARRERO & BALNEARIO BARRA SUL
   - Data: 28/11/2025
   - Preço: De R$599,99 por R$569,00
   - Duração: 3 dias

2. ARRAIAL DO CABO & MACAE
   - Data: 28/11/2025 e 05/12/2025
   - Preço: A partir de R$419,00
   - Duração: 3 dias

3. ILHA BELA LITORAL NORTE
   - Data: 29/11/2025
   - Preço: A partir de R$149,00
   - Duração: 2 dias

4. PORTO SEGURO BAHIA (Destaque Dezembro)
   - Data: 05/12/2025
   - Preço: A partir de R$2.699,00
   - Incluso: 04 Noites c/ Hospedagem, Aéreo Incluso, Passeio para todas as idades
   - Duração: 6 dias

5. PARATY & TRINDADE
   - Data: 05/12/2025
   - Preço: A partir de R$399,99
   - Incluso: Seguro Viagem, Café da manhã na chegada
   - Duração: 3 dias

6. COPACABANA RJ
   - Data: 13/12/2025 (R$199,99) e 03/01/2026 (R$215,00)
   - Duração: 2 dias
"""

async def run_simulation():
    output = []
    output.append("# SIMULAÇÃO DE CONVERSA REAL - Marcinho Tur")
    output.append(f"Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
    output.append("="*80 + "\n")
    
    # Injeta o contexto no prompt do sistema (simulado aqui anexando à mensagem do usuário, 
    # mas idealmente estaria no system_prompt ou RAG)
    # Para este teste, vamos assumir que o 'brain.py' já tem instruções ou vamos passar o contexto na primeira mensagem.
    
    conversation_flow = [
        "Olá, quais viagens vocês tem disponíveis para o final do ano? Queria algo com praia.",
        "Hum, esse de Porto Seguro parece interessante. O que exatamente está incluso nesse valor de 2.699?",
        "E criança paga o mesmo valor? Tenho um filho de 5 anos.",
        "Entendi. E quais as formas de pagamento? Parcelam no cartão?",
        "Gostei! Quero fechar esse pacote para mim, meu marido e meu filho. Como faço?"
    ]
    
    user_id = "cliente_simulado_01"
    channel = "whatsapp"
    
    output.append(f"## INICIANDO CONVERSA (Canal: {channel})\n")
    
    # Contexto inicial para o agente (simulando RAG)
    # Nota: O brain.py atual não recebe contexto extra dinâmico facilmente sem alterar o código,
    # então vamos ver como ele se comporta. Se ele alucinar, saberemos que precisamos integrar o catálogo.
    # Para ajudar, vou "hackear" a primeira mensagem adicionando o contexto como se fosse uma instrução do sistema oculta.
    
    first_message = True
    
    for user_msg in conversation_flow:
        output.append(f"\n👤 **Cliente:** {user_msg}\n")
        
        # Pequeno delay para realismo
        await asyncio.sleep(1.5)
        
        start_time = time.time()
        result = await process_user_intent(user_msg, user_id, channel)
        messages = result.get('messages', [])
        
        output.append(f"🤖 **Marcinho:**\n")
        for msg in messages:
            output.append(f"   {msg}\n")
            
        output.append("-" * 40)

    output.append(f"\n{'='*80}")
    output.append("\nFIM DA SIMULAÇÃO\n")
    
    # Salvar em arquivo
    filename = "simulacao_conversao.md"
    with open(filename, "w", encoding="utf-8") as f:
        f.write("\n".join(output))
    
    print(f"Simulação concluída! Veja o resultado em: {filename}")
    
    # Imprime o resultado no terminal também para o usuário ver
    print("\n" + "="*60)
    print("\n".join(output))
    print("="*60)

if __name__ == "__main__":
    asyncio.run(run_simulation())
