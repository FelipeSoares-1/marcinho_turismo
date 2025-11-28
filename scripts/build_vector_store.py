import os
import json
import pickle
import numpy as np
import faiss
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from dotenv import load_dotenv
import time

# Carrega variáveis de ambiente
load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
CATALOG_FILE = os.path.join(DATA_DIR, "catalog.json")
INDEX_FILE = os.path.join(DATA_DIR, "index.faiss")
METADATA_FILE = os.path.join(DATA_DIR, "index.pkl")

def main():
    if not GOOGLE_API_KEY:
        print("Erro: GOOGLE_API_KEY não encontrada no .env")
        return

    print("Carregando catálogo...")
    if not os.path.exists(CATALOG_FILE):
        print(f"Erro: Arquivo {CATALOG_FILE} não encontrado. Rode o scraper primeiro.")
        return

    with open(CATALOG_FILE, 'r', encoding='utf-8') as f:
        catalog = json.load(f)

    if not catalog:
        print("Catálogo vazio.")
        return

    # Verifica se já existe um índice parcial
    if os.path.exists(INDEX_FILE) and os.path.exists(METADATA_FILE):
        print("Índice existente encontrado. Carregando para retomar...")
        index = faiss.read_index(INDEX_FILE)
        with open(METADATA_FILE, 'rb') as f:
            metadatas = pickle.load(f)
        # Recalcula embeddings já processados (assumindo ordem fixa do catálogo)
        # Isso é simplificado. O ideal seria salvar IDs.
        # Vamos pular os primeiros N itens
        start_index = len(metadatas)
        print(f"Retomando do item {start_index + 1}...")
    else:
        index = None
        metadatas = []
        start_index = 0

    # Inicializa Embeddings (Local e Rápido)
    from langchain_community.embeddings import FastEmbedEmbeddings
    embeddings_model = FastEmbedEmbeddings(model_name="BAAI/bge-small-en-v1.5") # Modelo leve e eficiente

    texts = []
    # Prepara textos
    for item in catalog:
        # Monta o texto rico para embedding
        embarques_str = ", ".join(item.get('embarques', []))
        content = (
            f"Pacote: {item['title']}\n"
            f"Preço: {item['price']}\n"
            f"Descrição: {item['description']}\n"
            f"Roteiro: {item.get('roteiro', '')}\n"
            f"Inclusões: {item.get('inclusoes', '')}\n"
            f"Embarques: {embarques_str}"
        )
        texts.append(content)

    # Processamento em lote (agora pode ser maior pois é local)
    batch_size = 10 
    
    for i in range(start_index, len(texts), batch_size):
        batch = texts[i:i+batch_size]
        print(f"Processando lote {i//batch_size + 1}...")
        
        try:
            batch_embeddings = embeddings_model.embed_documents(batch)
            
            # Adiciona ao índice
            embeddings_np = np.array(batch_embeddings).astype('float32')
            
            if index is None:
                dimension = embeddings_np.shape[1]
                index = faiss.IndexFlatL2(dimension)
            
            index.add(embeddings_np)
            # Adiciona metadados correspondentes
            end_idx = min(i + batch_size, len(catalog))
            metadatas.extend(catalog[i:end_idx])
            
            # Salva checkpoint
            faiss.write_index(index, INDEX_FILE)
            with open(METADATA_FILE, 'wb') as f:
                pickle.dump(metadatas, f)
            
        except Exception as e:
            print(f"Erro no lote {i}: {e}")
            break

    print("Processamento concluído!")

if __name__ == "__main__":
    main()
