import requests
from bs4 import BeautifulSoup
import json
import os
import re
from urllib.parse import urljoin, urlparse
import time

BASE_URL = "https://marcinhotur.com.br"
OUTPUT_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "catalog.json")

visited_pages = set()
package_links = set()

def clean_text(text):
    if not text:
        return ""
    return re.sub(r'\s+', ' ', text).strip()

def is_valid_internal_link(url):
    parsed = urlparse(url)
    return parsed.netloc == "" or "marcinhotur.com.br" in parsed.netloc

def get_links_from_page(url):
    """
    Busca links na página que podem levar a pacotes ou outras listas de pacotes.
    """
    if url in visited_pages:
        return [], []
    
    print(f"🔎 Varrendo: {url}")
    visited_pages.add(url)
    
    try:
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
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
                
            # Evita links irrelevantes
            if any(x in full_url for x in ['whatsapp', 'facebook', 'instagram', 'tel:', 'mailto:', 'wp-admin', 'wp-json']):
                continue

            # Identifica Links de Pacotes
            if '/pacote/' in full_url or '/produto/' in full_url:
                found_packages.add(full_url)
            
            # Identifica Links de Listagem (Categorias, Paginação, "Ver Todos")
            # Lógica: Links que contêm 'page', 'categoria', 'viagens' ou texto como "Ver Todos"
            elif '/categoria/' in full_url or '/viagens' in full_url or 'page/' in full_url:
                found_listings.add(full_url)
                
        return list(found_packages), list(found_listings)

    except Exception as e:
        print(f"Erro ao ler {url}: {e}")
        return [], []

def get_package_details(package_url):
    try:
        # print(f"📦 Extraindo: {package_url}")
        response = requests.get(package_url, headers={"User-Agent": "Mozilla/5.0"})
        if response.status_code != 200:
            print(f"❌ Erro HTTP {response.status_code}: {package_url}")
            return None

        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Título (Lógica Robustecida)
        title = ""
        
        # 1. Tenta H1
        if soup.find('h1'):
            title = clean_text(soup.find('h1').text)
            
        # 2. Se H1 falhou ou vazio, tenta <title>
        if not title and soup.find('title'):
            raw_title = soup.find('title').text
            # Remove sufixos comuns
            for suffix in ['|', '-']:
                if suffix in raw_title:
                    raw_title = raw_title.split(suffix)[0]
            title = clean_text(raw_title)
            
        # 3. Fallback para URL (Último recurso)
        if not title or title == "Sem Título":
            parts = package_url.rstrip('/').split('/')
            slug = parts[-1]
            if slug.isdigit() and len(parts) > 1:
                slug = parts[-2]
            # Remove sufixo de data
            slug = slug.split('-data')[0]
            title = slug.replace('-', ' ').title()
            print(f"⚠️ Usando fallback de URL para título: {title}")
        
        if not title:
            print(f"❌ Título não encontrado: {package_url}")
            return None
            
        # print(f"✅ Sucesso: {title}")
        
        # Preço
        price = "Sob consulta"
        price_el = soup.find('span', class_='price') or soup.find('div', class_='price')
        if price_el:
            price = clean_text(price_el.text)

        # Imagens (Pega as 3 primeiras do carrossel ou conteúdo)
        images = []
        
        # Tenta pegar imagem de alta qualidade do OG:IMAGE
        og_image = soup.find("meta", property="og:image")
        if og_image and og_image.get("content"):
             images.append(og_image["content"])

        for img in soup.find_all('img'):
            src = img.get('src')
            if src and 'uploads' in src:
                full_url = urljoin(BASE_URL, src)
                if full_url not in images:
                    images.append(full_url)

        # Extração de campos adicionais
        roteiro = ""
        inclusoes = ""
        embarques = []
        descricao = ""
        
        # Gera Link de Reserva (Carrinho)
        booking_url = package_url.replace('/pacote/', '/carrinho_compra/')

        # Descrição
        desc_div = soup.find('div', class_='cart_destaque')
        if desc_div:
            descricao = desc_div.get_text(separator="\n", strip=True)

        # Roteiro e Inclusões (details)
        details_tags = soup.find_all('details')
        for det in details_tags:
            summary = det.find('summary')
            if not summary: continue
            
            summary_text = summary.get_text(strip=True).upper()
            content = det.find('div').get_text(separator="\n", strip=True) if det.find('div') else ""

            if "ROTEIRO" in summary_text:
                roteiro = content
            elif "O QUE INCLUI" in summary_text:
                inclusoes = content
        
        # Embarques
        embarques_header = soup.find(lambda tag: tag.name == "strong" and "EMBARQUES" in tag.get_text().upper())
        if embarques_header:
            container = embarques_header.find_parent('div', class_='cart_destaque')
            if container:
                boarding_blocks = container.find_all('div', style=lambda s: s and 'margin-top' in s)
                for block in boarding_blocks:
                    loc_div = block.find('div', class_='traco_route')
                    if loc_div:
                        local = loc_div.get_text(strip=True)
                        if local: embarques.append(local)

        return {
            "url": package_url,
            "booking_url": booking_url,
            "title": title,
            "price": price,
            "images": images[:3],
            "description": descricao,
            "roteiro": roteiro,
            "inclusoes": inclusoes,
            "embarques": embarques
        }

    except Exception as e:
        print(f"Erro ao processar pacote {package_url}: {e}")
        return None

def main():
    print("🕷️ Iniciando Crawler Profundo...")
    
    # 1. Fila de páginas para visitar (começa pela home)
    pages_to_visit = [BASE_URL]
    
    # 2. Loop de descoberta
    while pages_to_visit:
        current_page = pages_to_visit.pop(0)
        
        new_packages, new_listings = get_links_from_page(current_page)
        
        # Adiciona pacotes encontrados
        for pkg in new_packages:
            package_links.add(pkg)
            
        # Adiciona novas páginas de listagem para visitar (se ainda não visitadas)
        for lst in new_listings:
            if lst not in visited_pages and lst not in pages_to_visit:
                pages_to_visit.append(lst)
                
        time.sleep(0.5) # Respeito ao servidor

    print(f"\n✅ Encontrados {len(package_links)} links de pacotes únicos.")
    
    # 3. Scraping dos detalhes
    catalog = []
    for i, link in enumerate(package_links):
        print(f"[{i+1}/{len(package_links)}] Processando...")
        details = get_package_details(link)
        if details:
            catalog.append(details)
        time.sleep(0.5)
            
    # 4. Salvar
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(catalog, f, indent=2, ensure_ascii=False)
            
    print(f"\n💾 Catálogo atualizado com {len(catalog)} itens em: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
