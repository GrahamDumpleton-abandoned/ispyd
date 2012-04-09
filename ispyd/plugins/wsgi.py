import StringIO
import sys
import thread
import threading
import time
import traceback

from ispyd.wrapper import ObjectWrapper

_exceptions = []

class WSGITransaction(object):

    request_lock = threading.Lock()
    request_count = 0

    transactions = {}

    def __init__(self, environ):
        self.environ = environ

        self.thread_id = thread.get_ident()

        self.deleted = False
        self.running = False

        self.start = 0.0
        self.finish = 0.0

        with self.request_lock:
            WSGITransaction.request_count += 1
            self.request_id = WSGITransaction.request_count

    def __del__(self):
        self.deleted = True
        if self.running:
            self.__exit__(None, None, None)

    def __enter__(self):
        self.transactions[self.request_id] = self
        self.running = True
        self.start = time.time()
        return self

    def __exit__(self, exc, value, tb):
        _exceptions.append(tb)
        print 'TRACEBACK', exc, value, tb
        self.running = False
        self.finish = time.time()
        if not self.deleted:
            try:
                del self.transactions[self.request_id]
            except:
                pass

class WSGIApplicationIterable(object):

    def __init__(self, transaction, iterable):
        self.transaction = transaction
        self.iterable = iterable

    def __iter__(self):
        for item in self.iterable:
            yield item

    def close(self):
        try:
            if hasattr(self.iterable, 'close'):
                self.iterable.close()
        except:
            self.transaction.__exit__(*sys.exc_info())
            raise
        else:
            self.transaction.__exit__(None, None, None)

class WSGIApplicationWrapper(ObjectWrapper):

    def _ispyd_new_object(self, wrapped):
        return self.__class__(wrapped)

    def __call__(self, environ, start_response):
        transaction = WSGITransaction(environ)
        transaction.__enter__()

        try:
            iterable = self._ispyd_next_object(environ, start_response)
            raise RuntimeError('xxx')
        except:
            transaction.__exit__(*sys.exc_info())
            raise

        return WSGIApplicationIterable(transaction, iterable)

def wsgi_application():
    def decorator(wrapped):
        return WSGIApplicationWrapper(wrapped)
    return decorator

class WSGIShell(object):

    name = 'wsgi'

    def format_traceback(self, stack):
        output = StringIO.StringIO()

        for filename, lineno, name, line in traceback.extract_stack(stack): 
            print >> output, 'File: "%s", line %d, in %s' % (
                    filename, lineno, name)
            if line: 
                print >> output, '  %s' % line.strip()

        return output.getvalue()

    def format_transaction(self, transaction, frames):
        output = StringIO.StringIO()

        start_time = time.ctime(transaction.start)
        duration = time.time() - transaction.start

        print >> output

        print >> output, '==== %d ====' % transaction.request_id

        print >> output

        print >> output, 'thread_id = %d' % transaction.thread_id
        print >> output, 'start_time = %s' % start_time
        print >> output, 'duration = %0.6f seconds' % duration

        print >> output

        for key in sorted(transaction.environ.keys()):
            value = repr(transaction.environ[key])
            print >> output, '%s = %s' % (key, value)

        print >> output

        if transaction.thread_id in frames:
            text = self.format_traceback(frames[transaction.thread_id])

        if not text or transaction.finish != 0.0:
            return ''

        print >> output, text

        return output.getvalue()

    def do_requests(self, line):
        output = StringIO.StringIO()

        frames = dict(sys._current_frames().items())
        transactions = dict(WSGITransaction.transactions)
        request_ids = sorted(transactions.keys())

        for i in range(len(request_ids)):
            request_id = request_ids[i]
            text = self.format_transaction(transactions[request_id], frames)
            if text:
                output.write(text)

        text = output.getvalue()
        if text:
            print >> self.stdout, text
        else:
            print >> self.stdout, 'No active transactions.'
