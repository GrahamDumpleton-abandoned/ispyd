import inspect
import pdb
import sys
import traceback

from ispyd.wrapper import ObjectWrapper
from ispyd.console import acquire_console, release_console

_probes = {}
_tracebacks = {}

class DebuggerWrapper(ObjectWrapper):

    def __init__(self, wrapped, name):
        super(DebuggerWrapper, self).__init__(wrapped)
        self._ispyd_name = name

    def _ispyd_new_object(self, wrapped):
        return self.__class__(wrapped, self._ispyd_name)

    def __call__(self, *args, **kwargs):
        try:
            return self._ispyd_next_object(*args, **kwargs)
        except:
            _tracebacks[self._ispyd_name] = sys.exc_info()[2]
            raise

def resolve_path(module, name):
    if not inspect.ismodule(module):
        __import__(module)
        module = sys.modules[module]

    parent = module

    path = name.split('.')
    attribute = path[0]

    original = getattr(parent, attribute)
    for attribute in path[1:]:
        parent = original
        original = getattr(original, attribute)

    return (parent, attribute, original)

def remove_probe(module, name):
    (parent, attribute, original) = resolve_path(module, name)
    wrapper = getattr(parent, attribute)
    original = wrapper._ispyd_next_object
    setattr(parent, attribute, original)

def insert_probe(module, name, factory, args=()):
    (parent, attribute, original) = resolve_path(module, name)
    wrapper = factory(original, *args)
    setattr(parent, attribute, wrapper)
    return wrapper

class DebuggerShell(object):

    name = 'debugger'

    def activate(self, config_object):
        self.__config_object = config_object

        enabled = False

        if self.__config_object.has_option('debugger', 'enabled'):
            value = self.__config_object.get('debugger', 'enabled')
            enabled = value.lower() in ('1', 'on', 'yes', 'true')

        if not enabled:
            print >> self.stdout, 'Sorry, the debugger plugin is disabled.'
            return True

    def do_insert(self, line):
        if not line:
            print >> self.stdout, 'Invalid probe location.'
            return

        if line in _probes:
            print >> self.stdout, 'Probe already exists.'
            return

        try:
            module, name = line.split(':')
        except:
            print >> self.stdout, 'Invalid probe location.'
            return

        try:
            _probes[line] = insert_probe(module, name,
                                         DebuggerWrapper, (line,))
        except:
            print >> self.stdout, 'Failed to insert probe.'
            return

    def do_remove(self, line):
        if not line:
            print >> self.stdout, 'Invalid probe location.'
            return

        if not line in _probes:
            print >> self.stdout, 'Probe does not exist.'
            return

        try:
            module, name = line.split(':')
        except:
            print >> self.stdout, 'Invalid probe location.'
            return

        try:
            remove_probe(module, name)
        except:
            print >> self.stdout, 'Failed to remove probe.'
            return
        else:
            del _probes[line]

    def do_list(self, line):
        print >> self.stdout, sorted(_probes.keys())

    def do_reset(self, line):
        global _tracebacks
        _tracebacks = []
        for name in _probes.keys():
            self.do_remove(name)

    def do_tracebacks(self, line):
        print >> self.stdout, _tracebacks

    def do_print(self, line):
        if not line in _tracebacks:
            return
        traceback.print_tb(_tracebacks[line], file=self.stdout)

    def do_discard(self, line):
        if line in _tracebacks:
            del _tracebacks[line]

    def do_debug(self, line):
        if not line in _tracebacks:
            return

        tb = _tracebacks[line]

        debugger = pdb.Pdb(stdin=self.stdin, stdout=self.stdout)
        debugger.reset()

        acquire_console(self)

        try:
            debugger.interaction(None, tb)
        except SystemExit:
            pass
        finally:
            release_console()
