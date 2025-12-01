import os
import pickle
import faiss
import numpy as np
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from dotenv import load_dotenv

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data")
INDEX_FILE = os.path.join(DATA_DIR, "index.faiss")
METADATA_FILE = os.path.join(DATA_DIR, "index.pkl")

class RAGService:
    def __init__(self):
        self.index = None
        self.metadata = []
        self.embeddings_model = None
        self._load_resources()

    def _load_resources(self):
        """Carrega o índice FAISS e os metadados."""
        # if not GOOGLE_API_KEY:
        #     print("RAG: GOOGLE_API_KEY não configurada.")
        #     return

        # Inicializa Embeddings (Gemini API - Mais leve para Cloud Run)
        try:
            self.embeddings_model = GoogleGenerativeAIEmbeddings(model="models/embedding-001", google_api_key=GOOGLE_API_KEY)
        except Exception as e:
            print(f"RAG: Erro ao carregar modelo de embeddings: {e}")
            return

        if os.path.exists(INDEX_FILE) and os.path.exists(METADATA_FILE):
            try:
                self.index = faiss.read_index(INDEX_FILE)
                with open(METADATA_FILE, 'rb') as f:
                    self.metadata = pickle.load(f)
                print(f"RAG: Índice carregado com {self.index.ntotal} itens.")
            except Exception as e:
                print(f"RAG: Erro ao carregar índice: {e}")
        else:
            print("RAG: Arquivos de índice não encontrados. O sistema funcionará sem memória de longo prazo.")

    def search(self, query: str, k: int = 3):
        """Busca os k itens mais similares à query."""
        if not self.index or not self.embeddings_model:
            return []

        try:
            # Gera embedding da query
            query_embedding = self.embeddings_model.embed_query(query)
            query_np = np.array([query_embedding]).astype('float32')

            # Busca no FAISS
            distances, indices = self.index.search(query_np, k)

            results = []
            for i, idx in enumerate(indices[0]):
                if idx != -1 and idx < len(self.metadata):
                    item = self.metadata[idx]
                    results.append({
                        "item": item,
                        "distance": float(distances[0][i])
                    })
            
            return results
        except Exception as e:
            print(f"RAG: Erro na busca: {e}")
            return []

# Instância global
rag_service = RAGService()
