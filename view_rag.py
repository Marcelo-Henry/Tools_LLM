# view_rag.py
from rag import RAG

rag = RAG()

# Pega todos os documentos
results = rag.collection.get()

print(f"📚 Total de documentos no RAG: {len(results['ids'])}\n")

for i, (doc_id, doc) in enumerate(zip(results['ids'], results['documents']), 1):
    print(f"{i}. ID: {doc_id}")
    print(f"   Conteúdo: {doc[:100]}..." if len(doc) > 100 else f"   Conteúdo: {doc}")
    print()
