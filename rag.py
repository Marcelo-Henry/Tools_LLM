# rag.py
from sentence_transformers import SentenceTransformer
import chromadb
import os

class RAG:
    def __init__(self, collection_name="knowledge_base"):
        self.embedder = SentenceTransformer('all-MiniLM-L6-v2')
        self.client = chromadb.PersistentClient(path="./chroma_db")
        
        try:
            self.collection = self.client.get_collection(collection_name)
        except:
            self.collection = self.client.create_collection(collection_name)
    
    def add_documents(self, documents: list[str], ids: list[str] = None):
        """Adiciona documentos ao vector database"""
        if not ids:
            import time
            ids = [f"doc_{int(time.time()*1000)}_{i}" for i in range(len(documents))]
        
        embeddings = self.embedder.encode(documents).tolist()
        self.collection.add(documents=documents, embeddings=embeddings, ids=ids)
        return f"{len(documents)} documentos adicionados"
    
    def add_from_file(self, file_path: str):
        """Adiciona conteúdo de um arquivo ao RAG"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Divide em chunks (parágrafos)
        chunks = [p.strip() for p in content.split('\n\n') if p.strip()]
        ids = [f"{file_path}_{i}" for i in range(len(chunks))]
        
        return self.add_documents(chunks, ids)
    
    def search(self, query: str, n_results: int = 10) -> str:
        """Busca documentos relevantes"""
        query_embedding = self.embedder.encode([query]).tolist()
        results = self.collection.query(query_embeddings=query_embedding, n_results=n_results)
        
        if results['documents']:
            return "\n\n".join(results['documents'][0])
        return ""
