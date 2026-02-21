# autocomplete.py
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.styles import Style
from prompt_toolkit.formatted_text import HTML

class CommandCompleter(Completer):
    def __init__(self):
        self.commands = [
            '/quit',
            '/help',
            '/model',
            '/rag', '/rag enable', '/rag disable', '/rag status',
            '/rag add', '/rag view', '/rag clear', '/rag help',
            '/undo'
        ]
    
    def get_completions(self, document, complete_event):
        text = document.text_before_cursor
        for cmd in self.commands:
            if cmd.startswith(text) and cmd != text:
                yield Completion(cmd, start_position=-len(text))

style = Style.from_dict({
    'prompt': '#5f87ff',  # Azul
    'completion-menu.completion': 'bg:#3a3a3a #ffffff',  # Cinza escuro com texto branco
    'completion-menu.completion.current': 'bg:#5f87ff #000000',  # Azul quando selecionado
})

completer = CommandCompleter()

def get_input(prompt_text='> '):
    session = PromptSession(
        completer=completer,
        style=style,
        complete_while_typing=True
    )
    user_input = session.prompt(HTML(f'<prompt>{prompt_text}</prompt>'))
    
    # Auto-completar se comando incompleto
    if user_input and not user_input.endswith(' '):
        # Buscar matches exatos primeiro (comandos base)
        exact_matches = [cmd for cmd in completer.commands 
                        if cmd.startswith(user_input) 
                        and cmd != user_input
                        and ' ' not in cmd[len(user_input):]]
        
        if len(exact_matches) == 1:
            return exact_matches[0]
        
        # Se não houver match exato único, buscar qualquer match único
        all_matches = [cmd for cmd in completer.commands 
                      if cmd.startswith(user_input) and cmd != user_input]
        
        if len(all_matches) == 1:
            return all_matches[0]
    
    return user_input
