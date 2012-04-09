import cmd
import ConfigParser
import glob
import os
import socket
import sys
import threading

class ClientShell(cmd.Cmd):

    prompt = '(ispyd) '

    def __init__(self, config_file, stdin=None, stdout=None):
        cmd.Cmd.__init__(self, stdin=stdin, stdout=stdout)

        self.__config_file = config_file
        self.__config_object = ConfigParser.RawConfigParser()

        if not self.__config_object.read([config_file]):
            raise RuntimeError('Unable to open configuration file %s.' %
                               config_file)

        server = self.__config_object.get('ispyd', 'listen') % {'pid': '*'}

        if os.path.isabs(server):
            self.__servers = [(socket.AF_UNIX, path) for path in
                             sorted(glob.glob(server))]
        else:
            host, port = server.split(':')
            port = int(port)

            self.__servers = [(socket.AF_INET, (host, port))]

    def emptyline(self):
        pass

    def help_help(self):
        print >> self.stdout, """help (command)
        Output list of commands or help details for named command."""

    def do_exit(self, line):
        """exit
        Exit the client shell."""

        return True

    def do_servers(self, line):
        """servers
        Display a list of the servers which can be connected to."""

        for i in range(len(self.__servers)):
            print >> self.stdout, '%s: %s' % (i+1, self.__servers[i])

    def do_connect(self, line):
        """connect [index]
        Connect to the server from the servers lift with given index. If
        there is only one server then the index position does not need to
        be supplied."""

        if len(self.__servers) == 0:
            print >> self.stdout, 'No servers to connect to.'
            return

        if not line:
            if len(self.__servers) != 1:
                print >> self.stdout, 'Multiple servers, which should be used?'
                return
            else:
                line = '1'

        try:
            selection = int(line)
        except:
            selection = None

        if selection is None:
            print >> self.stdout, 'Server selection not an integer.'
            return

        if selection <= 0 or selection > len(self.__servers):
            print >> self.stdout, 'Invalid server selected.'
            return

        server = self.__servers[selection-1]

        client = socket.socket(server[0], socket.SOCK_STREAM)
        client.connect(server[1])

        def write():
            while 1:
                try:
                    c = sys.stdin.read(1)
                    if not c:
                        client.shutdown(socket.SHUT_RD)
                        break
                    client.sendall(c)
                except:
                    break

        def read():
            while 1:
                try:
                    c = client.recv(1)
                    if not c:
                        break
                    sys.stdout.write(c)
                    sys.stdout.flush()
                except:
                    break

        thread1 = threading.Thread(target=write)
        thread1.setDaemon(True)

        thread2 = threading.Thread(target=read)
        thread2.setDaemon(True)

        thread1.start()
        thread2.start()

        thread2.join()

        return True

def main():
    shell = ClientShell(sys.argv[1])
    shell.cmdloop()

if __name__ == '__main__':
    main()
