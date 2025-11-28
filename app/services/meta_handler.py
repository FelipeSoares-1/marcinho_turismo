from typing import Dict, Any, Optional, List
import asyncio
import os
import tempfile
import google.generativeai as genai
from app.core.brain import process_user_intent

from app.services.meta_client import MetaClient

# Configuração do Gemini para Transcrição
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)

meta_client = MetaClient()

async def transcribe_audio(audio_bytes: bytes) -> str:
    """
    Transcreve áudio usando o Gemini 1.5 Flash.
    """
    temp_path = None
    try:
        # Salva em arquivo temporário (Gemini precisa de arquivo)
        with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as temp_audio:
            temp_audio.write(audio_bytes)
            temp_path = temp_audio.name
        
        print(f"Áudio salvo em: {temp_path}")

        # Upload para o Gemini
        myfile = genai.upload_file(temp_path, mime_type="audio/ogg")
        
        # Modelo para transcrição
        model = genai.GenerativeModel("gemini-1.5-flash")
        
        # Prompt para transcrição fiel
        result = model.generate_content(
            [myfile, "Transcreva este áudio exatamente como foi falado. Se não houver fala, descreva o som."],
            request_options={"timeout": 600}
        )
        
        return result.text
    except Exception as e:
        import traceback
        print(f"Erro na transcrição: {e}")
        traceback.print_exc()
        return "[Erro ao transcrever áudio]"
    finally:
        if temp_path and os.path.exists(temp_path):
            try:
                os.unlink(temp_path)
            except Exception as cleanup_error:
                print(f"Erro ao limpar arquivo temporário: {cleanup_error}")

async def send_messages_with_delay(messages: List[str], user_id: str, channel: str):
    """
    Envia múltiplas mensagens com delay entre elas para simular digitação natural.
    """
    # Delay inicial "pensando" (antes da primeira mensagem)
    if channel == 'whatsapp':
        await meta_client.send_whatsapp_typing_action(user_id)
    
    # Cálculo dinâmico mais realista: 50ms a 100ms por caractere da primeira mensagem
    initial_delay = 0.0
    if messages:
        initial_delay = min(4.0, len(messages[0]) * 0.08) # Teto de 4s para começar
    
    initial_delay = max(1.5, initial_delay) # Mínimo de 1.5s de "pensando"
    
    print(f"Plan de Envio ({len(messages)} msgs). Delay Inicial: {initial_delay:.2f}s")
    await asyncio.sleep(initial_delay)

    for idx, message in enumerate(messages):
        # Simula delay de digitação entre mensagens (baseado no tamanho da PRÓXIMA mensagem ou da atual)
        # Se houver mensagem anterior, esperamos o tempo que levaria para digitar a ATUAL
        if idx > 0:
            # Velocidade média de digitação: ~5 a 8 caracteres por segundo
            # 50 chars = ~6 a 10 segundos.
            # Vamos usar um fator de 0.15s por char + base de 1.0s
            delay = 1.0 + (len(message) * 0.12)
            
            # Cap (limites) para não ficar eterno
            delay = max(2.0, min(delay, 6.0)) 
            
            print(f"Digitando mensagem {idx+1}/{len(messages)}... (Delay: {delay:.2f}s)")
            await asyncio.sleep(delay)
        
        # Envia via MetaClient
        if channel == 'whatsapp':
            await meta_client.send_whatsapp_message(user_id, message)
        elif channel.startswith('instagram'):
            await meta_client.send_instagram_message(user_id, message)
        
        print(f"[{channel.upper()}] Enviado para {user_id}: {message}")

