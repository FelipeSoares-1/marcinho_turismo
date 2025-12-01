import os
import json
import time
import requests
import re
from bs4 import BeautifulSoup
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from typing import List, Optional
from urllib.parse import urljoin, urlparse

load_dotenv()

# Configuração do Modelo
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    temperature=0,
    google_api_key=GOOGLE_API_KEY
)

BASE_URL = "https://marcinhotur.com.br"
OUTPUT_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "catalog.json")

# Definição do Schema de Saída (Estruturado)
class TravelPackage(BaseModel):
    title: str = Field(description="O título do pacote de viagem")
    price: str = Field(description="O preço do pacote. Se houver opções (duplo, triplo), liste todas. Ex: 'R$ 2.500 (Duplo) / R$ 2.100 (Quádruplo)'. Se não achar, use 'Sob consulta'.")
    payment_conditions: str = Field(description="Condições de pagamento, parcelamento, taxas e formas de pagamento (ex: '12x no cartão', 'à vista com desconto'). Procure por seções como 'INVESTIMENTO' ou 'FORMA DE PAGAMENTO'.")
    description: str = Field(description="Um resumo atrativo do pacote, mencionando os principais destaques.")
    roteiro: str = Field(description="O roteiro detalhado dia a dia. IMPORTANTE: Copie o texto integral dos dias (Dia 1, Dia 2, etc) para não perder detalhes. Formate com quebras de linha.")
    inclusoes: str = Field(description="Lista completa do que está incluso e NÃO incluso (ex: ingressos, taxas extras).")
    embarques: List[str] = Field(description="Lista dos locais e horários de embarque mencionados.")

visited_pages = set()
package_links = set()

def is_valid_internal_link(url):
    parsed = urlparse(url)
    return parsed.netloc == "" or "marcinhotur.com.br" in parsed.netloc

def get_links_from_page(url):
    """Busca links na página que podem levar a pacotes ou outras listas de pacotes."""
    if url in visited_pages:
        return [], []
    
    print(f"🔎 Varrendo: {url}")
    visited_pages.add(url)
    
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            return [], []
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        found_packages = set()
        found_listings = set()
        
        for a in soup.find_all('a', href=True):
            href = a['href']
            full_url = urljoin(BASE_URL, href)
            
            if not is_valid_internal_link(full_url):
                continue
                
            if any(x in full_url for x in ['whatsapp', 'facebook', 'instagram', 'tel:', 'mailto:', 'wp-admin', 'wp-json']):
                continue

            if '/pacote/' in full_url or '/produto/' in full_url:
                found_packages.add(full_url)
            elif '/categoria/' in full_url or '/viagens' in full_url or 'page/' in full_url:
                found_listings.add(full_url)
                
        return list(found_packages), list(found_listings)

    except Exception as e:
        print(f"Erro ao ler {url}: {e}")
        return [], []

def fetch_page_content(url):
    """Baixa o HTML e limpa para texto puro para economizar tokens"""
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            print(f"❌ Erro {response.status_code} ao acessar {url}")
            return None
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.decompose()
            
        content_div = soup.find('div', class_='elementor-widget-wrap') or soup.body
        text = content_div.get_text(separator="\n")
        
        clean_text = "\n".join([line.strip() for line in text.splitlines() if line.strip()])
        return clean_text[:30000] 
    except Exception as e:
        print(f"Erro ao processar {url}: {e}")
        return None

