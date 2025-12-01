import os
import json
from typing import Dict, Any, List
from datetime import datetime
import pytz  # Necessário para horário do Brasil

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from dotenv import load_dotenv

# Tenta importar o serviço de RAG (Garanta que esse arquivo existe no seu projeto)
try:
    from app.services.rag_service import rag_service
    RAG_AVAILABLE = True
except ImportError:
    print("⚠️ AVISO: rag_service não encontrado. O bot rodará sem memória de longo prazo.")
    RAG_AVAILABLE = False

# Carrega variáveis de ambiente
load_dotenv()

# --- CONFIGURAÇÃO DO MODELO ---
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not GOOGLE_API_KEY:
    print("❌ ERRO CRÍTICO: GOOGLE_API_KEY não encontrada no .env")

# Configuração do Gemini (Usando Flash para velocidade)
llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash", # Ou 'gemini-1.5-flash' dependendo da disponibilidade
    temperature=0.4, # Baixei a temperatura para ele ser mais "sério" e consistente
    google_api_key=GOOGLE_API_KEY,
    convert_system_message_to_human=True
)

# --- FUNÇÕES AUXILIARES ---

def get_time_greeting() -> str:
    """Calcula a saudação correta baseada no horário de Brasília."""
    try:
        tz = pytz.timezone('America/Sao_Paulo')
        now = datetime.now(tz)
        
        if 5 <= now.hour < 12:
            return "Bom dia"
        elif 12 <= now.hour < 18:
            return "Boa tarde"
        else:
            return "Boa noite"
    except Exception:
        return "Olá" # Fallback caso dê erro no timezone

def load_catalog_summary():
    """Carrega um resumo simples do catálogo para contexto geral."""
    try:
        # Ajuste o caminho conforme sua estrutura de pastas
        catalog_path = os.path.join(os.path.dirname(__file__), "..", "..", "data", "catalog.json")
        
        if not os.path.exists(catalog_path):
            return "Resumo do catálogo indisponível no momento."
        
        with open(catalog_path, 'r', encoding='utf-8') as f:
            catalog = json.load(f)
            
        summary = ""
        for item in catalog:
            # Cria uma lista simples: Nome - Preço
            summary += f"- {item.get('title', 'Pacote')}: {item.get('price', 'Sob consulta')}\n"
            
        return summary
    except Exception as e:
        print(f"Erro ao carregar resumo do catálogo: {e}")
        return "Erro ao carregar catálogo."

# Carrega o catálogo na inicialização
CATALOG_SUMMARY = load_catalog_summary()

# --- PROMPT DO SISTEMA (CÉREBRO) ---

system_template = """Você é o Márcio, da Marcinho Turismo.

INSTRUÇÕES DE INÍCIO DE CONVERSA:
1. SAUDAÇÃO: Use a saudação '{time_greeting}' **APENAS** na primeira mensagem ou se o cliente cumprimentar. Se a conversa já estiver fluindo, vá direto ao ponto.
2. IDENTIDADE: Apresente-se como "Márcio" se for o início da conversa.
3. NOME DO CLIENTE: Se o nome do cliente não estiver no histórico, pergunte educadamente com quem está falando antes de prosseguir.

DIRETRIZES ESTRITAS DE COMPORTAMENTO:
- ZERO EMOJIS: É estritamente proibido usar emojis. Mantenha o visual limpo e profissional.
- TOM DE VOZ: Seja sério, educado, prestativo e paciente.
- RESPOSTAS CURTAS: O WhatsApp é um chat rápido. Não envie blocos gigantes. Se tiver muita informação, pergunte se o cliente quer saber mais detalhes antes de mandar tudo.
- FLUXO DE VENDAS: Não vomite o roteiro inteiro. Dê um 'petisco' (ex: preço e o que inclui) e pergunte: 'Quer ver o roteiro dia a dia?'
- LINKS E PAGAMENTOS: Ao enviar links, envie APENAS a URL pura.
  - NÃO use formatação Markdown (não faça [texto](url)).
  - NÃO coloque entre crases.
  - Exemplo correto: https://marcinhotur.com.br/pagamento

- SEPARADOR DE MENSAGENS: Se precisar enviar blocos de texto separados (ex: explicar o pacote primeiro e depois mandar o preço), use EXATAMENTE "|||" para que o sistema divida as mensagens no WhatsApp.

CONTEXTO GERAL DA AGÊNCIA:
{catalog_summary}

CONTEXTO ESPECÍFICO ENCONTRADO NO BANCO DE DADOS (RAG):
{rag_context}

HISTÓRICO DA CONVERSA:
{history}

SAUDAÇÃO SUGERIDA: {time_greeting}
PERGUNTA ATUAL DO CLIENTE:
{user_text}
"""

