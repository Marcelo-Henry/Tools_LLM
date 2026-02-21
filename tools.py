# tools.py
import os
import subprocess
from utils import show_diff
from undo_system import UndoSystem

BASE_DIR = "./sandbox"
undo = UndoSystem()

def safe_path(path: str) -> str:
    full_path = os.path.abspath(os.path.join(BASE_DIR, path))
    base_path = os.path.abspath(BASE_DIR)

    if not full_path.startswith(base_path):
        raise PermissionError("Acesso fora da sandbox bloqueado")

    return full_path


def execute(command: dict):
    action = command.get("action")
    path = command.get("path", "")

    if action == "respond":
        return command.get("content", "")
    
    if action == "add_to_rag":
        from rag import RAG
        rag = RAG()
        content = command.get("content", "")
        if path:
            return rag.add_from_file(safe_path(path))
        elif content:
            return rag.add_documents([content])
        return "Nenhum conteúdo fornecido"

    if action == "list_files":
        target = safe_path(path)
        return os.listdir(target)

    if action == "read_file":
        target = safe_path(path)
        if not os.path.exists(target):
            return f"❌ Arquivo '{path}' não existe"
        with open(target, "r", encoding="utf-8") as f:
            return f.read()

    if action == "write_file":
        target = safe_path(path)
        
        # Snapshot antes de modificar
        undo.snapshot("write_file", target)
        
        # Lê conteúdo antigo se existir
        old_content = ""
        if os.path.exists(target):
            with open(target, "r", encoding="utf-8") as f:
                old_content = f.read()
        
        new_content = command.get("content", "")
        
        # Mostra diff
        show_diff(old_content, new_content, path, action)
        
        # Executa
        os.makedirs(os.path.dirname(target), exist_ok=True)
        with open(target, "w", encoding="utf-8") as f:
            f.write(new_content)
        return ""

    if action == "edit_file":
        target = safe_path(path)
        
        # Snapshot antes de modificar
        undo.snapshot("edit_file", target)
        
        # Lê conteúdo antigo
        old_content = ""
        if os.path.exists(target):
            with open(target, "r", encoding="utf-8") as f:
                old_content = f.read()
        
        new_content = command.get("content", "")
        
        # Mostra diff
        show_diff(old_content, new_content, path, action)
        
        # Executa
        with open(target, "w", encoding="utf-8") as f:
            f.write(new_content)
        return ""

    if action == "delete_file":
        target = safe_path(path)
        
        # Snapshot antes de deletar
        undo.snapshot("delete_file", target)
        
        os.remove(target)
        return "Arquivo deletado"

    if action == "shell":
        cmd = command.get("command", "")
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=safe_path("."), timeout=10)
            return result.stdout if result.returncode == 0 else f"Erro: {result.stderr}"
        except subprocess.TimeoutExpired:
            return "Erro: Comando excedeu timeout de 10s"
        except Exception as e:
            return f"Erro ao executar: {str(e)}"

    raise ValueError("Ação inválida")