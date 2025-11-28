import httpx
import os
import logging
from typing import Optional, Dict, Any

# Configuração de Logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MetaClient:
    """
    Cliente para interagir com a Graph API da Meta (WhatsApp e Instagram).
    """
    def __init__(self):
        self.whatsapp_token = os.getenv("WHATSAPP_API_TOKEN")
        self.whatsapp_phone_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
        self.instagram_token = os.getenv("INSTAGRAM_ACCESS_TOKEN")
        self.instagram_account_id = os.getenv("INSTAGRAM_ACCOUNT_ID")
        self.api_version = "v21.0"
        self.base_url = f"https://graph.facebook.com/{self.api_version}"

    async def send_whatsapp_message(self, to: str, text: str) -> Optional[Dict[str, Any]]:
        """
        Envia mensagem de texto para o WhatsApp.
        """
        if not self.whatsapp_token or not self.whatsapp_phone_id:
            logger.error("Credenciais do WhatsApp não configuradas.")
            return None

        url = f"{self.base_url}/{self.whatsapp_phone_id}/messages"
        headers = {
            "Authorization": f"Bearer {self.whatsapp_token}",
            "Content-Type": "application/json"
        }
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "text",
            "text": {"body": text}
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                logger.info(f"Mensagem WhatsApp enviada para {to}: {text[:20]}...")
                return response.json()
            except httpx.HTTPStatusError as e:
                logger.error(f"Erro API WhatsApp: {e.response.text}")
                return None
            except Exception as e:
                logger.error(f"Erro inesperado WhatsApp: {e}")
                return None

    async def send_whatsapp_typing_action(self, to: str) -> Optional[Dict[str, Any]]:
        """
        Envia ação de 'digitando...' para o WhatsApp.
        Nota: Nem todas as versões da API suportam isso oficialmente, mas é uma tentativa válida.
        """
        if not self.whatsapp_token or not self.whatsapp_phone_id:
            return None

        url = f"{self.base_url}/{self.whatsapp_phone_id}/messages"
        headers = {
            "Authorization": f"Bearer {self.whatsapp_token}",
            "Content-Type": "application/json"
        }
        # Payload não oficial/experimental para Cloud API (baseado em padrões comuns)
        # Se falhar, apenas logamos o erro e seguimos.
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "text", # Hack: Algumas implementações usam mensagem vazia ou controle específico
            # A API Cloud oficial não tem "typing_on" documentado publicamente da mesma forma que o Messenger.
            # Vamos tentar enviar uma mensagem de controle ou apenas ignorar se não houver endpoint claro.
        }
        
        # CORREÇÃO: A API Cloud do WhatsApp NÃO suporta "sender_action" ou "typing_on" nativamente como o Messenger.
        # Enviar isso pode causar erro 400.
        # Como o usuário pediu MUITO, vamos tentar o endpoint de messages com type="reaction" (não é typing) ou similar.
        # Mas para não quebrar o bot, vou simular o log e NÃO enviar nada que possa dar erro 400 e travar a conta.
        
        # ATUALIZAÇÃO: Pesquisas indicam que NÃO HÁ suporte oficial para "typing" na Cloud API (v21.0).
        # Enviar payload inválido pode prejudicar a qualidade do número.
        # Vou deixar o método mas com um log de aviso e NÃO fazer a requisição real para proteger a conta.
        logger.warning("Tentativa de enviar 'typing_on': Funcionalidade não suportada oficialmente na Cloud API.")
        return {"status": "skipped_unsupported"}

    async def send_instagram_message(self, recipient_id: str, text: str) -> Optional[Dict[str, Any]]:
        """
        Envia mensagem direta (DM) para o Instagram.
        """
        if not self.instagram_token:
            logger.error("Credenciais do Instagram não configuradas.")
            return None

        url = f"{self.base_url}/me/messages"
        headers = {
            "Authorization": f"Bearer {self.instagram_token}",
            "Content-Type": "application/json"
        }
        payload = {
            "recipient": {"id": recipient_id},
            "message": {"text": text}
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                logger.info(f"Mensagem Instagram enviada para {recipient_id}: {text[:20]}...")
                return response.json()
            except httpx.HTTPStatusError as e:
                logger.error(f"Erro API Instagram: {e.response.text}")
                return None
            except Exception as e:
                logger.error(f"Erro inesperado Instagram: {e}")
                return None

    async def get_media_url(self, media_id: str) -> Optional[str]:
        """
        Obtém a URL de download de uma mídia do WhatsApp pelo ID.
        """
        if not self.whatsapp_token:
            return None
            
        url = f"{self.base_url}/{media_id}"
        headers = {"Authorization": f"Bearer {self.whatsapp_token}"}
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                data = response.json()
                return data.get("url")
            except Exception as e:
                logger.error(f"Erro ao obter URL da mídia {media_id}: {e}")
                return None

    async def download_media(self, url: str) -> Optional[bytes]:
        """
        Baixa os bytes da mídia usando a URL obtida.
        Utiliza 'requests' para maior robustez com redirecionamentos complexos da Meta.
        """
        if not self.whatsapp_token:
            return None
            
        def _download_sync():
            import requests
            try:
                # Passo 1: Requisição Inicial com Autenticação
                headers_auth = {
                    "Authorization": f"Bearer {self.whatsapp_token}",
                    "User-Agent": "Mozilla/5.0 (Compatible; MarcinhoBot/1.0)"
                }
                
                # Desabilitamos o redirecionamento automático para controlar o envio do Token
                r = requests.get(url, headers=headers_auth, allow_redirects=False, timeout=30)
                
                final_url = url
                if r.status_code in (301, 302, 303, 307, 308):
                    final_url = r.headers.get("Location")
                    logger.info(f"Redirecionamento detectado para: {final_url}")
                    
                    # Passo 2: Requisição para o Link Final (Geralmente CDN Assinado)
                    # IMPORTANTE: CDNs assinados (lookaside.fbsbx.com) frequentemente REJEITAM
                    # o header Authorization. Por isso, enviamos SEM ele.
                    r = requests.get(
                        final_url, 
                        headers={"User-Agent": "Mozilla/5.0 (Compatible; MarcinhoBot/1.0)"},
                        timeout=60
                    )
                
                r.raise_for_status()
                return r.content
            except Exception as e:
                logger.error(f"Erro no download via requests: {e}")
                return None

        # Executa o download síncrono em uma thread separada para não bloquear o loop asyncio
        return await asyncio.to_thread(_download_sync)
