# agent.py
from openai import OpenAI
import json
import re
#192.168.0.103
BASE_URL = "http://192.168.0.103:1234/v1" # Aqui, você precisa colocar o IP do seu servidor local onde o LM Studio está rodando. Exemplo: "http://(IP_DO_SEU_SERVIDOR):1234/v1"
MODEL_NAME = "tanto_faz"
MAX_HISTORY = 20  # Número máximo de mensagens no histórico

SYSTEM_PROMPT = """You are an autonomous file management system..
Every responde NEED be in JSON format, following this structure:
{"action": "ACTION", "path": "FILE", "content": "TEXT"}
or, If you don't have to create, edit, read or delete a file, just respond with:
{"action": "ACTION", "content": "TEXT"}

Available actions:
- list_files, read_file, write_file, edit_file, delete_file, shell, respond

Format: {"action": "ACTION", "path": "FILE", "content": "TEXT"}

Respond in Portuguese (Brazil).

⚠️ EXECUTION RULES:
1. Return ONLY ONE JSON object per response
2. NEVER write [RESULT] - the system will provide it
3. After you return JSON, system executes and shows result
4. Then you decide the next action based on the result

🎨 BE CREATIVE - COMBINE TOOLS:
You have LIMITED tools, but you can COMBINE them creatively to achieve complex tasks!

Examples of creative combinations:
- Delete a specific line? → read_file + edit_file (rewrite without that line)
- Rename file? → read_file + write_file (new name) + delete_file (old name)
- Copy file? → read_file + write_file (new location)
- Insert line at position? → read_file + edit_file (split and rejoin)
- Replace text? → read_file + edit_file (with replacement)
- Append to file? → read_file + edit_file (add content at end)
- Count lines? → read_file + shell (wc -l) OR read_file + respond (count \\n)
- Search in files? → shell (grep) OR read_file + analyze

Think: "I don't have tool X, but I can achieve it by combining tools A + B + C!"

Example - Delete line 2 from file.txt:
Step 1: {"action": "read_file", "path": "file.txt"}
Step 2: [RESULT shows 3 lines]
Step 3: {"action": "edit_file", "path": "file.txt", "content": "line1\\nline3"}
Step 4: {"action": "respond", "content": "Linha 2 removida com sucesso!"}

Example - Rename old.txt to new.txt:
Step 1: {"action": "read_file", "path": "old.txt"}
Step 2: [RESULT shows content]
Step 3: {"action": "write_file", "path": "new.txt", "content": "<content from step 2>"}
Step 4: {"action": "delete_file", "path": "old.txt"}
Step 5: {"action": "respond", "content": "Arquivo renomeado de old.txt para new.txt!"}

🧠 REASONING FRAMEWORK:
Before each action, ask yourself:
1. "What information do I have?"
2. "What information do I need?"
3. "What action gets me that information?"
4. "Is the ENTIRE task complete, or do I need to continue?"

IMPORTANT: Use "respond" ONLY when the ENTIRE task is finished, not after each step!

Example of good reasoning:
User: "delete files that say they are not important"

Step 1: What do I have? → Nothing yet
        What do I need? → List of files
        Action: {"action": "shell", "command": "ls"}

Step 2: What do I have? → file1.txt, file2.txt, file3.txt
        What do I need? → Content of file1.txt
        Task complete? → NO, need to check all files
        Action: {"action": "read_file", "path": "file1.txt"}

Step 3: What do I have? → file1.txt says "NOT IMPORTANT"
        Analysis: Should delete this file
        Task complete? → NO, still have file2.txt and file3.txt to check
        Action: {"action": "delete_file", "path": "file1.txt"}

Step 4: What do I have? → file1.txt deleted
        What do I need? → Content of file2.txt
        Task complete? → NO, still have file2.txt and file3.txt
        Action: {"action": "read_file", "path": "file2.txt"}

Step 5: What do I have? → file2.txt says "IMPORTANT"
        Analysis: Should NOT delete, keep it
        Task complete? → NO, still have file3.txt to check
        Action: {"action": "read_file", "path": "file3.txt"}

Step 6: What do I have? → file3.txt says "NOT IMPORTANT"
        Analysis: Should delete this file
        Task complete? → NO, need to delete it first
        Action: {"action": "delete_file", "path": "file3.txt"}

Step 7: What do I have? → All files checked and processed
        Task complete? → YES! All files were analyzed
        Action: {"action": "respond", "content": "Deletei file1.txt e file3.txt. Mantive file2.txt pois é importante."}

Key principle: GATHER ALL DATA → PROCESS ALL ITEMS → RESPOND ONCE AT THE END

Remember: "respond" = task is COMPLETELY finished!

Examples:

User: list files
Assistant: {"action": "list_files", "path": "."}

User: read the files
Assistant: {"action": "read_file", "path": "hi.txt"}

User: create hello.py with print hello
Assistant: {"action": "write_file", "path": "hello.py", "content": "print('hello')"}

User: create test.py that asks name and prints it
Assistant: {"action": "write_file", "path": "test.py", "content": "name = input('Name: ')\\nprint(f'Hello {name}')"}

User: edit hello.py to add a function
Assistant: {"action": "edit_file", "path": "hello.py", "content": "def greet():\\n    print('hello')\\n\\ngreet()"}

User: read config.json
Assistant: {"action": "read_file", "path": "config.json"}

User: delete old.txt
Assistant: {"action": "delete_file", "path": "old.txt"}

User: run ls command
Assistant: {"action": "shell", "command": "ls -la"}

User: thanks
Assistant: {"action": "respond", "content": "Done!"}

User: what time is it
Assistant: {"action": "respond", "content": "I can only manage files, not tell time"}

User: create app.py with input and length check
Assistant: {"action": "write_file", "path": "app.py", "content": "name = input('Your name: ')\\nprint(f'Length: {len(name)}')"}

User: edit app.py to add greeting
Assistant: {"action": "edit_file", "path": "app.py", "content": "name = input('Your name: ')\\nprint(f'Hello {name}!')\\nprint(f'Length: {len(name)}')"}

REMEMBER: Use \\n for newlines, NEVER use triple quotes!

You can chain multiple actions by returning a JSON array:
[{"action": "write_file", "path": "test.txt", "content": "hello"}, {"action": "read_file", "path": "test.txt"}]

IMPORTANTE: Quando receber contexto do RAG, responda APENAS com base nas informações fornecidas. 
NÃO invente, NÃO suponha, NÃO adicione informações que não estejam no contexto.
Se a informação não estiver no contexto, diga claramente que não encontrou."""


