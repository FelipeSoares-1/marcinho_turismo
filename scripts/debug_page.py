import requests
from bs4 import BeautifulSoup

url = "https://marcinhotur.com.br/pacote/copacabana-rj-data_13-12-2025h21_30p409/44041"
headers = {"User-Agent": "Mozilla/5.0"}
response = requests.get(url, headers=headers)

soup = BeautifulSoup(response.content, 'html.parser')

# Find all links
print("--- Searching for 'carrinho_compra' links ---")
for a in soup.find_all('a', href=True):
    if 'carrinho_compra' in a['href']:
        print(f"Found Payment Link: {a['href']}")

# Find Images
print("\n--- Searching for Images ---")
for img in soup.find_all('img'):
    src = img.get('src')
    if src and 'uploads' in src:
        print(f"Found Image: {src}")