import cmd
import os
import sys
import traceback

_builtin_plugins = [
  'ispyd.plugins.debugger:DebuggerShell',
  'ispyd.plugins.process:ProcessShell',
  'ispyd.plugins.profiler:ProfilerShell',
  'ispyd.plugins.python:PythonShell',
  'ispyd.plugins.wsgi:WSGIShell',
]

class ProxyShell(cmd.Cmd):

    use_rawinput = 0

    def __init__(self, plugin, stdin, stdout):
        cmd.Cmd.__init__(self, stdin=stdin, stdout=stdout)

        self.__plugin = plugin

        plugin.stdin = stdin
        plugin.stdout = stdout

    def activate(self, config_object):
        if hasattr(self.__plugin, 'activate'):
            return self.__plugin.activate(config_object)

    def shutdown(self):
        if hasattr(self.__plugin, 'shutdown'):
            return self.__plugin.shutdown()

    def get_names(self):
        names1 = []
        classes = [self.__plugin.__class__]
        while classes:
            aclass = classes.pop(0)
            if aclass.__bases__:
                classes = classes + list(aclass.__bases__)
            names1 = names1 + dir(aclass)

        names2 = cmd.Cmd.get_names(self)

        names = set(names1 + names2)

        return list(names)

    def emptyline(self):
        pass

    def __getattr__(self, name):
        return getattr(self.__plugin, name)

    def do_prompt(self, flag):
        """prompt (on|off)
	Enable or disable the shell prompt."""

        if flag == 'on':
            self.prompt = '(%s:%d) ' % (self.__plugin.name, os.getpid())
        elif flag == 'off':
            self.prompt = ''

    def do_exit(self, line):
        """exit
        Exit the sub shell. Control will be returned to the root shell."""

        if hasattr(self.__plugin, 'do_exit'):
            self.__plugin.do_exit(line)
        return True

    def help_help(self):
        print >> self.stdout, """help (command)
        Output list of commands or help details for named command."""

class RootShell(cmd.Cmd):

    name = 'ispyd'

    use_rawinput = 0

    def __init__(self, config_object):
        cmd.Cmd.__init__(self)

        self.__config_object = config_object

        self.__plugins = {}

        if self.__config_object.has_option('ispyd', 'plugins'):
            names = self.__config_object.get('ispyd', 'plugins')
            names = names % {'builtins': ' '.join(_builtin_plugins)}
            names = names.split()
        else:
            names = _builtin_plugins

        for name in names:
            module, object = name.split(':')
            __import__(module)
            plugin = getattr(sys.modules[module], object)
            self.__plugins[plugin.name] = plugin

        self.do_prompt('on')

    def emptyline(self):
        pass

    def do_prompt(self, flag):
        """prompt (on|off)
	Enable or disable the shell prompt. When invoking a sub shell, the
	current setting will be inherited by the sub shell."""

        if flag == 'on':
            self.prompt = '(%s:%d) ' % (self.name, os.getpid())
        elif flag == 'off':
            self.prompt = ''

    def do_plugins(self, line):
        """plugins
        Outputs the names of the loaded plugins."""

        plugins = sorted(self.__plugins.keys())
        print >> self.stdout, plugins

    def do_shell(self, name):
        """enter name
        Invoke and enter into shell for the named plugin."""

        if name in self.__plugins:
            type = self.__plugins[name]

            plugin = type()

            shell = ProxyShell(plugin, self.stdin, self.stdout)

            shell.do_prompt(self.prompt and 'on' or 'off')

            if shell.activate(self.__config_object):
                return

            try:
                shell.cmdloop()
            except:
                print >> self.stdout, 'Exception in shell "%s".' % plugin.name
                traceback.print_exception(*sys.exc_info(), file=self.stdout)

            shell.shutdown()

    def do_exit(self, line):
        """exit
        Exit the root shell."""

        return True

    def help_help(self):
        print >> self.stdout, """help (command)
        Output list of commands or help details for named command."""
