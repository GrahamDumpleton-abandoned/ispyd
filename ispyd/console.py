import code
import os
import sys
import threading

import __builtin__

from ispyd.wrapper import ObjectWrapper

_consoles = threading.local()

def acquire_console(shell):
    _consoles.active = shell

def release_console():
    del _consoles.active

def setquit():
    """Define new built-ins 'quit' and 'exit'.
    These are simply strings that display a hint on how to exit.

    """
    if os.sep == ':':
        eof = 'Cmd-Q'
    elif os.sep == '\\':
        eof = 'Ctrl-Z plus Return'
    else:
        eof = 'Ctrl-D (i.e. EOF)'

    class Quitter(object):
        def __init__(self, name):
            self.name = name

        def __repr__(self):
            return 'Use %s() or %s to exit' % (self.name, eof)

        def __call__(self, code=None):
            # If executed with our interactive console, only raise the
            # SystemExit exception but don't close sys.stdout as we are
            # not the owner of it.

            if hasattr(_consoles, 'active'):
                raise SystemExit(code)

            # Shells like IDLE catch the SystemExit, but listen when their
            # stdin wrapper is closed.

            try:
                sys.stdin.close()
            except:
                pass
            raise SystemExit(code)

    __builtin__.quit = Quitter('quit')
    __builtin__.exit = Quitter('exit')

setquit()

class OutputWrapper(ObjectWrapper):

    def write(self, data):
        try:
            shell = _consoles.active
            return shell.stdout.write(data)
        except:
            return self._ispyd_next_object.write(data)

    def writelines(self, data):
        try:
            shell = _consoles.active
            return shell.stdout.writelines(data)
        except:
            return self._ispyd_next_object.writelines(data)

sys.stdout = OutputWrapper(sys.stdout)
sys.stderr = OutputWrapper(sys.stderr)
