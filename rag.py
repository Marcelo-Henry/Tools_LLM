# rag.py
from sentence_transformers import SentenceTransformer
import chromadb
import glob
import threading
from utils import rag_spinner

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


def ensure_rag(rag):
    """Carrega RAG apenas quando necessário (lazy loading)"""
    if rag is None:
        import os
        import warnings
        import logging
        
        os.environ['TOKENIZERS_PARALLELISM'] = 'false'
        os.environ['TRANSFORMERS_VERBOSITY'] = 'error'
        os.environ['HF_HUB_DISABLE_PROGRESS_BARS'] = '1'
        os.environ['HF_HUB_DISABLE_SYMLINKS_WARNING'] = '1'
        os.environ['HF_HUB_DISABLE_TELEMETRY'] = '1'
        warnings.filterwarnings('ignore')
        logging.getLogger('sentence_transformers').setLevel(logging.ERROR)
        logging.getLogger('huggingface_hub').setLevel(logging.ERROR)
        
        stop_event = threading.Event()
        spinner_thread = threading.Thread(target=rag_spinner, args=(stop_event,))
        spinner_thread.daemon = True
        spinner_thread.start()
        
        rag = RAG()
        
        stop_event.set()
        spinner_thread.join()
        print("✅ RAG carregado!\n")
    return rag


def handle_rag_command(user_input, rag_enabled, rag, agent):
    """Processa comandos /rag"""
    parts = user_input.split(maxsplit=2)
    cmd = parts[1] if len(parts) > 1 else "help"
    
    if cmd in ["help", ""]:
        status = "✅ Habilitado" if rag_enabled else "⚪ Desabilitado"
        print(f"\n📚 Sistema RAG (Retrieval-Augmented Generation)\n")
        print(f"Status: {status}\n")
        print("Comandos:")
        print("  /rag enable              - Habilitar RAG")
        print("  /rag disable             - Desabilitar RAG")
        print("  /rag status              - Ver status atual")
        print("  /rag add <texto>         - Adicionar texto")
        print("  /rag add file:<path>     - Adicionar arquivo")
        print("  /rag view                - Ver documentos")
        print("  /rag clear               - Limpar base de conhecimento")
        print("  /rag help                - Mostrar esta ajuda\n")
        return rag_enabled, rag
    
    if cmd == "enable":
        rag = ensure_rag(rag)
        rag_enabled = True
        agent.use_rag = True
        agent.rag = rag
        print("✅ RAG habilitado!\n")
        return rag_enabled, rag
    
    if cmd == "disable":
        rag_enabled = False
        agent.use_rag = False
        print("⚪ RAG desabilitado\n")
        return rag_enabled, rag
    
    if cmd == "status":
        status = "✅ Habilitado" if rag_enabled else "⚪ Desabilitado"
        loaded = "Sim" if rag is not None else "Não"
        print(f"\n📊 Status do RAG:")
        print(f"  Estado: {status}")
        print(f"  Modelo carregado: {loaded}\n")
        return rag_enabled, rag
    
    if cmd == "add":
        if not rag_enabled:
            print("❌ RAG está desabilitado. Use /rag enable primeiro\n")
            return rag_enabled, rag
        
        rag = ensure_rag(rag)
        content = parts[2] if len(parts) > 2 else ""
        
        if not content:
            print("❌ Uso: /rag add <texto> ou /rag add file:<path>\n")
            return rag_enabled, rag
        
        if content.startswith("file:"):
            file_pattern = content[5:]
            files = glob.glob(file_pattern)
            
            if not files:
                print(f"❌ Nenhum arquivo encontrado: {file_pattern}\n")
                return rag_enabled, rag
            
            for file_path in files:
                try:
                    result = rag.add_from_file(file_path)
                    print(f"✅ {file_path}: {result}")
                except Exception as e:
                    print(f"❌ {file_path}: {e}")
            print()
        else:
            print(rag.add_documents([content]))
        return rag_enabled, rag
    
    if cmd == "view":
        if not rag_enabled:
            print("❌ RAG está desabilitado. Use /rag enable primeiro\n")
            return rag_enabled, rag
        
        rag = ensure_rag(rag)
        results = rag.collection.get()
        total = len(results['ids'])
        print(f"\n📚 Total: {total} documento{'s' if total != 1 else ''}\n")
        if total == 0:
            print("Nenhum documento no RAG ainda.\n")
        else:
            for i, (doc_id, doc) in enumerate(zip(results['ids'], results['documents']), 1):
                preview = doc[:80] + "..." if len(doc) > 80 else doc
                print(f"{i}. {preview}")
        print()
        return rag_enabled, rag
    
    if cmd == "clear":
        if not rag_enabled:
            print("❌ RAG está desabilitado. Use /rag enable primeiro\n")
            return rag_enabled, rag
        
        rag = ensure_rag(rag)
        client = chromadb.PersistentClient(path="./chroma_db")
        client.delete_collection("knowledge_base")
        print("✅ RAG limpo!\n")
        rag = RAG()
        agent.rag = rag
        return rag_enabled, rag
    
    print(f"❌ Comando desconhecido: {cmd}")
    print("Use /rag help para ver comandos disponíveis\n")
    return rag_enabled, rag
