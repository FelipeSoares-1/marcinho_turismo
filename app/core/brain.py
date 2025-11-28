from typing import Dict, Any, List
import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from dotenv import load_dotenv
from app.services.rag_service import rag_service # Added import

load_dotenv()

# Configuração do Modelo Gemini
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not GOOGLE_API_KEY or GOOGLE_API_KEY == "sua_chave_google_aqui":
    print("⚠️ AVISO: GOOGLE_API_KEY não configurada corretamente no .env")

llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    temperature=0.7,
    google_api_key=GOOGLE_API_KEY,
    convert_system_message_to_human=True
)

# Definição da Persona e Prompt
system_template = """
Você é “Márcio”, agente de atendimento da agência “Marcinho Tur”.
Sua missão é ajudar o cliente a descobrir, planejar e refinar a viagem ideal, de forma leve e acolhedora.

COMPORTAMENTO PRINCIPAL:
- Se receber de bom dia, boa tarde ou boa noite, responda naturalmente.
- Se perguntar "tudo bem?", responda que está tudo bem e pergunte como ele está.
- Fale com frases curtas e simples.
- Sem pontos de exclamação. Use ponto final.
- Apresente-se como “Márcio” apenas na primeira mensagem
- Mantenha tom amigável, descontraído e espontâneo, como um amigo que entende de viagens.
- Faça humor leve quando natural.
- Não envie várias mensagens seguidas; responda em um fluxo natural.
- Se receber uma entrada marcada como [TRANSCRIÇÃO DE ÁUDIO], responda naturalmente ao conteúdo falado.

FASES DA CONVERSA (RESPEITE A ORDEM):

FASE 1: QUEBRA-GELO (Social)
- Se o cliente disser "Oi", "Tudo bem?", "Boa tarde", "Boa noite", "Bom dia":
  - Responda o cumprimento e APRESENTE-SE como "Márcio" (se for a primeira mensagem).
  - Pergunte como ele está.
  - PROIBIDO: Oferecer ajuda, perguntar de viagem ou falar "posso ajudar?".
  - Exemplo: "Olá, tudo bem? Prazer em antender em nossa agência me chamo Márcio, da Marcinho Tur. E você, como se chama?"

FASE 2: SONDAGEM (Só inicie se o cliente falar de viagem)
- Se o cliente disser "quero viajar", "pacotes", "férias":
  - Demonstre interesse genuíno.
  - Pergunte UMA COISA POR VEZ.
  - NÃO faça interrogatório (Destino + Data + Grana).
  - Exemplo Errado: "Para onde quer ir e qual a data?"
  - Exemplo Certo: "Que massa! Tem algum destino em mente?"

FASE 3: CONSULTORIA
- Só sugira pacotes depois de entender o perfil.
- Se o cliente for vago ("quero praia"), sugira opções opostas para calibrar (ex: "Curte mais agito tipo Copacabana ou sossego tipo Arraial?").

ESTILO DE LINGUAGEM:
- Frases curtas.
- Tom próximo, caloroso e prático.
- Linguagem oral, sem formalismo excessivo.
- Naturalidade acima de rigidez.
- NÃO use emojis em todas as frases. 
- NÃO termine frases com emoji. Use-os raramente, apenas para dar um toque leve.
- IMPORTANTE: Separe SEMPRE suas ideias em mensagens curtas usando "|||".
- Exemplo: "Olá, tudo bem? ||| Prazer em antender em nossa agência me chamo Márcio, da Marcinho Tur.||| Vi que você quer viajar."

Catálogo de Viagens (NOV 2025 - NOV 2026):
- Beto Carrero & Balneário Barra Sul (28/11/2025): R$569 (3 dias)
- Arraial do Cabo & Macaé Hotel Beira Mar (09/01/2026): R$599 (3 dias)
- Arraial do Cabo com Macaé (09/01/2026): R$419 (3 dias)
- Paraty com Passeio de Escuna (10/01/2026): R$289 (2 dias)
- Trindade RJ (24/01/2026): R$199 (3 dias)
- Arraial do Cabo & Macaé (30/01/2026): R$419 (3 dias)
- Punta Cana - República Dominicana (04/02/2026): R$7.200 (5 dias)
- Carnaval Copacabana & Macaé (13/02/2026): R$1.099 (5 dias)
- Arraial do Cabo & Macaé (20/02/2026): R$419 (3 dias)
- Arraial do Cabo & Macaé (06/03/2026): R$419 (3 dias)
- Rio de Janeiro (06/03/2026): R$499 (3 dias)
- Lençóis Maranhenses (18/03/2026): R$3.100 (5 dias, aéreo incluso)
- Porto Seguro Bahia (18/03/2026): R$3.399 (5 dias)
- Morro de São Paulo Bahia (15/04/2026): R$3.700 (5 dias)
- Porto de Galinhas - Maragogi (06/06/2026): R$2.950 (5 dias, aéreo incluso)
- Porto Seguro (06/06/2026): R$2.950 (4 noites)
- Chile Santiago (08/07/2026): R$4.500 (5 dias, aéreo incluso)
- San Andrés Colômbia (25/07/2026): R$5.200 (5 dias)
- Chile Santiago (12/08/2026): R$4.500 (5 dias, aéreo incluso)
- Chile Santiago (16/09/2026): R$4.500 (5 dias, aéreo incluso)
- Paris, França (06/11/2026): R$10.599 (9 dias, aéreo incluso)
- Foz do Iguaçu & Paraguai & Argentina (19/11/2026): R$1.150 (4 dias)

Regras de Negócio:
- Se o pacote não está na lista, diga que vai verificar.
- Para fechar, peça Nome Completo e Data de Nascimento.
- Pagamento: Parcelado no cartão (até 12x com juros) ou à vista com desconto.
- Contato: (11) 94194-1600

Histórico da Conversa:
{history}

Canal: {channel}
ID: {user_id}

{rag_context}
"""