class ContextManager:
    def __init__(self, max_tokens=6000):
        self.max_tokens = max_tokens
    
    def estimate_tokens(self, text):
        """Estimativa rápida de tokens (3 chars ≈ 1 token)"""
        return len(str(text)) // 3
    
    def compress_history(self, history):
        """Comprime histórico mantendo contexto essencial"""
        if not history:
            return history
        
        total_tokens = sum(self.estimate_tokens(msg["content"]) for msg in history)
        
        if total_tokens <= self.max_tokens:
            return history
        
        # Mantém últimas 4 mensagens + resumo do resto
        recent = history[-4:]
        old = history[:-4]
        
        if not old:
            return recent
        
        # Cria resumo do histórico antigo
        summary = self._summarize_old_messages(old)
        
        return [{"role": "system", "content": f"[Resumo do histórico anterior: {summary}]"}] + recent
    
    def _summarize_old_messages(self, messages):
        """Resume mensagens antigas"""
        actions = []
        for msg in messages:
            if msg["role"] == "assistant":
                content = msg["content"]
                # Extrai ações do JSON
                if "action" in content:
                    try:
                        data = json.loads(content)
                        action = data.get("action", "")
                        path = data.get("path", "")
                        if action and path:
                            actions.append(f"{action}({path})")
                        elif action:
                            actions.append(action)
                    except:
                        pass
        
        if actions:
            return f"Executou {len(actions)} ações: {', '.join(actions[:5])}{'...' if len(actions) > 5 else ''}"
        return f"{len(messages)} mensagens anteriores"
    
    def truncate_output(self, text, max_chars=500):
        """Trunca outputs muito longos"""
        if len(text) <= max_chars:
            return text
        
        # Mostra início e fim
        half = max_chars // 2
        return f"{text[:half]}\n\n... ({len(text) - max_chars} caracteres omitidos) ...\n\n{text[-half:]}"


