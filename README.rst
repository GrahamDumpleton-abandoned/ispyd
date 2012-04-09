Copyright 2012 GRAHAM DUMPLETON

Overview
========

The 'ispyd' package provides an in process shell for introspecting a
running process. It was primarily intended for investigating running WSGI
application processes, specifically to determine what a process is doing
when it hangs, but has many other features as well. This includes being
able to start an embedded interactive Python interpreter session, set
debugger probe points to record tracebacks for exceptions and then later
run 'pdb' in post mortem mode on those exceptions.

The system works by creating a background thread in your application
process which handles incoming requests. For each connection in turn
received an interactive shell will be exposed to the client which then
allows commands to be run to get back information about the running
process.

Note that this system should still be regarded as experimental at this
point and you likely would not want to run it on a production system. The
anticipated feature set for builtin plugins is also by no means complete at
this point.

Installation
------------

Requires CPython 2 (2.6 or later) for full functionality.

Some features may not work properly with PyPy or when coroutine systems
such as those based on greenlets are used. For example, gevent or eventlet.

To install directly from source code run::

    python setup.py install

To create a tarball which can then be install using 'pip' run::

    python setup.py sdist

The resulting tarball will be located in the 'dist' directory and of the
form::

    ispyd-X.Y.Z.tar.gz

This can then be installed by running::

    pip install dist/ispyd-X.Y.Z.tar.gz

The package is not yet available on PyPi and will so only once version 1.0
has been reached.

1.0 will only be reached once code is cleaned up a bit and made more
resiliant to stuffing up the configuration. Internal code documentation
still needs to be done and internal help messages added.

You can also expect some features or how they are implemented to be changed
before 1.0 is released.

Integration
-----------

To integrate into your Python application you need to add the lines::

    from ispyd.manager import ShellManager

    config_file = os.path.join(os.path.dirname(__file__), 'ispyd.ini')
    shell_manager = ShellManager(config_file)

This assumes that a configuration file 'ispyd.ini' has been created and
exists in the same directory as the Python application/script file. If this
is not the case, change how 'config_file' is calculated or set it to an
explicit file system path.

The 'ispyd.ini' configuration file at the minimum needs to contain::

    [ispyd]
    listen = /tmp/ispyd-%(pid)s.sock

When the value of 'listen' is an absolute file system path, it will be used
as the name of a UNIX socket. If '%(pid)s' is used in the specified path,
it will be substituted with the process ID of the process. This is to allow
for use in applications which create multiple processes such as Python web
applications running under a multiprocess WSGI server.

If the application only runs a single process, you can instead use a fixed
path such as::

    [ispyd]
    listen = /tmp/ispyd.sock

Although '/tmp' is being used here, it should preferably be a directory
in a different location, where the directory is owned by and only
writable/readable to the same user that your Python process will run as.
The UNIX socket created will have mask 0600 so that is only accessible to
the user that the process runs as.

An attempt will be made to remove the UNIX listener socket files when the
process is shutdown. If the process crashes however this will not occur. It
may also not occur with some versions of embedded WSGI servers such as
uWSGI which do not support regitration of cleanup callbacks using the
'atexit' module in Python. In either event, it may be necessary to manually
remove old stale UNIX listener socket files.

If running a single application process, instead of using a UNIX listener
socket an INET socket can instead be used. This would be done with the
configuration::

    [ispyd]
    listen = localhost:12345

That is, a 'host:port' setting instead of an absolute file system path.

Note that when using an INET socket you can't rely on filesystem permissions
prohibiting who can access the port. The most you can do is restrict which
interface the port can be accessed. By using 'localhost' you restrict it to
connections from the same host. You should be extremely careful opening it
through a FQDN or '0.0.0.0' as that would imply it can be access from outside
of the system.

Connections
-----------

The system only currently allows one connection to the process at a time.
Because connections may be received across either UNIX or INET socket types
and telnet only works for INET sockets, a 'ispy' client program is provided
for connecting to processes. To run the client run execute::

    ispy ispyd.ini

The 'ispyd.ini' argument should be the path to the same configuration file
as used by the application the package was integrated with.

When 'ispy' is run it will enter you first into a local shell. To get the
set of available commands run 'help'::

    $ ispy ispyd.ini 
    (ispyd) help

    Undocumented commands:
    ======================
    connect  exit  help  servers

You can then get a list of the processes that can be connected to by using
the 'servers' command. This will look at the 'listen' entry to determine
the address and will present multiple choices where this is possible with
the configuration. For example, when using UNIX sockets and the application
is running with multiple process one would see::

    (ispyd) servers
    1: (1, '/tmp/ispyd-14905.sock')
    2: (1, '/tmp/ispyd-14906.sock')
    3: (1, '/tmp/ispyd-14907.sock')

