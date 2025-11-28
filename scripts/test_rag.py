import sys
import os

# Adiciona o diretório raiz ao path para importar módulos
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.services.rag_service import rag_service

def test_search():
    print("Testing RAG search for 'reveillon'...")
    results = rag_service.search("reveillon", k=5)
    
    if not results:
        print("No results found.")
    else:
        print(f"Found {len(results)} results:")
        for res in results:
            print(f"- {res['item']['title']} (Dist: {res['distance']:.4f})")

    print("\nTesting RAG search for 'ano novo'...")
    results = rag_service.search("ano novo", k=5)
    if not results:
        print("No results found.")
    else:
        print(f"Found {len(results)} results:")
        for res in results:
            print(f"- {res['item']['title']} (Dist: {res['distance']:.4f})")

if __name__ == "__main__":
    test_search()