class Planner:
    def __init__(self, agent):
        self.agent = agent
    
    def needs_planning(self, user_input):
        """Detecta se tarefa precisa de planejamento"""
        keywords = [
            "todos", "cada", "múltiplos", "vários", "analise", 
            "procure", "encontre", "delete", "modifique", "refatore"
        ]
        return any(kw in user_input.lower() for kw in keywords)
    
    def generate_plan(self, user_input):
        """Gera plano de ações sem executar"""
        # Injeta instrução para gerar plano
        planning_prompt = f"""Tarefa: {user_input}

Antes de executar, liste TODAS as ações necessárias em ordem.
Formato: retorne JSON com {{"action": "plan", "steps": ["passo 1", "passo 2", ...]}}

NÃO execute nada ainda, apenas planeje."""
        
        # Salva histórico original
        original_history = self.agent.history.copy()
        
        # Limpa histórico para planejar
        self.agent.history = []
        
        try:
            response = self.agent.think(planning_prompt)
            
            # Restaura histórico
            self.agent.history = original_history
            
            if isinstance(response, dict) and response.get("action") == "plan":
                return response.get("steps", [])
            
            # Fallback: extrai passos do conteúdo
            content = response.get("content", "")
            steps = re.findall(r'\d+\.\s*(.+)', content)
            return steps if steps else None
        
        except Exception:
            self.agent.history = original_history
            return None
    
    def show_plan(self, steps):
        """Mostra plano formatado"""
        print("\n📋 Plano de execução:\n")
        for i, step in enumerate(steps, 1):
            print(f"  {i}. {step}")
        print()
    
    def confirm(self):
        """Solicita confirmação do usuário"""
        while True:
            response = input("Executar este plano? (y/n): ").strip().lower()
            if response in ['y', 'yes', 's', 'sim']:
                return True
            if response in ['n', 'no', 'não', 'nao']:
                return False
            print("Responda y (sim) ou n (não)")