If using INET sockets, you would instead see something like::

    (ispyd) servers
    1: (2, ('localhost', 12345))

You can now select which process you would like to connect to using the
'connect' command. This should be provided as argument an integer corresponding
to the entry in the list returned by the 'servers' command. If there is
only one entry, the argument to 'connect' can be left off::

    (ispyd) connect 1
    (ispyd:14940) help

    Documented commands (type help <topic>):
    ========================================
    exit  help  plugins  prompt  shell

When 'connect' is issued and a successful connection made you will be
connected to the monitored process. You can distinguish this by virtue of
the process ID of the process being included as part of the prompt. The
'help' command can then be used to see what further commands exist at
this level. To disconnect from the process when at this level use the
'exit' command.

Plugins
-------

The system is intended to be extendable. This is done through plugins which
can provide different features. A number of in built plugins are provided,
but third party plugins can be created and referenced from the configuration
file.

To see the list of loaded plugins used the 'plugins' command::

    (ispyd:14940) plugins
    ['debugger', 'process', 'python', 'wsgi']

To enter a sub shell for a listed plugin use the 'shell' command or '!'
shortcut::

    (ispyd:14940) shell process
    (process:14940) help

    Documented commands (type help <topic>):
    ========================================
    exit  help  prompt

    Undocumented commands:
    ======================
    cwd  egid  environ  euid  gid  pid  uid

    (process:14940) environ
    {'PATH': '/usr/bin:/bin:/usr/sbin:/sbin', 'HOME': '/Users/graham'}

Issuing 'exit' at this level will return you back to the top level shell
for the process. If you wanted to disconnect from the process completely
you would then need to run 'exit' a second time.

Most commands you can run with plugins will be self explanatory, but a
few special cases are explained in following sections.

Threads
+++++++

The 'threads' command can be found in the 'python' plugin. This will dump out
the current stack traces of all executing threads.

Note that if using a WSGI server such as Apache/mod_wsgi where the threads
are originally created outside of the Python interpreter, you will only get
a thread stack trace when the thread is handling a web request.

Console
+++++++

The 'console' command can be found in the 'python' plugin. Provided the
feature is enabled in the configuration file, it will launch you into an
embedded interactive Python interpreter directly within the process::

    (ispyd:14940) shell python
    (python:14940) help

    Documented commands (type help <topic>):
    ========================================
    exit  help  prompt

    Undocumented commands:
    ======================
    argv             executable          maxsize     path      threads
    console          filesystemencoding  maxunicode  platform  version
    defaultencoding  maxint              modules     prefix  

    (python:14940) console
    Python 2.6.1 (r261:67515, Jun 24 2010, 21:47:49) 
    [GCC 4.2.1 (Apple Inc. build 5646)] on darwin
    Type "help", "copyright", "credits" or "license" for more information.
    (EmbeddedConsole)
    >>> exit()

To exit the embedded interpreter call the 'exit()' or 'quit()' functions.

By default the ability to run the embedded interpreter is turned off. To
enable it you need to explicitly add to the configuration file::

    [python:console]
    enabled = true

As this is going to allow someone to do whatever they want with the internals
of the process it should only be enabled in a controlled environment where
you know that access is properly restricted.

Debugger
++++++++

The 'debugger' plugin allows you to dynamically insert probe points on
specific functions in your running Python process. After that point when
the function is called, if an exception occurs within the context of that
function, the traceback will be stored for later post mortem analysis
using 'pdb':: 

    (ispyd:15009) shell debugger
    (debugger:15009) help

    Documented commands (type help <topic>):
    ========================================
    exit  help  prompt

    Undocumented commands:
    ======================
    debug  discard  insert  list  print  remove  reset  tracebacks

    (debugger:15009) insert __main__:function
    (debugger:15009) tracebacks
    {'__main__:function': <traceback object at 0x1013a11b8>}
    (debugger:15009) debug __main__:function
    > /Users/graham/Projects/wsgi-shell/sample/wsgi.py(15)function()
    -> raise RuntimeError('xxx')
    (Pdb) dir()
    []
    (Pdb) __file__
    'wsgi.py'

By default, use of the 'debugger' plugin is disabled. To enable it you need
to add to the configuration file::

    [debugger]
    enabled = true

Requests
++++++++

With the addition of a WSGI application middleware wrapper around the entry
point for your WSGI application special monitoring for web requests in a
WSGI application can be enabled. If using Django 1.4 for example, you would
add the WSGI application middleware wrapper using::

    from ispyd.plugins.wsgi import WSGIApplicationWrapper

    from django.core.wsgi import get_wsgi_application
    application = get_wsgi_application()

    application = WSGIApplicationWrapper(application)

With this in place, the 'requests' command in the 'wsgi' plugin will dump
out details of any active requests at that time. This will include the WSGI
environ dictionary and the stack trace for where the code is executing.
