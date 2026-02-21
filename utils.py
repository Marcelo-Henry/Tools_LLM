# utils.py
import sys
import time

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
    for char in text:
        sys.stdout.write(char)
        sys.stdout.flush()
        time.sleep(delay)
    print()
