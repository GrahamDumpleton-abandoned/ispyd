import code
import fnmatch
import sys
import thread
import threading
import traceback

from ispyd.console import acquire_console, release_console

class EmbeddedConsole(code.InteractiveConsole):

    def write(self, data):
        self.stdout.write(data)
        self.stdout.flush()

    def raw_input(self, prompt):
        self.stdout.write(prompt)
        self.stdout.flush()
        line = self.stdin.readline()
        line = line.rstrip('\r\n')
        return line

class PythonShell(object):

    name = 'python'

    def activate(self, config_object):
        self.__config_object = config_object

    def do_platform(self, line):
        print >> self.stdout, sys.platform

    def do_version(self, line):
        print >> self.stdout, sys.version

    def do_prefix(self, line):
        print >> self.stdout, sys.prefix

    def do_path(self, line):
        print >> self.stdout, sys.path

    def do_executable(self, line):
        print >> self.stdout, sys.executable

    def do_argv(self, line):
        print >> self.stdout, sys.argv

    def do_defaultencoding(self, line):
        print >> self.stdout, sys.getdefaultencoding()

    def do_filesystemencoding(self, line):
        print >> self.stdout, sys.getfilesystemencoding()

    def do_maxint(self, line):
        print >> self.stdout, sys.maxint

    def do_maxsize(self, line):
        print >> self.stdout, sys.maxsize

    def do_maxunicode(self, line):
        print >> self.stdout, sys.maxunicode

    def do_modules(self, pattern):
        if pattern:
            result = []
            for name in sys.modules.keys():
                if fnmatch.fnmatch(name, pattern):
                    result.append(name)
            print >> self.stdout, sorted(result)
        else:
            result = []
            for name in sys.modules.keys():
                if not '.' in name:
                    result.append(name)
            print >> self.stdout, sorted(result)

    def do_threads(self, line): 
        all = [] 
        for threadId, stack in sys._current_frames().items():
            block = []
            block.append('# ThreadID: %s' % threadId) 
            thr = threading._active.get(threadId)
            if thr:
                block.append('# Name: %s' % thr.name) 
            for filename, lineno, name, line in traceback.extract_stack(
                stack): 
                block.append('File: \'%s\', line %d, in %s' % (filename,
                        lineno, name)) 
                if line:
                    block.append('  %s' % (line.strip()))
            all.append('\n'.join(block))

        print >> self.stdout, '\n\n'.join(all)

    def do_console(self, line):
        enabled = False

        if self.__config_object.has_option('python:console', 'enabled'):
            value = self.__config_object.get('python:console', 'enabled')
            enabled = value.lower() in ('1', 'on', 'yes', 'true')

        if not enabled:
            print >> self.stdout, 'Sorry, the Python console is disabled.'
            return

        locals = {}

        locals['stdin'] = self.stdin
        locals['stdout'] = self.stdout

        console = EmbeddedConsole(locals)

        console.stdin = self.stdin
        console.stdout = self.stdout

        acquire_console(self)

        try:
            console.interact()
        except SystemExit:
            pass
        finally:
            release_console()
