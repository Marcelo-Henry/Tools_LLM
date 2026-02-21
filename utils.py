# utils.py
import sys
import time
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.styles import Style
from prompt_toolkit.formatted_text import HTML

def title(name):
    """Define o título da janela do terminal"""
    try:
        import setproctitle
        setproctitle.setproctitle(name)
    except ImportError:
        pass
    sys.stdout.write(f"\033]0;{name}\007")
    sys.stdout.flush()

def rag_spinner(stop_event):
    """Spinner para carregamento do RAG"""
    frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
    idx = 0
    while not stop_event.is_set():
        sys.stdout.write(f"\r{frames[idx]} Carregando RAG...")
        sys.stdout.flush()
        idx = (idx + 1) % len(frames)
        time.sleep(0.07)
    sys.stdout.write("\r" + " " * 30 + "\r")
    sys.stdout.flush()

def spinner(stop_event):
    """Spinner para thinking"""
    frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
    idx = 0
    while not stop_event.is_set():
        sys.stdout.write(f"\r{frames[idx]} Thinking...")
        sys.stdout.flush()
        idx = (idx + 1) % len(frames)
        time.sleep(0.07)
    sys.stdout.write("\r" + " " * 30 + "\r")
    sys.stdout.flush()

def typewriter(text, delay=0.01):
    """Efeito de digitação para texto"""
    print("\n\x1b[31m>\x1b[0m", end=" ")  # Linha em branco + > vermelho (instantâneo)
    for char in text:
        sys.stdout.write(char)
        sys.stdout.flush()
        time.sleep(delay)
    print()


# Autocomplete
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

_autocomplete_style = Style.from_dict({
    'prompt': '#ff0000',  # Vermelho
    'completion-menu.completion': 'bg:#3a3a3a #ffffff',  # Cinza escuro com texto branco
    'completion-menu.completion.current': 'bg:#5f87ff #000000',  # Azul quando selecionado
})

_completer = CommandCompleter()

def get_input(prompt_text='> '):
    """Input com autocomplete de comandos"""
    session = PromptSession(
        completer=_completer,
        style=_autocomplete_style,
        complete_while_typing=True
    )
    user_input = session.prompt(HTML(f'<prompt>{prompt_text}</prompt>'))
    
    # Auto-completar se comando incompleto
    if user_input and not user_input.endswith(' '):
        # Buscar matches exatos primeiro (comandos base)
        exact_matches = [cmd for cmd in _completer.commands 
                        if cmd.startswith(user_input) 
                        and cmd != user_input
                        and ' ' not in cmd[len(user_input):]]
        
        if len(exact_matches) == 1:
            return exact_matches[0]
        
        # Se não houver match exato único, buscar qualquer match único
        all_matches = [cmd for cmd in _completer.commands 
                      if cmd.startswith(user_input) and cmd != user_input]
        
        if len(all_matches) == 1:
            return all_matches[0]
    
    return user_input


# Diff Viewer
import difflib

def show_diff(old_content: str, new_content: str, filepath: str, action: str):
    """Mostra diff visual sem confirmação."""
    
    # Determina se é criação ou modificação
    is_new = not old_content
    tool_name = "write" if action == "write_file" else "write"
    
    # Header
    if is_new:
        print(f"\nI'll create the following file: \033[31m{filepath}\033[0m (using tool: {tool_name})")
    else:
        print(f"\nI'll modify the following file: \033[31m{filepath}\033[0m (using tool: {tool_name})")
    
    # Split em linhas
    old_lines = old_content.splitlines(keepends=True) if old_content else []
    new_lines = new_content.splitlines(keepends=True)
    
    # Gera diff unificado
    diff = list(difflib.unified_diff(old_lines, new_lines, lineterm=''))
    
    # Pula headers do unified_diff (primeiras 2 linhas)
    if len(diff) > 2:
        diff = diff[2:]
    
    # Mostra diff colorido com numeração
    print()
    new_line_num = 0
    for line in diff:
        if line.startswith('@@'):
            continue
        elif line.startswith('+'):
            new_line_num += 1
            print(f"\033[32m+   {new_line_num:>3}: {line[1:]}\033[0m", end='')
        elif line.startswith('-'):
            print(f"\033[31m-      : {line[1:]}\033[0m", end='')
        else:
            new_line_num += 1
            print(f"    {new_line_num:>3}: {line[1:]}", end='')
    
    # Se não houver diff (arquivo idêntico), mostra conteúdo
    if not diff:
        for i, line in enumerate(new_lines, 1):
            print(f"\033[32m+   {i:>3}: {line}\033[0m", end='')
    
    print()  # Nova linha final
