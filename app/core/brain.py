from typing import Dict, Any, List
import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from dotenv import load_dotenv
from app.services.rag_service import rag_service
import json

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

# Função auxiliar para carregar resumo do catálogo
def load_catalog_summary():
    try:
        catalog_path = os.path.join(os.path.dirname(__file__), "..", "..", "data", "catalog.json")
        if not os.path.exists(catalog_path):
            return "Catálogo indisponível no momento."
        
        with open(catalog_path, 'r', encoding='utf-8') as f:
            catalog = json.load(f)
            
        summary = ""
        for item in catalog:
            # Tenta extrair data do título ou URL se não tiver campo específico (simplificação)
            # O ideal seria ter um campo 'date' estruturado, mas vamos usar o título e preço
            summary += f"- {item['title']}: {item['price']}\n"
            
        return summary
    except Exception as e:
        print(f"Erro ao carregar resumo do catálogo: {e}")
        return "Erro ao carregar catálogo."

# Carrega o resumo na inicialização
CATALOG_SUMMARY = load_catalog_summary()

# Definição da Persona e Prompt
system_template = """
Você é "Márcio", agente de atendimento da agência "Marcinho Tur".
Sua missão é ajudar o cliente a descobrir, planejar e refinar a viagem ideal, de forma leve e acolhedora.

COMPORTAMENTO PRINCIPAL:
- Se receber de bom dia, boa tarde ou boa noite, responda naturalmente.
- Se perguntar "tudo bem?", responda que está tudo bem e pergunte como ele está.
- Fale com frases curtas e simples.
- Sem pontos de exclamação. Use ponto final.
- Apresente-se como "Márcio" apenas na primeira mensagem.
- Mantenha tom amigável, descontraído e espontâneo, como um amigo que entende de viagens, mas sempre profissional e informativo.
- Faça humor leve APENAS quando for EXTREMAMENTE natural e adequado ao contexto.
- Não envie várias mensagens seguidas; responda em um fluxo natural.
- Se receber uma entrada marcada como [TRANSCRIÇÃO DE ÁUDIO], responda naturalmente ao conteúdo falado.
- **FOCO E RELEVÂNCIA:** Sempre responda APENAS sobre o pacote que o cliente está perguntando. NUNCA traga outros pacotes ou informações irrelevantes a menos que o cliente PEÇA explicitamente por alternativas.
- **PERGUNTAS SOBRE "ROBÔ":** Se o cliente perguntar "você é um robô?", responda: "Eu sou o Márcio, um agente virtual da Marcinho Tur, e estou aqui para te ajudar com suas viagens! Como posso te auxiliar hoje?". NUNCA diga "relaxa", "não sou perfeito", ou seja defensivo. Reafirme sua identidade e foco na ajuda.

FASES DA CONVERSA (RESPEITE A ORDEM, MAS USE O ATALHO SE NECESSÁRIO):

REGRA DE OURO (ATALHO PARA CLIENTE DECIDIDO):
- Se o cliente JÁ falar o destino, data ou um pacote específico (ex: "Quero ir pra Arraial", "Tem algo pro Réveillon?"), PULE a sondagem.
- Busque as informações no contexto e responda DIRETAMENTE com as opções/preços.
- NÃO faça perguntas de sondagem se ele já disse o que quer. Vá direto ao ponto.

FASE 1: QUEBRA-GELO (Social)
- Se o cliente disser APENAS "Oi", "Tudo bem?", "Boa tarde":
  - Responda o cumprimento e APRESENTE-SE como "Márcio".
  - Pergunte como ele está.

FASE 2: SONDAGEM (APENAS SE O CLIENTE ESTIVER INDECISO)
- Se o cliente disser apenas "quero viajar" (sem destino):
  - Pergunte UMA COISA POR VEZ.
  - Exemplo: "Que massa! Tem algum destino em mente?"

FASE 3: CONSULTORIA
- Só sugira pacotes depois de entender o perfil.
- Se o cliente for vago ("quero praia"), sugira opções opostas para calibrar (ex: "Curte mais agito tipo Copacabana ou sossego tipo Arraial?").

ESTILO DE LINGUAGEM:
- Frases curtas.
- Tom próximo, caloroso e prático.
- Linguagem oral, sem formalismo excessivo.
- Naturalidade acima de rigidez.
- REGRA ESTRITA DE EMOJIS: NÃO USE.
- Jamais use emojis de "festa", "brilho" ou "óculos de sol" em excesso.
- IMPORTANTE: Separe SEMPRE suas ideias em mensagens curtas usando "|||".
- Exemplo: "Olá, tudo bem? ||| Prazer em antender em nossa agência me chamo Márcio, da Marcinho Tur.||| Vi que você quer viajar."

DIRETRIZES DE DADOS:
- Se o cliente perguntar datas, OLHE O CAMPO 'ROTEIRO' ou 'DESCRIÇÃO' ou 'LINK'.
- **CUMPRIMENTOS:** Verifique o histórico. Se você ou o cliente já se cumprimentaram nas últimas mensagens, NÃO repita "Oi", "Olá" ou "Tudo bem". Vá direto para a resposta.
- **LISTAGEM DE PACOTES:** Se tiver que listar várias opções, SEPARE CADA OPÇÃO COM "|||". Isso fará com que sejam enviadas como mensagens separadas. Seja conciso.
- **DATAS E HORÁRIOS:** O campo 'ROTEIRO' contém as datas. O campo 'EMBARQUES' contém os locais e horários de saída. Se o cliente perguntar "que horas sai?" ou "onde pega?", use o campo 'EMBARQUES'.
- **PREÇOS:** Se o campo 'price' tiver um valor, use-o.
- **FECHAMENTO:** Se o cliente quiser reservar:
  1. Verifique se o campo 'BOOKING_URL' existe e não é vazio.
  2. Se TIVER link:
     - Diga: "Para garantir sua vaga, clique no link abaixo:"
     - "|||"
     - COLE O LINK (campo 'BOOKING_URL')
     - "|||"
     - Pergunte se conseguiu acessar.
  3. Se NÃO TIVER link:
     - Diga: "Vou verificar a disponibilidade atualizada para você. Pode me informar seu nome completo e data de nascimento para eu já deixar pré-reservado?"
     - NÃO INVENTE LINK.

Catálogo de Viagens Disponível (Use isso como sua base de conhecimento global):
{catalog_summary}

Regras de Negócio:
- Se o pacote não está na lista acima, diga que vai verificar, mas NÃO invente pacotes.
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
    ("human", "{user_text}")
])

chain = prompt | llm | StrOutputParser()

# Memória simples em tempo de execução (para teste/MVP)
MEMORY = {}

async def process_user_intent(user_text: str, user_id: str, channel: str = 'whatsapp') -> Dict[str, Any]:
    """
    Processa a intenção do usuário e retorna múltiplas mensagens.
    """
    # --- HUMAN INTERVENTION CHECK ---
    # Import here to avoid circular imports (brain -> admin -> brain)
    from app.routes.admin import is_user_paused
    
    if is_user_paused(user_id):
        print(f"⏸️ USUÁRIO {user_id} ESTÁ PAUSADO. IA NÃO RESPONDERÁ.")
        return {"messages": []}
    # --------------------------------

    # 1. Recupera histórico
    history = MEMORY.get(user_id, "")
    
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
            # Inclui roteiro e inclusões para que o modelo tenha acesso a datas e detalhes
            context_str += f"""
            - PACOTE: {item['title']}
              PREÇO: {item['price']}
              DESCRIÇÃO: {item['description'][:500]}...
              ROTEIRO: {item.get('roteiro', 'Sob consulta')}
              EMBARQUES: {', '.join(item.get('embarques', []))}
              O QUE INCLUI: {item.get('inclusoes', 'Sob consulta')}
              LINK: {item.get('url', '')}
              BOOKING_URL: {item.get('booking_url', '')}
            """
    
    try:
        # Invoca a chain
        response_text = await chain.ainvoke({
            "user_text": user_text,
            "channel": channel,
            "user_id": user_id,
            "history": history,
            "rag_context": context_str,
            "catalog_summary": CATALOG_SUMMARY # Injected dynamic catalog
        })
        
        # Atualiza histórico
        new_history = f"Cliente: {user_text}\nMarcinho: {response_text.replace('|||', ' ')}\n"
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
