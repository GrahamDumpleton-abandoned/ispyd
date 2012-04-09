import fnmatch
import os
import sys

class ProcessShell(object):

    name = 'process'

    def do_pid(self, line):
        """pid
	Display the process ID of the current process."""

        print >> self.stdout, os.getpid()

    def do_uid(self, line):
        """uid
	Display the uid under which the process is executing."""

        print >> self.stdout, os.getuid()

    def do_euid(self, line):
        """uid
	Display the current effective uid under which the process is
	executing."""

        print >> self.stdout, os.geteuid()

    def do_gid(self, line):
        """gid
	Display the gid under which the process is executing."""

        print >> self.stdout, os.getgid()

    def do_egid(self, line):
        """egid
	Display the current effective gid under which the process is
	executing."""

        print >> self.stdout, os.getegid()

    def do_cwd(self, line):
        """cwd
	Display the current working directory the process is running in."""

        print >> self.stdout, os.getcwd()
