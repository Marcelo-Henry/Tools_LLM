# undo_system.py
import os
import shutil
import json
from datetime import datetime

UNDO_DIR = "./.undo_history"

class UndoSystem:
    def __init__(self):
        os.makedirs(UNDO_DIR, exist_ok=True)
        self.stack_file = os.path.join(UNDO_DIR, "stack.json")
        self.stack = self._load_stack()
    
    def _load_stack(self):
        if os.path.exists(self.stack_file):
            with open(self.stack_file, "r") as f:
                return json.load(f)
        return []
    
    def _save_stack(self):
        with open(self.stack_file, "w") as f:
            json.dump(self.stack, f, indent=2)
    
    def snapshot(self, action, path, content=None):
        """Salva estado antes de operação destrutiva"""
        timestamp = datetime.now().isoformat()
        snapshot_id = f"{len(self.stack)}_{timestamp}"
        
        operation = {
            "id": snapshot_id,
            "action": action,
            "path": path,
            "timestamp": timestamp
        }
        
        # Salva conteúdo antigo se arquivo existe
        if os.path.exists(path):
            backup_path = os.path.join(UNDO_DIR, f"{snapshot_id}.bak")
            shutil.copy2(path, backup_path)
            operation["backup"] = backup_path
            operation["existed"] = True
        else:
            operation["existed"] = False
        
        self.stack.append(operation)
        self._save_stack()
        return snapshot_id
    
    def undo(self):
        """Desfaz última operação"""
        if not self.stack:
            return "❌ Nenhuma operação para desfazer"
        
        op = self.stack.pop()
        self._save_stack()
        
        try:
            if op["action"] in ["write_file", "edit_file"]:
                if op["existed"]:
                    # Restaura backup
                    shutil.copy2(op["backup"], op["path"])
                    os.remove(op["backup"])
                    return f"✅ Restaurado: {op['path']}"
                else:
                    # Remove arquivo criado
                    if os.path.exists(op["path"]):
                        os.remove(op["path"])
                    return f"✅ Removido: {op['path']}"
            
            elif op["action"] == "delete_file":
                # Restaura arquivo deletado
                if "backup" in op:
                    shutil.copy2(op["backup"], op["path"])
                    os.remove(op["backup"])
                    return f"✅ Restaurado: {op['path']}"
            
            return f"✅ Desfeito: {op['action']} em {op['path']}"
        
        except Exception as e:
            # Recoloca na stack se falhar
            self.stack.append(op)
            self._save_stack()
            return f"❌ Erro ao desfazer: {e}"
    
    def clear(self):
        """Limpa histórico de undo"""
        for op in self.stack:
            if "backup" in op and os.path.exists(op["backup"]):
                os.remove(op["backup"])
        self.stack = []
        self._save_stack()
        return "✅ Histórico de undo limpo"
    
    def list_operations(self):
        """Lista operações disponíveis para undo"""
        if not self.stack:
            return "Nenhuma operação no histórico"
        
        result = []
        for i, op in enumerate(reversed(self.stack), 1):
            result.append(f"{i}. {op['action']} - {op['path']} ({op['timestamp']})")
        return "\n".join(result)
