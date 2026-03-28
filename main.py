import sys
import os
import subprocess
import threading
import time

# 1. Impressão do Banner imediata
print("\x1b[31m" + r"""
                          ___       ___           ___           ___     
                         /\__\     |\__\         /\  \         /\  \    
                        /:/  /     |:|  |       /::\  \       /::\  \   
                       /:/  /      |:|  |      /:/\:\  \     /:/\:\  \  
                      /:/  /       |:|__|__   /::\~\:\  \   /::\~\:\  \ 
                     /:/__/        /::::\__\ /:/\:\ \:\__\ /:/\:\ \:\__\
                     \:\  \       /:/~~/~    \/_|::\/:/  / \:\~\:\ \/__/
                      \:\  \     /:/  /         |:|::/  /   \:\ \:\__\  
                       \:\  \    \/__/          |:|\/__/     \:\ \/__/  
                        \:\__\                  |:|  |        \:\__\    
                         \/__/                   \|__|         \/__/    
""" + "\x1b[0m")

# 2. Verificação de dependências
def check_dependencies():
    import importlib.util
    
    missing = []
    # Mapeamento de nome no requirements.txt para nome do módulo importado (se diferente)
    packages = {
        "openai": "openai",
        "sentence-transformers": "sentence_transformers",
        "chromadb": "chromadb",
        "prompt_toolkit": "prompt_toolkit"
    }
    
    if not os.path.exists("requirements.txt"):
        return
        
    with open("requirements.txt", "r") as f:
        for line in f:
            pkg = line.strip().split("==")[0].split(">=")[0]
            if not pkg or pkg.startswith("#"): continue
            
            module_name = packages.get(pkg, pkg.replace("-", "_"))
            if importlib.util.find_spec(module_name) is None:
                missing.append(pkg)
                
    if missing:
        choice = input("Verifiquei e vi que você não instalou as dependências necessárias. Posso instalar por você? (y/n): ").lower()
        if choice == 'y':
            from utils import spinner
            print("Installing using 'python3 -m pip install -r requirements.txt'")
            
            stop_event = threading.Event()
            spinner_thread = threading.Thread(target=spinner, args=(stop_event, "Installing..."))
            spinner_thread.start()
            
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt", "--break-system-packages"], 
                                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            finally:
                stop_event.set()
                spinner_thread.join()
                print("✓ Dependências instaladas com sucesso!\n")
        else:
            sys.exit(0)

check_dependencies()

# 3. Pergunta o IP do servidor
def ask_server_url():
    print("Informe o endereço do servidor LLM (precisa ser OpenAI-Compatible).")
    print("Exemplo: http://1.2.3.4:1234\n")
    try:
        url = input("URL do servidor: ").strip()
    except (KeyboardInterrupt, EOFError):
        print()
        sys.exit(0)
    if not url:
        url = "http://localhost:1234"
    if not url.startswith("http"):
        url = "http://" + url
    return url.rstrip("/") + "/v1"

SERVER_URL = ask_server_url()

# 4. Imports pesados e inicialização
from utils import spinner, typewriter, get_input, title
title("lyre")
from agent import Agent, Planner
from tools import execute, undo
from rag import handle_rag_command, ensure_rag
import json

print("Comandos disponíveis:")
print("  /help      - Ver ajuda e exemplos")
print("  /rag       - Sistema de conhecimento")
print("  /model     - Ver modelo carregado no LM Studio")
print("  /undo      - Desfazer última operação")
print("  /quit      - Sair\n")

print("Olá! Como posso lhe ajudar?\n")

# Inicializa agente e título após banner
agent = Agent(use_rag=False, base_url=SERVER_URL)
rag = None
rag_enabled = False

while True:
    try:
        user_input = get_input("> ")
    except (EOFError, KeyboardInterrupt):
        break

    if user_input.lower() in ["/quit"]:
        break
    
    # Comando direto no terminal (oculto)
    if user_input.startswith("!"):
        cmd = user_input[1:].strip()
        if cmd:
            try:
                subprocess.run(cmd, shell=True)
            except Exception as e:
                print(f"❌ Erro: {e}\n")
        continue
    
    # Comando Clear (oculto)
    if user_input.lower() == "clear":
        os.system('clear' if os.name != 'nt' else 'cls')
        continue
    
    # Comando Model
    if user_input in ["/model"]:
        try:
            models = agent.client.models.list()
            if models.data:
                model = models.data[0]
                print(f"\n🤖 Modelo carregado: {model.id}\n")
            else:
                print("\n⚠️ Nenhum modelo carregado no LM Studio\n")
        except Exception as e:
            print(f"\n❌ Erro ao conectar com LM Studio: {e}\n")
        continue
    
    # Comando Help
    if user_input in ["/help"]:
        print("\n💬 Fale naturalmente com o agente:")
        print("  \"crie um arquivo hello.py que imprime olá\"")
        print("  \"liste os arquivos da pasta\"")
        print("  \"execute o comando ls\"")
        print("\n📚 Sistema RAG (memória de longo prazo):")
        print("  /rag       - Ver comandos disponíveis")
        print("\n⚙️ Outros comandos:")
        print("  /help      - Mostrar esta ajuda")
        print("  /model     - Ver modelo carregado")
        print("  /undo      - Desfazer última operação")
        print("  /quit      - Sair (/q, /exit, exit, quit)")
        print("\n💡 Dica: O agente executa ações automaticamente.")
        print("   Seja específico no que você quer!\n")
        continue
    
    # Comando Undo
    if user_input in ["/undo"]:
        result = undo.undo()
        print(f"\n{result}\n")
        continue
    
    # Comandos RAG
    if user_input.startswith("/rag"):
        rag_enabled, rag = handle_rag_command(user_input, rag_enabled, rag, agent)
        continue

    try:
        # Detecta se precisa de planejamento
        planner = Planner(agent)
        
        if planner.needs_planning(user_input):
            print("\n🤔 Analisando tarefa...\n")
            steps = planner.generate_plan(user_input)
            
            if steps and len(steps) > 1:
                planner.show_plan(steps)
                if not planner.confirm():
                    print("❌ Operação cancelada\n")
                    continue
        
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
            
            # Para o spinner após primeira resposta
            if step == 1:
                stop_event.set()
                spinner_thread.join()
            
            action = command.get("action", "unknown")
            
            # Se for resposta final, encerra o loop
            if action == "respond":
                stop_event.set()
                spinner_thread.join()
                typewriter(command.get("content", ""))
                print()
                break
            
            # Mostra comando shell antes de executar
            if action == "shell":
                cmd_to_run = command.get("command", "")
                print(f"\033[33m[shell]\033[0m Running: {cmd_to_run}")
            
            # Executa ação e captura resultado
            result = execute(command)
            result_msg = result if result else "✓ Executado com sucesso"
            action_result = f"[RESULT] {result_msg}"
            
            # Mostra resultado da ação
            if action == "shell":
                print(f"\033[32m→\033[0m {result_msg[:150]}{'...' if len(result_msg) > 150 else ''}")
            else:
                print(f"\033[33m[{action}]\033[0m {result_msg[:150]}{'...' if len(result_msg) > 150 else ''}")
        
        if step >= max_steps:
            stop_event.set()
            spinner_thread.join()
            print("⚠️ Limite de ações atingido")
            print()

    except KeyboardInterrupt:
        if 'stop_event' in locals():
            stop_event.set()
            spinner_thread.join()
        print("\n\nFui interrompiada pelo usuário...\n")
    except Exception as e:
        if 'stop_event' in locals():
            stop_event.set()
            spinner_thread.join()
        print("❌ Erro:", e)
