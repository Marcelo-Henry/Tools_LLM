import sys
def title(name):
    try:
        import setproctitle
        setproctitle.setproctitle(name)
    except ImportError:
        pass
    sys.stdout.write(f"\033]0;{name}\007")
    sys.stdout.flush()