import fnmatch
import os
import sys

class ProcessShell(object):

    name = 'process'

    def do_pid(self, line):
        print >> self.stdout, os.getpid()

    def do_uid(self, line):
        print >> self.stdout, os.getuid()

    def do_euid(self, line):
        print >> self.stdout, os.geteuid()

    def do_gid(self, line):
        print >> self.stdout, os.getgid()

    def do_egid(self, line):
        print >> self.stdout, os.getegid()

    def do_environ(self, line):
        print >> self.stdout, os.environ

    def do_cwd(self, line):
        print >> self.stdout, os.getcwd()
