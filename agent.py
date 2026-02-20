# agent.py
from openai import OpenAI
import json
from rag import RAG

BASE_URL = "http://192.168.0.103:1234/v1"
MODEL_NAME = "tanto_faz"
MAX_HISTORY = 20  # Número máximo de mensagens no histórico

SYSTEM_PROMPT = """You are an autonomous file management system.

YOU CANT, NEVER, WITH NO NEGOCIATING, DONT SPECIFY THE ACTIONS.
EVERY RESPONDE MUST BE LIKE THIS:
{"action": "ACTION", "path": "FILE", "content": "TEXT"}
OR, IF YOU DONT NEED TO MAKE ANY FILES:
{"action": "ACTION", "content": "TEXT"}

Available actions:
- list_files, read_file, write_file, edit_file, delete_file, shell, respond, whatsapp, add_to_rag

Format: {"action": "ACTION", "path": "FILE", "content": "TEXT"}

Respond in Portuguese (Brazil).

⚠️ EXECUTION RULES:
1. Return ONLY ONE JSON object per response
2. NEVER write [RESULT] - the system will provide it
3. After you return JSON, system executes and shows result
4. Then you decide the next action based on the result

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

REMEMBER: Use \\n for newlines, NEVER use triple quotes!"""
You can chain multiple actions by returning a JSON array:
[{"action": "write_file", "path": "test.txt", "content": "hello"}, {"action": "read_file", "path": "test.txt"}]

add_to_rag: Add knowledge to RAG. Use "path" for files or "content" for direct text.

IMPORTANTE: Quando receber contexto do RAG, responda APENAS com base nas informações fornecidas. 
NÃO invente, NÃO suponha, NÃO adicione informações que não estejam no contexto.
Se a informação não estiver no contexto, diga claramente que não encontrou."""

class Agent:
    def __init__(self, use_rag=False):
        self.client = OpenAI(
            base_url=BASE_URL,
            api_key="lm-studio"
        )
        self.history = []
        self.use_rag = use_rag
        self.rag = RAG() if use_rag else None

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
            self.history.append({"role": "user", "content": action_result})
        else:
            # Adiciona mensagem do usuário ao histórico
            self.history.append({"role": "user", "content": user_input})
        
        # Mantém apenas as últimas MAX_HISTORY mensagens
        if len(self.history) > MAX_HISTORY:
            self.history = self.history[-MAX_HISTORY:]
        
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
        
        response = self.client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            temperature=0,
            max_tokens=7000
        )

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
            # Procura todos os objetos JSON válidos (incluindo multiline)
            matches = re.findall(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', content, re.DOTALL)
            for match in matches:
                # Valida se parece com JSON válido (tem "action")
                if '"action"' in match:
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
                commands.append(json.loads(block))
            except json.JSONDecodeError:
                # Fix: Remove triple quotes e corrige escapes
                if '"""' in block:
                    block = block.replace('"""', '')
                
                # Fix: Corrige barras invertidas mal escapadas (\ seguido de espaço/newline)
                block = re.sub(r'\\\s+', '', block)
                
                # Tenta novamente após limpeza
                try:
                    commands.append(json.loads(block))
                    continue
                except:
                    pass
                
                # Procura por padrão {"action": ...}
                match = re.search(r'\{[^}]*"action"[^}]*\}', block)
                if match:
                    try:
                        commands.append(json.loads(match.group(0)))
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
                    commands.append({
                        "action": "write_file",
                        "path": filename,
                        "content": code
                    })
                    continue
        
        # Se não conseguiu parsear nenhum comando, retorna erro
        if not commands:
            return {"action": "respond", "content": f"Erro: modelo retornou texto ao invés de JSON:\n{content}"}
        
        # Retorna apenas o PRIMEIRO comando (executa passo a passo)
        return commands[0]
