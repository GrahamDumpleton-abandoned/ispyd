import atexit
import cmd
import ConfigParser
import os
import socket
import threading
import traceback
import sys

from ispyd.shell import RootShell

class ShellManager(object):

    def __init__(self, config_file):
        self.__config_file = config_file
        self.__config_object = ConfigParser.RawConfigParser()

        if not self.__config_object.read([config_file]):
            raise RuntimeError('Unable to open configuration file %s.' %
                               config_file)

        self.__socket_server = self.__config_object.get('ispyd',
            'listen') % {'pid': os.getpid()}

        if not os.path.isabs(self.__socket_server):
            host, port = self.__socket_server.split(':')
            port = int(port)
            self.__socket_server = (host, port)

        self.__thread = threading.Thread(target=self.__thread_run,
            name='ISpyd-Shell-Manager')

        self.__thread.setDaemon(True)
        self.__thread.start()

    def __socket_cleanup(self, path):
        try:
            os.unlink(path)
        except:
            pass

    def __thread_run(self):
        if type(self.__socket_server) == type(()):
            listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            listener.bind(self.__socket_server)
        else:
            try:
                os.unlink(self.__socket_server)
            except:
                pass

            listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            listener.bind(self.__socket_server)

            atexit.register(self.__socket_cleanup, self.__socket_server)
            os.chmod(self.__socket_server, 0600)

        listener.listen(5)

        while True:
            client, addr = listener.accept()

            shell = RootShell(self.__config_object)

            shell.stdin = client.makefile('r')
            shell.stdout = client.makefile('w')

            try:
                shell.cmdloop()
            except:
                print >> shell.stdout, 'Exception in shell "%s".' % shell.name
                traceback.print_exception(*sys.exc_info(), file=shell.stdout)

            shell.stdin = None
            shell.stdout = None

            del shell

            client.close()