async def handle_whatsapp_event(payload: Dict[str, Any]):
    """
    Processa eventos recebidos do WhatsApp Business API.
    """
    print("Handling WhatsApp Event")
    try:
        entry = payload.get('entry', [])[0]
        changes = entry.get('changes', [])[0]
        value = changes.get('value', {})
        
        if 'messages' in value:
            message = value['messages'][0]
            user_id = message['from']
            msg_type = message.get('type')
            
            text_to_process = ""

            if msg_type == 'text':
                text_to_process = message.get('text', {}).get('body', '')
            
            elif msg_type == 'audio':
                # Simulação de falha humana/técnica baseada no horário para máxima credibilidade
                from datetime import datetime, timedelta
                import random

                # Fuso horário simples BRT (UTC-3) sem dependência extra
                now = datetime.utcnow() - timedelta(hours=3)
                hour = now.hour
                
                print(f"Áudio recebido às {hour}h (BRT). Selecionando resposta humanizada...")

                fallback_messages = []

                if 8 <= hour < 19:
                    # Horário Comercial (08h às 19h): Correria, Barulho, Agência
                    options = [
                        ["Opa! Tô na correria aqui na agência e tá muito barulho.", "Consegue escrever pra mim rapidinho?"],
                        ["Eita, meu áudio aqui não tá querendo baixar de jeito nenhum.", "Manda em texto por favor?"],
                        ["Tô atendendo um cliente aqui e não consigo ouvir áudio agora.", "Pode escrever?"],
                        ["Minha internet móvel tá oscilando pra áudio...", "Escreve pra mim que é mais garantido!"]
                    ]
                    fallback_messages = random.choice(options)

                elif 19 <= hour < 23:
                    # Noite (19h às 23h): Sem fone, em casa, descansando
                    options = [
                        ["Opa! Tô sem fone agora e não consigo ouvir.", "Pode mandar escrito?"],
                        ["Meu volume aqui tá pifado, acredita?", "Consegue escrever pra mim?"],
                        ["Tô num lugar que não dá pra ouvir áudio agora...", "Manda texto por favor!"]
                    ]
                    fallback_messages = random.choice(options)

                else:
                    # Madrugada (23h às 08h): Silêncio, gente dormindo
                    options = [
                        ["Fala! Tô falando baixo aqui que o pessoal já dormiu.", "Escreve pra mim por favor?"],
                        ["Madrugadão e eu sem fone...", "Manda texto que eu te respondo na hora!"],
                        ["Opa! Nesse horário não consigo ouvir áudio.", "Consegue digitar?"]
                    ]
                    fallback_messages = random.choice(options)
                
                await send_messages_with_delay(
                    fallback_messages, 
                    user_id, 
                    'whatsapp'
                )
            
            if text_to_process:
                result = await process_user_intent(text_to_process, user_id, 'whatsapp')
                messages = result.get('messages', [])
                
                # Envia as mensagens com delay
                await send_messages_with_delay(messages, user_id, 'whatsapp')
                
    except (IndexError, KeyError) as e:
        print(f"Erro ao processar payload do WhatsApp: {e}")


async def handle_instagram_event(payload: Dict[str, Any]):
    """
    Processa eventos recebidos da Instagram Graph API.
    Diferencia entre Mensagens Diretas (DM) e Comentários.
    """
    print("Handling Instagram Event")
    try:
        entry = payload.get('entry', [])[0]
        
        if 'messaging' in entry:
            # Direct Message
            messaging_event = entry['messaging'][0]
            sender_id = messaging_event.get('sender', {}).get('id')
            message = messaging_event.get('message', {})
            text = message.get('text', '')
            
            if text:
                result = await process_user_intent(text, sender_id, 'instagram_dm')
                messages = result.get('messages', [])
                await send_messages_with_delay(messages, sender_id, 'instagram_dm')
                
        elif 'changes' in entry:
            # Feed comments
            changes = entry['changes'][0]
            field = changes.get('field')
            value = changes.get('value', {})
            
            if field == 'comments':
                text = value.get('text', '')
                from_user = value.get('from', {})
                user_id = from_user.get('id')
                
                # Palavras-chave para gatilho
                keywords = ["preço", "eu quero", "valor", "info"]
                if any(keyword in text.lower() for keyword in keywords):
                    print(f"Comentário de interesse detectado: {text}")
                    result = await process_user_intent(text, user_id, 'instagram_comment')
                    messages = result.get('messages', [])
                    await send_messages_with_delay(messages, user_id, 'instagram_comment')
                    
    except (IndexError, KeyError) as e:
        print(f"Erro ao processar payload do Instagram: {e}")