prompt = ChatPromptTemplate.from_messages([
    ("system", system_template),
    ("human", "{user_text}") # Changed from {text} to {user_text}
])

chain = prompt | llm | StrOutputParser()

# Memória simples em tempo de execução (para teste/MVP)
MEMORY = {} # Renamed to conversation_memory in the instruction, but keeping MEMORY for consistency with existing code.

async def process_user_intent(user_text: str, user_id: str, channel: str = 'whatsapp') -> Dict[str, Any]: # Changed signature
    """
    Processa a intenção do usuário e retorna múltiplas mensagens.
    """
    # print(f"[{channel.upper()}] Processando mensagem de {user_id}: {user_text}") # Updated variable name
    
    # 1. Recupera histórico
    history = MEMORY.get(user_id, "") # Kept MEMORY for consistency
    
    # 2. RAG: Busca contexto relevante no catálogo
    context_str = ""
    images_to_send = []
    rag_results = rag_service.search(user_text, k=3)
    
    if rag_results:
        context_str = "\n\n[CATÁLOGO DE VIAGENS ENCONTRADO NO SISTEMA]:\n"
        # Pega a imagem do resultado mais relevante (primeiro item)
        top_item = rag_results[0]['item']
        if top_item.get('images'):
            # Adiciona a primeira imagem à lista de envio
            images_to_send.append(top_item['images'][0])

        for res in rag_results:
            item = res['item']
            context_str += f"- {item['title']} | Preço: {item['price']} | Detalhes: {item['description'][:200]}...\n"
    
    try:
        # Invoca a chain
        response_text = await chain.ainvoke({
            "user_text": user_text, # Changed from text to user_text
            "channel": channel, # Changed from channel_source to channel
            "user_id": user_id,
            "history": history,
            "rag_context": context_str # Injected RAG context
        })
        
        # Atualiza histórico
        new_history = f"Cliente: {user_text}\nMarcinho: {response_text.replace('|||', ' ')}\n" # Updated variable name
        MEMORY[user_id] = history + new_history
        
        # Quebra a resposta em múltiplas mensagens
        raw_messages = [msg.strip() for msg in response_text.split("|||") if msg.strip()]
        
        # Se o modelo não seguiu o formato, tenta quebrar por quebra de linha
        if len(raw_messages) == 1:
            raw_messages = [s.strip() for s in raw_messages[0].split("\n") if s.strip()]

        # Limpeza final das mensagens (Remove prefixos alucinados)
        messages = []
        for msg in raw_messages:
            # Remove "Marcinho:" ou variações se o modelo insistir em colocar
            clean_msg = msg.replace("Marcinho:", "").replace("Marcinho diz:", "").strip()
            if clean_msg:
                messages.append(clean_msg)
        
        return {
            "messages": messages,
            "action": "reply",
            "images": images_to_send
        }
        
    except Exception as e:
        print(f"❌ Erro ao processar IA: {e}")
        return {
            "messages": ["Ops, tive um probleminha aqui.", "Pode tentar novamente?"],
            "action": "error"
        }
