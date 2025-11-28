import requests
url = "https://marcinhotur.com.br/pacote/beto-carreiro-balneario-barra-sul-data_28-11-2025h19_00p364/44041"
headers = {'User-Agent': 'Mozilla/5.0'}
try:
    r = requests.get(url, headers=headers)
    with open("page_source.html", "w", encoding="utf-8") as f:
        f.write(r.text)
    print("HTML saved.")
except Exception as e:
    print(f"Error: {e}")
