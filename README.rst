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
uWSGI which do not support registration of cleanup callbacks using the
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
through a FQDN or '0.0.0.0' as that would imply it can be accessed from
outside of the system.

Connections
-----------

The system only currently allows one connection to the process at a time.
Because connections may be received across either UNIX or INET socket types
and telnet only works for INET sockets, an 'ispy' client program is provided
for connecting to processes. To run the client run execute::

    ispy ispyd.ini

The 'ispyd.ini' argument should be the path to the same configuration file
as used by the application the package was integrated with.

When 'ispy' is run it will enter you first into a local shell. To get the
set of available commands run 'help'::

    $ ispy ispyd.ini 
    (ispyd) help

    Documented commands (type help <topic>):
    ========================================
    connect  exit  help  servers

You can then get a list of the processes that can be connected to by using
the 'servers' command. This will look at the 'listen' entry to determine
the address and will present multiple choices where this is possible with
the configuration. For example, when using UNIX sockets and the application
is running with multiple processes one would see::

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

To see the list of loaded plugins use the 'plugins' command::

    (ispyd:14940) plugins
    ['debugger', 'process', 'python', 'wsgi']

To enter a sub shell for a listed plugin use the 'shell' command or '!'
shortcut::

    (ispyd:14940) shell python
    (process:14940) help

    Documented commands (type help <topic>):
    ========================================
    cwd  egid  euid  exit  gid  help  pid  prompt  uid

    (process:14940) cwd
    /Users/graham/

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
    argv             environ     filesystemencoding  maxsize     path      prompt 
    console          executable  help                maxunicode  platform  threads
    defaultencoding  exit        maxint              modules     prefix    version

    (python:14940) console
    Python 2.6.1 (r261:67515, Jun 24 2010, 21:47:49) 
    [GCC 4.2.1 (Apple Inc. build 5646)] on darwin
    Type "help", "copyright", "credits" or "license" for more information.
    (EmbeddedConsole)
    >>> import os
    >>> os.getcwd()
    '/Users/graham'
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
    debug    exit  insert  print   remove  tracebacks
    discard  help  list    prompt  reset 

    (debugger:15009) insert __main__:function

    (debugger:15009) tracebacks
    {'__main__:function': <traceback object at 0x1013a11b8>}
    (debugger:15009) debug __main__:function
    > /Users/graham/wsgi.py(15)function()
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
environ dictionary and the stack trace for where the code is executing::

    (wsgi:18630) help

    Documented commands (type help <topic>):
    ========================================
    exit  help  prompt  requests

    (wsgi:18630) requests
    No active transactions.

    (wsgi:18630) requests

    ==== 67 ====

    thread_id = 140735076232384
    start_time = Mon Apr  9 21:49:54 2012
    duration = 0.013629 seconds

    CONTENT_LENGTH = ''
    CONTENT_TYPE = ''
    HTTP_ACCEPT = '*/*'
    HTTP_HOST = 'localhost:5000'
    HTTP_USER_AGENT = 'ApacheBench/2.3'
    PATH_INFO = '/'
    QUERY_STRING = ''
    REMOTE_ADDR = '127.0.0.1'
    REMOTE_PORT = 50012
    REQUEST_METHOD = 'GET'
    SCRIPT_NAME = ''
    SERVER_NAME = '0.0.0.0'
    SERVER_PORT = '5000'
    SERVER_PROTOCOL = 'HTTP/1.0'
    SERVER_SOFTWARE = 'Werkzeug/0.8.3'
    werkzeug.request = <Request 'http://localhost:5000/' [GET]>
    werkzeug.server.shutdown = <function shutdown_server at 0x10476cc80>
    wsgi.errors = <ispyd.console.OutputWrapper object at 0x1013c68d0>
    wsgi.input = <socket._fileobject object at 0x10476caa0>
    wsgi.multiprocess = False
    wsgi.multithread = False
    wsgi.run_once = False
    wsgi.url_scheme = 'http'
    wsgi.version = (1, 0)

    File: "wsgi.py", line 25, in <module>
      application.run(host='0.0.0.0', port=port)
    File: "/Users/graham/lib/python2.6/site-packages/flask/app.py", line 703, in run
      run_simple(host, port, self, **options)
    File: "/Users/graham/lib/python2.6/site-packages/werkzeug/serving.py", line 617, in run_simple
      inner()
    File: "/Users/graham/lib/python2.6/site-packages/werkzeug/serving.py", line 599, in inner
      passthrough_errors, ssl_context).serve_forever()
    File: "/Users/graham/lib/python2.6/site-packages/werkzeug/serving.py", line 358, in serve_forever
      HTTPServer.serve_forever(self)
    File: "/System/Library/Frameworks/Python.framework/Versions/2.6/lib/python2.6/SocketServer.py", line 226, in serve_forever
      self._handle_request_noblock()
    File: "/System/Library/Frameworks/Python.framework/Versions/2.6/lib/python2.6/SocketServer.py", line 281, in _handle_request_noblock
      self.process_request(request, client_address)
    File: "/System/Library/Frameworks/Python.framework/Versions/2.6/lib/python2.6/SocketServer.py", line 307, in process_request
      self.finish_request(request, client_address)
    File: "/System/Library/Frameworks/Python.framework/Versions/2.6/lib/python2.6/SocketServer.py", line 320, in finish_request
      self.RequestHandlerClass(request, client_address, self)
    File: "/System/Library/Frameworks/Python.framework/Versions/2.6/lib/python2.6/SocketServer.py", line 615, in __init__
      self.handle()
    File: "/Users/graham/lib/python2.6/site-packages/werkzeug/serving.py", line 182, in handle
      rv = BaseHTTPRequestHandler.handle(self)
    File: "/System/Library/Frameworks/Python.framework/Versions/2.6/lib/python2.6/BaseHTTPServer.py", line 329, in handle
      self.handle_one_request()
    File: "/Users/graham/lib/python2.6/site-packages/werkzeug/serving.py", line 217, in handle_one_request
      return self.run_wsgi()
    File: "/Users/graham/lib/python2.6/site-packages/werkzeug/serving.py", line 159, in run_wsgi
      execute(app)
    File: "/Users/graham/lib/python2.6/site-packages/werkzeug/serving.py", line 146, in execute
      application_iter = app(environ, start_response)
    File: "/Users/graham/lib/python2.6/site-packages/flask/app.py", line 1518, in __call__
      return self.wsgi_app(environ, start_response)
    File: "build/bdist.macosx-10.6-universal/egg/ispyd/plugins/wsgi.py", line 86, in __call__
      iterable = self._ispyd_next_object(environ, start_response)
    File: "/Users/graham/lib/python2.6/site-packages/flask/app.py", line 1504, in wsgi_app
      response = self.full_dispatch_request()
    File: "/Users/graham/lib/python2.6/site-packages/flask/app.py", line 1262, in full_dispatch_request
      rv = self.dispatch_request()
    File: "/Users/graham/lib/python2.6/site-packages/flask/app.py", line 1248, in dispatch_request
      return self.view_functions[rule.endpoint](**req.view_args)
    File: "wsgi.py", line 19, in hello
      time.sleep(0.05)
