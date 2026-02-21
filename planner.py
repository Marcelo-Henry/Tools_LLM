# planner.py
import re

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
