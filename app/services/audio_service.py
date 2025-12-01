import os
import requests
import google.generativeai as genai
from dotenv import load_dotenv
import tempfile
from pathlib import Path

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)

class AudioService:
    def __init__(self):
        self.model = genai.GenerativeModel('gemini-1.5-flash')

    def download_audio(self, audio_url: str) -> str:
        """
        Baixa o áudio da URL fornecida e salva em um arquivo temporário.
        Retorna o caminho do arquivo.
        """
        try:
            # WhatsApp URLs might require headers or tokens if not public
            # For Meta API, we usually need the access token in the header
            headers = {}
            token = os.getenv("META_ACCESS_TOKEN")
            if token:
                headers["Authorization"] = f"Bearer {token}"

            response = requests.get(audio_url, headers=headers, stream=True)
            response.raise_for_status()

            # Create a temp file
            # We preserve the extension if possible, or default to .ogg (common for WhatsApp)
            ext = ".ogg" 
            if "audio/mp4" in response.headers.get("Content-Type", ""):
                ext = ".m4a"
            elif "audio/mpeg" in response.headers.get("Content-Type", ""):
                ext = ".mp3"

            with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp_file:
                for chunk in response.iter_content(chunk_size=8192):
                    tmp_file.write(chunk)
                return tmp_file.name
        except Exception as e:
            print(f"❌ Erro ao baixar áudio: {e}")
            return None

    def transcribe_audio(self, file_path: str) -> str:
        """
        Envia o arquivo de áudio para o Gemini e retorna a transcrição.
        """
        if not file_path or not os.path.exists(file_path):
            return "Erro: Arquivo de áudio não encontrado."

        try:
            print(f"📤 Enviando áudio para o Gemini: {file_path}")
            # Upload the file to Gemini
            audio_file = genai.upload_file(path=file_path)
            
            # Generate content
            prompt = "Transcreva este áudio fielmente. Se houver ruído ou silêncio, ignore. Retorne APENAS o texto transcrito."
            response = self.model.generate_content([prompt, audio_file])
            
            # Cleanup: Delete the file from Gemini to save space/privacy (optional but good practice)
            # genai.delete_file(audio_file.name) 
            
            return response.text.strip()
        except Exception as e:
            print(f"❌ Erro na transcrição: {e}")
            return "Desculpe, não consegui ouvir seu áudio."
        finally:
            # Cleanup local temp file
            try:
                os.unlink(file_path)
            except:
                pass

audio_service = AudioService()
