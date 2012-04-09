import code
import fnmatch
import os
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
        """platform
	Display the platform the process is running on. This is the value
        available from 'sys.platform'."""

        print >> self.stdout, sys.platform

    def do_version(self, line):
        """version
	Display the version of Python being used. This is the value
	available from 'sys.version'."""

        print >> self.stdout, sys.version

    def do_prefix(self, line):
        """prefix
	Display the location of the Python installation being used. This is
	the value available from 'sys.prefix'."""

        print >> self.stdout, sys.prefix

    def do_path(self, line):
        """path
	Display the Python module search path. This is the value available
	from 'sys.path'."""

        print >> self.stdout, sys.path

    def do_executable(self, line):
        """executable
	Display the executable run when this process was started. This is
	the value available from 'sys.executable'.
        
	Note that in an embedded system this may not refer to the Python
	executable, but the name of the application Python was being
	embedded in."""

        print >> self.stdout, sys.executable

    def do_argv(self, line):
        """argv
        Display the command line arguments supplied when the executable
        that started this process was run. This is the value available
        from 'sys.argv'.

        Note that in an embedded sytem this may not reflect the actual
        command line arguments used."""

        print >> self.stdout, sys.argv

    def do_defaultencoding(self, line):
        """defaultencoding
        Display the default encoding used when converting Unicode strings.
        This is the value available from 'sys.defaultencoding'."""

        print >> self.stdout, sys.getdefaultencoding()

    def do_filesystemencoding(self, line):
        """filesystemencoding
        Display the file system encoding. This is the value available from
        'sys.filesystemencoding'."""

        print >> self.stdout, sys.getfilesystemencoding()

    def do_maxint(self, line):
        """maxint
	Display the largest positive integer supported by Pythons regular
	integer type. This is the value available from 'sys.maxint'."""

        print >> self.stdout, sys.maxint

    def do_maxsize(self, line):
        """maxsize
	Display the largest positive integer supported by the platforms
	Py_ssize_t type, and thus the maximum size lists, strings, dicts,
	and many other containers can have. This is the value available
	from 'sys.maxsize'."""

        print >> self.stdout, sys.maxsize

    def do_maxunicode(self, line):
        """maxunicode
	Display an integer giving the largest supported code point for a
	Unicode character. The value of this depends on the configuration
	option that specifies whether Unicode characters are stored as
	UCS-2 or UCS-4. This is the value available from 'sys.maxunicode'."""

        print >> self.stdout, sys.maxunicode

    def do_environ(self, line):
        """environ
	Display the set of environment variables for the process. This is
        the set of environment variables available from 'os.environ'.

	Note that this is only those environment variables which were
	already set at the point the Python (sub)interpreter was started or
	which were later set from within the (sub)interpreter. It will not
	include any which are later set from C code, or set from within
	another Python (sub)interpreter within the same process."""

        print >> self.stdout, os.environ

    def do_modules(self, pattern):
        """modules
        Display the currently loaded Python modules. By default this will
        only display the root module for any packages. If you wish to see
        all modules, including sub modules of packages, use 'modules *'.
	The value '*' can be replaced with any glob pattern to be more
	selective. For example 'modules ispyd.*' will list just the sub
	modules for this package."""

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
        """threads
	Display stack trace dumps for all threads currently executing
	within the Python interpreter.
        
        Note that if coroutines are being used, such as systems based
        on greenlets, then only the thread stack of the currently
        executing coroutine will be displayed."""

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
        """console
        When enabled in the configuration file, will startup up an embedded
        interactive Python interpreter. Invoke 'exit()' or 'quit()' to
        escape the interpreter session."""

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
