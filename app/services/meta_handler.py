from typing import Dict, Any, Optional, List
import asyncio
import os
import tempfile
from app.services.meta_client import MetaClient

meta_client = MetaClient()



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
                audio_id = message.get('audio', {}).get('id')
                if audio_id:
                    print(f"🎧 Áudio recebido (ID: {audio_id}). Iniciando transcrição...")
                    
                    # 1. Obtém URL de download
                    audio_url = await meta_client.get_media_url(audio_id)
                    
                    if audio_url:
                        # 2. Baixa o áudio (bytes)
                        audio_bytes = await meta_client.download_media(audio_url)
                        
                        if audio_bytes:
                            # 3. Salva em arquivo temporário para o Gemini processar
                            import tempfile
                            from app.services.audio_service import audio_service
                            
                            with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as temp_audio:
                                temp_audio.write(audio_bytes)
                                temp_path = temp_audio.name
                            
                            # 4. Transcreve
                            transcription = audio_service.transcribe_audio(temp_path)
                            print(f"📝 Transcrição: {transcription}")
                            
                            # 5. Adiciona prefixo para o Brain saber que é áudio
                            text_to_process = f"[TRANSCRIÇÃO DE ÁUDIO]: {transcription}"
                        else:
                            print("❌ Falha ao baixar bytes do áudio.")
                            await send_messages_with_delay(
                                ["Tive um problema técnico para ouvir seu áudio.", "Pode escrever para mim?"],
                                user_id, 'whatsapp'
                            )
                    else:
                        print("❌ Falha ao obter URL do áudio.")
                        await send_messages_with_delay(
                            ["Não consegui carregar seu áudio.", "Pode digitar por favor?"],
                            user_id, 'whatsapp'
                        )
            
            if text_to_process:
                result = await process_user_intent(text_to_process, user_id, 'whatsapp')
                messages = result.get('messages', [])
                images = result.get('images', [])

                # Envia as mensagens com delay
                await send_messages_with_delay(messages, user_id, 'whatsapp')
                
                # Envia imagens (se houver) APÓS as mensagens de texto
                # Isso garante que o contexto textual chegue antes da foto
                if images:
                    for img_url in images:
                        print(f"Enviando imagem para {user_id}: {img_url}")
                        await meta_client.send_whatsapp_image(user_id, img_url)
                        # Pequeno delay entre imagem e próxima ação (se houvesse)
                        await asyncio.sleep(1)
                
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
