import requests
from bs4 import BeautifulSoup
import json
import os
import re
from urllib.parse import urljoin

BASE_URL = "https://marcinhotur.com.br"
OUTPUT_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "catalog.json")

def clean_text(text):
    if not text:
        return ""
    return re.sub(r'\s+', ' ', text).strip()

def get_package_details(package_url):
    try:
        print(f"Scraping: {package_url}")
        response = requests.get(package_url, headers={"User-Agent": "Mozilla/5.0"})
        if response.status_code != 200:
            print(f"Erro ao acessar {package_url}: {response.status_code}")
            return None

        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Título (Tentativa robusta)
        title = ""
        if soup.find('h1'):
            title = clean_text(soup.find('h1').text)
        elif soup.find('title'):
            title = clean_text(soup.find('title').text.split('|')[0]) # Remove sufixo do site
        
        if not title or title == "Sem Título":
            # Fallback para URL: pega o penúltimo segmento se o último for numérico
            parts = package_url.rstrip('/').split('/')
            slug = parts[-1]
            if slug.isdigit() and len(parts) > 1:
                slug = parts[-2]
            
            # Remove sufixo de data se existir (ex: -data_28-11...)
            slug = slug.split('-data')[0]
            title = slug.replace('-', ' ').title()
        
        # Preço (Tentativa de achar o preço principal)
        price = "Sob consulta"
        price_el = soup.find('span', class_='price') or soup.find('div', class_='price')
        if price_el:
            price = clean_text(price_el.text)

        # Imagens
        images = []
        for img in soup.find_all('img'):
            src = img.get('src')
            if src and 'uploads' in src: # Filtro básico para pegar fotos do pacote
                full_url = urljoin(BASE_URL, src)
                if full_url not in images:
                    images.append(full_url)
        
        # Extração de campos adicionais
        roteiro = ""
        inclusoes = ""
        embarques = []
        descricao = ""

        # 1. Descrição (div.cart_destaque com texto)
        desc_div = soup.find('div', class_='cart_destaque')
        if desc_div:
            descricao = desc_div.get_text(separator="\n", strip=True)
            descricao = descricao.replace("Ouvir", "").replace("Parar", "").strip()

        # 2. Roteiro e Inclusões (dentro de <details>)
        details_tags = soup.find_all('details')
        for det in details_tags:
            summary = det.find('summary')
            if not summary:
                continue
            summary_text = summary.get_text(strip=True).upper()
            
            content_div = det.find('div')
            if not content_div:
                continue
                
            content_text = content_div.get_text(separator="\n", strip=True)

            if "ROTEIRO" in summary_text:
                roteiro = content_text
            elif "O QUE INCLUI" in summary_text:
                inclusoes = content_text
            elif "INFORMAÇÕES IMPORTANTES" in summary_text:
                 # Opcional: se quiser pegar info importante também
                 pass

        # 3. Embarques
        # Busca por "EMBARQUES" e tenta achar os blocos de embarque
        embarques_header = soup.find(lambda tag: tag.name == "strong" and "EMBARQUES" in tag.get_text().upper())
        if embarques_header:
            # O container pai deve ter as divs de embarque
            # A estrutura observada é que o strong está dentro de uma div, e os embarques estão em divs irmãs ou próximas
            # Vamos subir alguns níveis e procurar por divs com class 'traco_route'
            
            # Tenta subir para o container geral dos embarques
            container = embarques_header.find_parent('div', class_='cart_destaque')
            if container:
                # Itera sobre os filhos para achar os locais
                # Estrutura: <div style="margin-top: 15px;"> ... <div class="traco_route"><strong>LOCAL</strong></div> ... </div>
                boarding_blocks = container.find_all('div', style=lambda s: s and 'margin-top' in s)
                for block in boarding_blocks:
                    loc_div = block.find('div', class_='traco_route')
                    if loc_div:
                        local_strong = loc_div.find('strong')
                        if local_strong:
                             local = local_strong.get_text(strip=True)
                             # Horário geralmente está em outra div traco_route no mesmo bloco
                             horario_div = block.find_all('div', class_='traco_route')
                             horario = ""
                             if len(horario_div) > 1:
                                 horario = horario_div[1].get_text(strip=True)
                             
                             if local:
                                 embarques.append(f"{local} {horario}".strip())

        return {
            "url": package_url,
            "title": title,
            "price": price,
            "images": images[:3],
            "description": descricao,
            "roteiro": roteiro,
            "inclusoes": inclusoes,
            "embarques": embarques
        }

    except Exception as e:
        print(f"Erro ao processar {package_url}: {e}")
        return None

def main():
    print("Iniciando scraper do catálogo...")
    
    # Garante que a pasta data existe
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)

    try:
        response = requests.get(BASE_URL, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Encontrar links de produtos/pacotes
        package_links = set()
        for a in soup.find_all('a', href=True):
            href = a['href']
            # Filtra links de compartilhamento e garante que é um link interno de pacote
            if ('/pacote/' in href or '/produto/' in href) and 'api.whatsapp.com' not in href and 'telegram.me' not in href and 'facebook.com' not in href:
                full_url = urljoin(BASE_URL, href)
                package_links.add(full_url)
        
        print(f"Encontrados {len(package_links)} links de pacotes VÁLIDOS.")
        
        catalog = []
        for link in package_links:
            details = get_package_details(link)
            if details and details['title'] != "Sem Título": # Filtra páginas quebradas
                catalog.append(details)
        
        # Salvar JSON
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(catalog, f, indent=2, ensure_ascii=False)
            
        print(f"\nCatálogo salvo com {len(catalog)} itens em: {OUTPUT_FILE}")

    except Exception as e:
        print(f"Erro fatal no scraper: {e}")

if __name__ == "__main__":
    main()
