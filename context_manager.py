# context_manager.py

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
                        import json
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
