import asyncio
import sys
import os
import requests

# Add project root to path
sys.path.append(os.getcwd())

from app.services.audio_service import audio_service

def test_transcription():
    print("--- Testando AudioService ---")
    
    # 1. Download sample audio (Wikipedia Example.ogg)
    url = "https://upload.wikimedia.org/wikipedia/commons/c/c8/Example.ogg"
    print(f"Baixando áudio de exemplo: {url}")
    
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        temp_file = "test_audio.ogg"
        with open(temp_file, "wb") as f:
            f.write(response.content)
            
        print(f"Áudio salvo em: {temp_file}")
        
        # 2. Transcribe
        print("Enviando para o Gemini...")
        text = audio_service.transcribe_audio(temp_file)
        
        print(f"\n📝 Resultado da Transcrição:\n{text}")
        
        if text and "Erro" not in text:
            print("\n✅ SUCESSO: Transcrição realizada.")
        else:
            print("\n❌ FALHA: Erro na transcrição.")
            
    except Exception as e:
        print(f"❌ Erro no teste: {e}")
    finally:
        if os.path.exists("test_audio.ogg"):
            # os.remove("test_audio.ogg") # Keep for inspection if needed
            pass

if __name__ == "__main__":
    test_transcription()
