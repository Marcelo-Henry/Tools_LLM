# agent.py
from openai import OpenAI
import json

BASE_URL = "http://127.0.0.1:1234/v1"
MODEL_NAME = "tanto_faz"
MAX_HISTORY = 20  # Número máximo de mensagens no histórico

SYSTEM_PROMPT = """Respond with JSON only. Format: {"action": "ACTION", "path": "FILE", "content": "TEXT"}
Actions: list_files, read_file, write_file, edit_file, delete_file, shell, respond

You can chain multiple actions by returning a JSON array:
[{"action": "write_file", "path": "test.txt", "content": "hello"}, {"action": "read_file", "path": "test.txt"}]"""

class Agent:
    def __init__(self):
        self.client = OpenAI(
            base_url=BASE_URL,
            api_key="lm-studio"
        )
        self.history = []

    def think(self, user_input: str) -> dict:
        # Adiciona mensagem do usuário ao histórico
        self.history.append({"role": "user", "content": user_input})
        
        # Mantém apenas as últimas MAX_HISTORY mensagens
        if len(self.history) > MAX_HISTORY:
            self.history = self.history[-MAX_HISTORY:]
        
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
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
            max_tokens=2000
        )

        content = response.choices[0].message.content.strip()
        
        # Remove blocos markdown ```json
        if content.startswith("```"):
            lines = content.split("\n")
            content = "\n".join(lines[1:-1]) if len(lines) > 2 else content
            if content.startswith("json"):
                content = content[4:].strip()
        
        # Adiciona resposta do assistente ao histórico
        self.history.append({"role": "assistant", "content": content})

        # Remove tags <think> do DeepSeek R1
        if "<think>" in content:
            parts = content.split("</think>")
            if len(parts) > 1:
                content = parts[1].strip()
            else:
                # Se não fechou o </think>, pega tudo depois de <think>
                content = content.split("<think>")[0].strip()
                if not content:
                    raise ValueError("Modelo retornou apenas raciocínio, sem JSON")

        # Remove markdown code blocks se existirem
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
            content = content.strip()

        # 🔒 Parser defensivo
        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            import re
            
            # Tenta extrair action e path do JSON quebrado
            action_match = re.search(r'"action":\s*"(\w+)"', content)
            path_match = re.search(r'"path":\s*"([^"]+)"', content)
            
            if action_match:
                action = action_match.group(1)
                result = {"action": action}
                
                if path_match:
                    result["path"] = path_match.group(1)
                
                # Se for write_file e não tem content válido, extrai o texto após path
                if action == "write_file" and "content" not in content:
                    # Pega tudo após "path": "xxx", até o final
                    remaining = content[path_match.end():]
                    # Remove lixo inicial e pega o texto útil
                    text = re.sub(r'^[^a-zA-Z]+', '', remaining).strip()
                    result["content"] = text
                
                return result
            
            raise ValueError(f"Resposta não é JSON válido:\n{content}\nErro: {e}")
