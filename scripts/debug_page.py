import requests

url = "https://marcinhotur.com.br/pacote/reveillon-arrail-do-cabo-macae-buzios-data_30-12-2025h18_30p349/44041"
print(f"Fetching {url}")
try:
    r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
    print(f"Status: {r.status_code}")
    print(r.text[:2000]) # Print first 2000 chars
except Exception as e:
    print(e)