prompt = ChatPromptTemplate.from_template(system_template)

# Cria a chain (Corrente de pensamento)
chain = prompt | llm | StrOutputParser()

# Memória volátil (Dicionário simples para teste/MVP)
# Nota: Em produção, substituir por Redis ou Banco de Dados
MEMORY = {}

# --- FUNÇÃO PRINCIPAL ---

async def process_user_intent(user_text: str, user_id: str, channel: str = 'whatsapp') -> Dict[str, Any]:
    """
    Processa a mensagem do usuário, consulta o RAG e gera resposta via Gemini.
    """
    
    # 1. Verifica intervenção humana (Pause)
    try:
        from app.routes.admin import is_user_paused
        if is_user_paused(user_id):
            print(f"⏸️ USUÁRIO {user_id} PAUSADO. IA SILENCIADA.")
            return {"messages": []}
    except ImportError:
        pass # Ignora se não tiver o módulo de admin ainda

    # 2. Recupera histórico
    history = MEMORY.get(user_id, "")
    
    # 3. Calcula saudação (Bom dia/tarde/noite)
    current_greeting = get_time_greeting()
    
    # 4. RAG: Busca no Banco Vetorial
    context_str = "Nenhuma informação específica encontrada no banco de dados para esta pergunta."
    
    if RAG_AVAILABLE:
        try:
            rag_results = rag_service.search(user_text, k=3)
            if rag_results:
                context_str = "--- DADOS ENCONTRADOS NO SISTEMA ---\n"
                for res in rag_results:
                    item = res['item']
                    context_str += f"""
                    - PACOTE: {item.get('title')}
                      PREÇO: {item.get('price')}
                      DESCRIÇÃO: {item.get('description', '')[:500]}
                      INCLUSO: {item.get('inclusoes', 'Consultar')}
                      LINK PAGAMENTO/DETALHES: {item.get('url', 'N/A')}
                    """
                context_str += "\n--- FIM DOS DADOS ---"
        except Exception as e:
            print(f"Erro no RAG: {e}")
            # Não quebra o bot, apenas segue sem contexto específico
            pass

    # 5. Gera a resposta com a IA
    try:
        response_text = await chain.ainvoke({
            "user_text": user_text,
            "history": history,
            "rag_context": context_str,
            "catalog_summary": CATALOG_SUMMARY,
            "time_greeting": current_greeting
        })
        
        # 6. Atualiza Histórico (Mantém os últimos 2000 caracteres para não estourar memória)
        # Removemos o separador interno "|||" do histórico para não confundir o modelo no futuro
        clean_response = response_text.replace("|||", " ")
        new_history = f"Cliente: {user_text}\nMárcio: {clean_response}\n"
        MEMORY[user_id] = (history + new_history)[-2000:]
        
        # 7. Processamento da Saída (Split das mensagens)
        # O modelo usa "|||" para indicar que quer mandar balões separados no Zap
        raw_messages = [msg.strip() for msg in response_text.split("|||") if msg.strip()]
        
        return {
            "messages": raw_messages,
            "action": "reply"
        }
        
    except Exception as e:
        print(f"❌ Erro crítico na IA: {e}")
        return {
            "messages": ["Desculpe, o sistema da agência está momentaneamente indisponível. Tente novamente em 1 minuto."],
            "action": "error"
        }