def extract_data_with_llm(url, raw_text):
    """Usa o Gemini para extrair dados estruturados do texto bruto"""
    # print(f"🧠 Analisando com IA: {url}...")
    
    prompt = f"""
    Você é um especialista em extração de dados de turismo.
    Analise o texto abaixo, extraído de uma página de venda de pacote de viagem.
    
    Sua missão é extrair e estruturar as informações para um catálogo de vendas.
    
    TEXTO DA PÁGINA:
    {raw_text}
    
    INSTRUÇÕES ESPECÍFICAS:
    1. PREÇO: Procure valores em R$ no texto. Muitas vezes estão no meio da descrição ou na seção "INVESTIMENTO".
    2. PAGAMENTO: Extraia todas as condições de parcelamento, taxas de adesão e descontos à vista.
    3. ROTEIRO: Resuma o roteiro dia a dia de forma clara e organizada. **SEMPRE INCLUA TODOS OS PASSEIOS OPCIONAIS E SEUS RESPECTIVOS CUSTOS SE ESTIVEREM ESPECIFICADOS NO TEXTO ORIGINAL.**
    4. INCLUSÕES: Liste tudo que está incluso no pacote. **SEMPRE INCLUA TODOS OS CUSTOS ADICIONAIS OU ITENS NÃO INCLUSOS SE ESTIVEREM ESPECIFICADOS NO TEXTO ORIGINAL.**
    5. EMBARQUES: Procure por locais de saída (ex: Tatuapé, Barra Funda) e horários.
    
    Retorne APENAS o JSON seguindo o schema solicitado.
    """
    
    structured_llm = llm.with_structured_output(TravelPackage)
    
    try:
        result = structured_llm.invoke(prompt)
        return result.dict()
    except Exception as e:
        print(f"❌ Erro na extração LLM: {e}")
        return None

def main():
    print("🕷️ Iniciando Crawler Inteligente (Powered by Gemini)...")
    
    pages_to_visit = [BASE_URL]
    
    # Fase 1: Descoberta de Links
    print("--- FASE 1: Mapeando Site ---")
    max_pages = 50 # Aumentado para garantir varredura completa
    count = 0
    
    while pages_to_visit and count < max_pages:
        current_page = pages_to_visit.pop(0)
        new_packages, new_listings = get_links_from_page(current_page)
        
        for pkg in new_packages:
            package_links.add(pkg)
            
        for lst in new_listings:
            if lst not in visited_pages and lst not in pages_to_visit:
                pages_to_visit.append(lst)
        
        count += 1
        time.sleep(0.2)

    print(f"\n✅ Encontrados {len(package_links)} pacotes para analisar.")
    
    # Fase 2: Extração com IA
    print("--- FASE 2: Extração com IA ---")
    catalog = []
    
    # Para teste rápido, vamos limitar a 10 pacotes se houver muitos
    # Remove o [:10] abaixo para rodar em tudo em produção
    links_to_process = list(package_links)
    
    for i, link in enumerate(links_to_process):
        print(f"[{i+1}/{len(links_to_process)}] Processando: {link}")
        raw_text = fetch_page_content(link)
        
        if raw_text:
            data = extract_data_with_llm(link, raw_text)
            if data:
                data['url'] = link
                # 1. Gera Link de Reserva (Carrinho) substituindo /pacote/ por /carrinho_compra/
                data['booking_url'] = link.replace('/pacote/', '/carrinho_compra/')
                
                # 2. Extração de Imagem via Meta Tag (og:image)
                try:
                   r = requests.get(link, headers={"User-Agent": "Mozilla/5.0"})
                   s = BeautifulSoup(r.content, 'html.parser')
                   
                   og_image = s.find("meta", property="og:image")
                   if og_image and og_image.get("content"):
                       data['images'] = [og_image["content"]]
                   else:
                       # Fallback
                       imgs = [img['src'] for img in s.find_all('img') if 'uploads' in img.get('src', '')]
                       data['images'] = imgs[:3] if imgs else ["https://marcinhotur.com.br/assets/uploads/logos/marcinhotur1.png"]
                except:
                   data['images'] = []

                catalog.append(data)
            else:
                print("   ⚠️ Falha na extração IA")
        
        # Salvar parcial a cada 5
        if i % 5 == 0:
             with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
                json.dump(catalog, f, indent=2, ensure_ascii=False)
        
        time.sleep(1) # Rate limit do Gemini e do Site
            
    # Salvamento Final
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(catalog, f, indent=2, ensure_ascii=False)
            
    print(f"\n💾 Catálogo RECONSTRUÍDO com {len(catalog)} itens inteligentes em: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