class Agent:
    def __init__(self, use_rag=False):
        self.client = OpenAI(
            base_url=BASE_URL,
            api_key="lm-studio"
        )
        self.history = []
        self.use_rag = use_rag
        self.rag = None  # RAG será injetado externamente quando habilitado
        self.context_manager = ContextManager()
    
    def check_server(self):
        """Verifica se servidor está rodando e modelo carregado"""
        try:
            models = self.client.models.list()
            if not models.data:
                return False, "Ops! Como vou responder se eu não tem modelo carregado? Carrega um modelo aí e tenta de novo!"
            return True, None
        except Exception as e:
            error_msg = str(e).lower()
            if any(x in error_msg for x in ["connection", "refused", "timeout", "timed out"]):
                return False, f"Ops! O servidor está rodando? Pra mim deu erro aqui..."
            return False, f"Aconteceu um erro aqui: {str(e)}"
    
    def _log_json(self, parsed_json: dict, is_error: bool = False):
        """Salva JSON parseado em arquivo de log"""
        try:
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            prefix = "⚠️ " if is_error else ""
            with open(".txt", "a", encoding="utf-8") as f:
                f.write(f"{prefix}[{timestamp}] {json.dumps(parsed_json, ensure_ascii=False)}\n")
        except Exception:
            pass  # Falha silenciosa para não interromper fluxo

    def think(self, user_input: str, action_result: str = None) -> dict:
        # Buscar contexto relevante se RAG estiver ativado
        context = ""
        if self.use_rag and self.rag:
            context = self.rag.search(user_input)
            if context:
                print(f"🔍 RAG: Contexto encontrado ({len(context)} caracteres)")
                user_input = f"Context:\n{context}\n\nQuestion: {user_input}"
            else:
                print("🔍 RAG: Nenhum contexto relevante encontrado")
        
        # Se há resultado de ação anterior, adiciona ao histórico
        if action_result:
            # Trunca outputs muito longos
            truncated = self.context_manager.truncate_output(action_result)
            self.history.append({"role": "user", "content": truncated})
        else:
            # Adiciona mensagem do usuário ao histórico
            self.history.append({"role": "user", "content": user_input})
        
        # Comprime histórico se necessário
        self.history = self.context_manager.compress_history(self.history)
        
        # Reforça o papel do sistema a cada chamada
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "system", "content": "You are executing actions in a real system. Continue with the next action or respond when done."},
            {"role": "user", "content": "list files"},
            {"role": "assistant", "content": '{"action": "list_files", "path": "."}'},
            {"role": "user", "content": "create test.txt with hello"},
            {"role": "assistant", "content": '{"action": "write_file", "path": "test.txt", "content": "hello"}'},
            {"role": "user", "content": "thanks"},
            {"role": "assistant", "content": '{"action": "respond", "content": "You\'re welcome!"}'}
        ] + self.history
        
        try:
            response = self.client.chat.completions.create(
                model=MODEL_NAME,
                messages=messages,
                temperature=0,
                max_tokens=7000
            )
        except Exception as e:
            error_msg = str(e).lower()
            if any(x in error_msg for x in ["connection", "refused", "timeout", "timed out"]):
                return {"action": "respond", "content": "Ops! O servidor está rodando? Pra mim deu erro aqui..."}
            return {"action": "respond", "content": f"Aconteceu um erro aqui: {str(e)}"}

        content = response.choices[0].message.content.strip()
        
        # Remove markdown code blocks e extrai TODOS os JSONs
        import re
        json_blocks = []
        if "```" in content:
            # Extrai TODOS os blocos JSON dentro de markdown
            matches = re.findall(r'```(?:json)?\s*(\{.*?\})\s*```', content, re.DOTALL)
            if matches:
                json_blocks = matches
        
        # Se não encontrou em markdown, procura JSONs soltos
        if not json_blocks:
            # Procura todos os objetos JSON válidos com "action" (incluindo multiline e texto ao redor)
            matches = re.findall(r'\{[^{}]*"action"[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', content, re.DOTALL)
            for match in matches:
                json_blocks.append(match.strip())
        
        # Se ainda não encontrou, usa o conteúdo original
        if not json_blocks:
            json_blocks = [content]
        
        # Processa cada bloco JSON
        commands = []
        for block in json_blocks:
            # Adiciona resposta do assistente ao histórico (apenas o primeiro)
            if not commands:
                self.history.append({"role": "assistant", "content": block})

            # Remove tags <think> do DeepSeek R1
            if "<think>" in block:
                parts = block.split("</think>")
                if len(parts) > 1:
                    block = parts[1].strip()
                else:
                    block = block.split("<think>")[0].strip()
                    if not block:
                        continue

            # 🔒 Parser defensivo
            try:
                parsed = json.loads(block)
                commands.append(parsed)
                self._log_json(parsed)
            except json.JSONDecodeError:
                # Salva JSON com erro de parsing
                self._log_json({"raw_content": block, "error": "JSONDecodeError"}, is_error=True)
                
                # Fix: Corrige barras invertidas mal escapadas (\ seguido de espaço/newline)
                block = re.sub(r'\\\s+', '', block)
                
                # Tenta novamente após limpeza
                try:
                    parsed = json.loads(block)
                    commands.append(parsed)
                    self._log_json(parsed)
                    continue
                except:
                    pass
                
                # Procura por padrão {"action": ...}
                match = re.search(r'\{[^}]*"action"[^}]*\}', block)
                if match:
                    try:
                        parsed = json.loads(match.group(0))
                        commands.append(parsed)
                        self._log_json(parsed)
                        continue
                    except:
                        pass
                
                # 🧠 Parser inteligente: detecta intenção de criar arquivo
                file_match = re.search(r'#\s*Arquivo:\s*(\S+)\s*\n+(.*)', block, re.DOTALL)
                if file_match:
                    filename = file_match.group(1)
                    code = file_match.group(2)
                    code = re.sub(r'```\w*\n?', '', code).strip()
                    code = re.split(r'\n\nTo run this', code)[0].strip()
                    recovered = {
                        "action": "write_file",
                        "path": filename,
                        "content": code
                    }
                    commands.append(recovered)
                    self._log_json(recovered)
                    continue
        
        # Se não conseguiu parsear nenhum comando, retorna erro
        if not commands:
            return {"action": "respond", "content": f"Erro: modelo retornou texto ao invés de JSON:\n{content}"}
        
        # Retorna apenas o PRIMEIRO comando (executa passo a passo)
        return commands[0]
