# main.py
import sys
from utils import title
title("llm")
from agent import Agent, Planner
from tools import execute, undo
from utils import spinner, typewriter, get_input
from rag import handle_rag_command, ensure_rag
import json
import threading
import time

agent = Agent(use_rag=False)
rag = None
rag_enabled = False

print("\x1b[31m" + """
                ⢀⣴⣶⣶⣦⡀            ⢀⣴⣶⣶⣦⡀             ⢀⣴⣶⣶⣦⡀         ⢀⣴⣶⣶⣦⡀
               ⢰⣿⠋⠁⠈⠙⣿⡆          ⢰⣿⠋⠁⠈⠙⣿⡆           ⢰⣿⠋⠁  ⣷⡀       ⢀⣾  ⠈⠙⣿⡆
               ⢸⣿     ⣿⡇         ⢸⣿     ⣿⡇          ⢸⣿     ⠹⣷⡀    ⣴⡿      ⣿⡇
               ⢸⣿     ⣿⡇         ⢸⣿     ⣿⡇          ⢸⣿      ⠹⣷⡀   ⡿       ⣿⡇
               ⢸⣿     ⣿⡇         ⢸⣿     ⣿⡇          ⢸⣿  ⣿⡇⣷  ⠹⣷⣦⣾⠏ ⢀⣾⣿⡇   ⣿⡇
               ⢸⣿     ⣿⡇         ⢸⣿     ⣿⡇          ⢸⣿  ⣿⡇⣷⡀      ⣴⡿ ⣿⡇   ⣿⡇ 
               ⢸⣿     ⣿⡇         ⢸⣿     ⣿⡇          ⢸⣿  ⣿⡇ ⠹⣷⡀   ⡿   ⣿⡇   ⣿⡇
               ⢸⣿     ⣿⣄⡀        ⢸⣿     ⣿⣄⡀         ⢸⣿  ⣿⡇  ⠹⣷⣦⣾⠏    ⣿⡇   ⣿⡇
               ⢸⣿     ⠈⠻⠿⠿⠿⠿⠿⠿⣷⡀ ⢸⣿     ⠈⠻⠿⠿⠿⠿⠿⠿⣷⡀  ⢸⣿  ⣿⡇            ⣿⡇  ⣿⡇
               ⠸⣿⣄⡀           ⣿⡇ ⠸⣿⣄⡀           ⣿⡇  ⠸⣿⣄ ⣿⡇            ⣿⡇ ⣠⣿⠇
                ⠈⠻⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠟⠁   ⠈⠻⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿⠟⠁    ⠈⠻⠿⠟⠁            ⠈⠻⣿⠟⠁

""" + "\x1b[0m")

print("Comandos disponíveis:")
print("  /help      - Ver ajuda e exemplos")
print("  /rag       - Sistema de conhecimento")
print("  /model     - Ver modelo carregado no LM Studio")
print("  /undo      - Desfazer última operação")
print("  /quit      - Sair\n")

print("Olá! Como posso lhe ajudar?\n")
while True:
    try:
        user_input = get_input("> ")
    except (EOFError, KeyboardInterrupt):
        break

    if user_input.lower() in ["/quit"]:
        break
    
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
