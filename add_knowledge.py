# add_knowledge.py
from rag import RAG

rag = RAG()

# Exemplo: adicionar documentos manualmente
docs = [
    "Python é uma linguagem de programação de alto nível, interpretada e de propósito geral.",
    "JavaScript é usado principalmente para desenvolvimento web front-end e back-end com Node.js.",
    "Machine Learning é um subcampo da inteligência artificial focado em algoritmos que aprendem com dados."
]

print(rag.add_documents(docs))

# Ou adicionar de um arquivo
# print(rag.add_from_file("./sandbox/conhecimento.txt"))

print("✅ Conhecimento adicionado ao RAG!")
