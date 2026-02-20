# main.py
from agent import Agent
from tools import execute
import json
import sys
import threading
import time
import readline
from rag import RAG

agent = Agent(use_rag=True)
rag = RAG()  # Instância global do RAG

def spinner(stop_event):
    frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
    idx = 0
    while not stop_event.is_set():
        sys.stdout.write(f"\r{frames[idx]} Thinking...")
        sys.stdout.flush()
        idx = (idx + 1) % len(frames)
        time.sleep(0.07)
    sys.stdout.write("\r" + " " * 30 + "\r")
    sys.stdout.flush()

def typewriter(text, delay=0.01):
    """Efeito de digitação para texto"""
    for char in text:
        sys.stdout.write(char)
        sys.stdout.flush()
        time.sleep(delay)
    print()  # Nova linha no final
    
time.sleep(0.5)
print("\033[94m" + """
                *@@@@@@*      *@@@@@@*      *@@@@@@mm   mm@@@@@@*
                   @@             @@             @@@@@@     @@@@@@
                   @@             @@            @@  @@@@   mm@@  @@@@
                  @@             @@             @@    @@!! @@**  @@@@
                  @!      mm     @!      mm     !!    @@!!mm@@@@** @@@@
                  @!    ::@@     @!    ::@@     !!    **!!@@@@**   @@@@
                  !!      !!     !!      !!     !!    !!!!!!!!!!**  !!!
                  !:    !!!!     !:    !!!!     ::    **!!!!!!**   !!!
                :: ::!!::::::    :: ::!!::::::  :::::: ::    :: :: ::::::


""" + "\033[0m")
time.sleep(0.5)
print("Hello! How can I help you today?")
print("")
print("""
⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿
⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿
⣿⣿⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣿⣿
⣿⣿⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣿⣿
⣿⣿⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣿⣿
⣿⣿⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣿⣿
⣿⣿⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣿⣿
⣿⣿⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣿⣿
⣿⣿⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣿⣿
⣿⣿⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣿⣿
⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿
⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿
""")

print("Comandos RAG:")
print("  /add <texto>                    - Adicionar texto direto")
print("  /add file:<path>                - Adicionar arquivo")
print("  /add file:rag/whatsapp_campeas/*.txt  - Adicionar múltiplos arquivos")
print("  /view                           - Ver documentos no RAG")
print("  /clear                          - Limpar RAG")
print("\nDigite um comando em linguagem natural\n")

while True:
    user_input = input("\033[94m> \033[0m")

    if user_input.lower() in ["exit", "quit", "/bye", "/q", "/quit", ".exit", ".quit", ".q"]:
        break
    
    # Comandos RAG
    if user_input.startswith("/add "):
        import glob
        content = user_input[5:]
        
        # Verificar se é um arquivo
        if content.startswith("file:"):
            file_pattern = content[5:]
            files = glob.glob(file_pattern)
            
            if not files:
                print(f"❌ Nenhum arquivo encontrado: {file_pattern}\n")
                continue
            
            for file_path in files:
                try:
                    result = rag.add_from_file(file_path)
                    print(f"✅ {file_path}: {result}")
                except Exception as e:
                    print(f"❌ {file_path}: {e}")
            print()
        else:
            # Adicionar texto direto
            print(rag.add_documents([content]))
        continue
    
    if user_input == "/view":
        results = rag.collection.get()
        total = len(results['ids'])
        print(f"📚 Total: {total} documento{'s' if total != 1 else ''}\n")
        if total == 0:
            print("Nenhum documento no RAG ainda.\n")
        else:
            for i, (doc_id, doc) in enumerate(zip(results['ids'], results['documents']), 1):
                preview = doc[:80] + "..." if len(doc) > 80 else doc
                print(f"{i}. {preview}")
        print()
        continue
    
    if user_input == "/clear":
        import chromadb
        client = chromadb.PersistentClient(path="./chroma_db")
        client.delete_collection("knowledge_base")
        print("✅ RAG limpo!\n")
        # Recriar instância
        rag = RAG()
        continue

    try:
        stop_event = threading.Event()
        spinner_thread = threading.Thread(target=spinner, args=(stop_event,))
        spinner_thread.start()
        
        # Loop de raciocínio: LLM executa ações até decidir responder
        max_steps = 30  # Limite de segurança aumentado
        step = 0
        action_result = None
        
        while step < max_steps:
            command = agent.think(user_input if step == 0 else "", action_result)
            step += 1
            
            action = command.get("action", "unknown")
            
            # Debug: mostra JSON cru
            print(f"\n\033[90m[DEBUG] {json.dumps(command, ensure_ascii=False)}\033[0m")
            
            # Se for resposta final, encerra o loop
            if action == "respond":
                stop_event.set()
                spinner_thread.join()
                typewriter(command.get("content", ""))
                print()
                break
            
            # Executa ação e captura resultado
            result = execute(command)
            result_msg = result if result else "✓ Executado com sucesso"
            action_result = f"[RESULT] {result_msg}"
            
            # Mostra ação executada
            print(f"\033[33m[{action}]\033[0m {result_msg[:150]}{'...' if len(result_msg) > 150 else ''}")
        
        if step >= max_steps:
            stop_event.set()
            spinner_thread.join()
            print("⚠️ Limite de ações atingido")
            print()

    except Exception as e:
        if 'stop_event' in locals():
            stop_event.set()
            spinner_thread.join()
        print("❌ Erro:", e)
