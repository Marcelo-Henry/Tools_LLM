# main.py
from agent import Agent
from tools import execute
from utils import spinner, typewriter
import json
import sys
import threading
import time
import readline

agent = Agent(use_rag=False)
rag = None  # RAG com lazy loading
rag_enabled = False

def ensure_rag():
    """Carrega RAG apenas quando necessário (lazy loading)"""
    global rag
    if rag is None:
        # Configurar ambiente apenas quando carregar RAG
        import os
        import warnings
        import logging
        from multiprocessing import Process, Queue
        
        os.environ['TOKENIZERS_PARALLELISM'] = 'false'
        os.environ['TRANSFORMERS_VERBOSITY'] = 'error'
        os.environ['HF_HUB_DISABLE_PROGRESS_BARS'] = '1'
        os.environ['HF_HUB_DISABLE_SYMLINKS_WARNING'] = '1'
        os.environ['HF_HUB_DISABLE_TELEMETRY'] = '1'
        warnings.filterwarnings('ignore')
        logging.getLogger('sentence_transformers').setLevel(logging.ERROR)
        logging.getLogger('huggingface_hub').setLevel(logging.ERROR)
        
        # Spinner em thread separada
        stop_event = threading.Event()
        spinner_thread = threading.Thread(target=lambda: rag_loading_spinner(stop_event))
        spinner_thread.daemon = True
        spinner_thread.start()
        
        from rag import RAG
        rag = RAG()
        
        stop_event.set()
        spinner_thread.join()
        print("\r✅ RAG carregado!                                    \n")
    return rag

def rag_loading_spinner(stop_event):
    """Spinner animado para carregamento do RAG"""
    frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
    idx = 0
    while not stop_event.is_set():
        sys.stdout.write(f"\r{frames[idx]} Carregando RAG...")
        sys.stdout.flush()
        idx = (idx + 1) % len(frames)
        time.sleep(0.08)
    sys.stdout.write("\r" + " " * 40 + "\r")
    sys.stdout.flush()

time.sleep(0.5)
print("\033[94m" + """
             ⢀⣴⣶⣶⣦⡀                ⢀⣴⣶⣶⣦⡀                  ⢀⣴⣶⣶⣦⡀         ⢀⣴⣶⣶⣦⡀
            ⢰⣿⠋⠁⠈⠙⣿⡆              ⢰⣿⠋⠁⠈⠙⣿⡆                ⢰⣿⠋⠁  ⣷⡀       ⢀⣾  ⠈⠙⣿⡆
            ⢸⣿     ⣿⡇             ⢸⣿     ⣿⡇               ⢸⣿     ⠹⣷⡀    ⣴⡿      ⣿⡇
            ⢸⣿     ⣿⡇             ⢸⣿     ⣿⡇               ⢸⣿      ⠹⣷⡀   ⡿       ⣿⡇
            ⢸⣿     ⣿⡇             ⢸⣿     ⣿⡇               ⢸⣿  ⣿⡇⣷  ⠹⣷⣦⣾⠏ ⢀⣾⣿⡇   ⣿⡇
            ⢸⣿     ⣿⡇             ⢸⣿     ⣿⡇               ⢸⣿  ⣿⡇⣷⡀      ⣴⡿ ⣿⡇   ⣿⡇ 
            ⢸⣿     ⣿⡇             ⢸⣿     ⣿⡇               ⢸⣿  ⣿⡇ ⠹⣷⡀   ⡿   ⣿⡇   ⣿⡇
            ⢸⣿     ⣿⣄⡀            ⢸⣿     ⣿⣄⡀              ⢸⣿  ⣿⡇  ⠹⣷⣦⣾⠏    ⣿⡇   ⣿⡇
            ⢸⣿     ⠈⠻⠿⠿⠿⠿⠿⠿⣷⡀     ⢸⣿     ⠈⠻⠿⠿⠿⠿⠿⠿⣷⡀       ⢸⣿  ⣿⡇            ⣿⡇  ⣿⡇
            ⠸⣿⣄⡀            ⣿⡇    ⠸⣿⣄⡀           ⣿⡇       ⠸⣿⣄ ⣿⡇            ⣿⡇ ⣠⣿⠇
             ⠈⠻⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠟⠁       ⠈⠻⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠟⠁         ⠈⠻⠿⠟⠁            ⠈⠻⣿⠟⠁

""" + "\033[0m")
print("Hello! How can I help you today?\n")

print("Comandos disponíveis:")
print("  /help      - Ver ajuda e exemplos")
print("  /rag       - Sistema de conhecimento")
print("  /quit      - Sair")
print("\nDigite um comando em linguagem natural\n")

while True:
    user_input = input("\033[94m> \033[0m")

    if user_input.lower() in ["exit", "quit", "/bye", "/q", "/quit", ".exit", ".quit", ".q"]:
        break
    
    # Comando Help
    if user_input in ["/help", "help"]:
        print("\n💬 Fale naturalmente com o agente:")
        print("  \"crie um arquivo hello.py que imprime olá\"")
        print("  \"liste os arquivos da pasta\"")
        print("  \"execute o comando ls\"")
        print("\n📚 Sistema RAG (memória de longo prazo):")
        print("  /rag       - Ver comandos disponíveis")
        print("\n⚙️ Outros comandos:")
        print("  /help      - Mostrar esta ajuda")
        print("  /quit      - Sair (/q, /exit, exit, quit)")
        print("\n💡 Dica: O agente executa ações automaticamente.")
        print("   Seja específico no que você quer!\n")
        continue
    
    # Comandos RAG
    if user_input.startswith("/rag"):
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
            continue
        
        if cmd == "enable":
            ensure_rag()
            rag_enabled = True
            agent.use_rag = True
            agent.rag = rag
            print("✅ RAG habilitado!\n")
            continue
        
        if cmd == "disable":
            rag_enabled = False
            agent.use_rag = False
            print("⚪ RAG desabilitado\n")
            continue
        
        if cmd == "status":
            status = "✅ Habilitado" if rag_enabled else "⚪ Desabilitado"
            loaded = "Sim" if rag is not None else "Não"
            print(f"\n📊 Status do RAG:")
            print(f"  Estado: {status}")
            print(f"  Modelo carregado: {loaded}\n")
            continue
        
        if cmd == "add":
            if not rag_enabled:
                print("❌ RAG está desabilitado. Use /rag enable primeiro\n")
                continue
            
            ensure_rag()
            import glob
            content = parts[2] if len(parts) > 2 else ""
            
            if not content:
                print("❌ Uso: /rag add <texto> ou /rag add file:<path>\n")
                continue
            
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
                print(rag.add_documents([content]))
            continue
        
        if cmd == "view":
            if not rag_enabled:
                print("❌ RAG está desabilitado. Use /rag enable primeiro\n")
                continue
            
            ensure_rag()
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
            continue
        
        if cmd == "clear":
            if not rag_enabled:
                print("❌ RAG está desabilitado. Use /rag enable primeiro\n")
                continue
            
            ensure_rag()
            import chromadb
            client = chromadb.PersistentClient(path="./chroma_db")
            client.delete_collection("knowledge_base")
            print("✅ RAG limpo!\n")
            # Recriar instância
            rag = RAG()
            agent.rag = rag
            continue
        
        print(f"❌ Comando desconhecido: {cmd}")
        print("Use /rag help para ver comandos disponíveis\n")
        continue
        import glob
        content = user_input[5:]

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
