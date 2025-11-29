import sys
import os
import asyncio

# Adiciona o diretório raiz ao PYTHONPATH
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from app.services.rag_service import rag_service

def debug_rag():
    query = "Me fala mais sobre o Réveillon dos Sonhos em Copacabana"
    print(f"🔍 Buscando por: '{query}'")
    
    results = rag_service.search(query, k=5)
    
    print(f"\nEncontrados {len(results)} resultados:")
    for i, res in enumerate(results):
        item = res['item']
        print(f"\n--- Resultado {i+1} (Distance: {res['distance']:.4f}) ---")
        print(f"Título: {item['title']}")
        print(f"Roteiro: {item.get('roteiro', 'NÃO TEM ROTEIRO')[:100]}...")
        print(f"Inclusões: {item.get('inclusoes', 'NÃO TEM INCLUSÕES')[:100]}...")

if __name__ == "__main__":
    debug_rag()
