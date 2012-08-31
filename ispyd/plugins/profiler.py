import atexit
import Queue
import StringIO
import sys
import threading
import time
import traceback

_profiler = None

class Profiler(threading.Thread):

    def __init__(self, duration, interval, filename):
        super(Profiler, self).__init__()
        self._duration = duration
        self._interval = interval
        self._filename = filename
        self._queue = Queue.Queue()
        self._nodes = {}
        self._links = {}

    def run(self):
        start = time.time()

        while time.time() < start+self._duration:
            try:
                self._queue.get(timeout=self._interval)
                break
            except:
                pass

            stacks = sys._current_frames().values()

            for stack in stacks:
                self.process_stack(stack)

        print >> open(self._filename, 'w'), repr((self._nodes, self._links))

        #print >> open(self._filename, 'w'), repr(self._records)

        global _profiler

        _profiler = None

    def abort(self):
        self._queue.put(True)
        self.join()

    def process_stack(self, stack):
        output = StringIO.StringIO()

        parent = None

        for filename, lineno, name, line in traceback.extract_stack(stack): 
            node = (filename, name)

            node_record = self._nodes.get(node)

            if node_record is None:
                node_record = { 'count': 1 }
                self._nodes[node] = node_record
            else:
                node_record['count'] += 1

            if parent:
                link = (parent, node)

                link_record = self._links.get(link)

                if link_record is None:
                    link_record = { 'count': 1 }
                    self._links[link] = link_record
                else:
                    link_record['count'] += 1

            parent = node
                    

        """
        children = None

        for filename, lineno, name, line in traceback.extract_stack(stack): 
            #key = (filename, lineno, name)
            key = (filename, name)

            if children is None:
                record = self._records.get(key)

                if record is None:
                    record = { 'count': 1, 'children': {} }
                    self._records[key] = record
                else:
                    record['count'] += 1

                children = record['children']

            elif key in children:
                record = children[key]
                record['count'] += 1
                children = record['children']

            else:
                record = { 'count': 1, 'children': {} }
                children[key] = record
                children = record['children']
        """

def _abort():
    if _profiler:
        _profiler.abort()

atexit.register(_abort)

class ProfilerShell(object):

    name = 'profiler'

    def activate(self, config_object):
        self.__config_object = config_object

        enabled = False

        if self.__config_object.has_option('profiler', 'enabled'):
            value = self.__config_object.get('profiler', 'enabled')
            enabled = value.lower() in ('1', 'on', 'yes', 'true')

        if not enabled:
            print >> self.stdout, 'Sorry, the profiler plugin is disabled.'
            return True

    def do_start(self, line):
        global _profiler

        if _profiler is None:
            _profiler = Profiler(10.0*60.0, 0.105, '/tmp/profile.dat')
            #_profiler = Profiler(20.0, 1.0, '/tmp/profile.dat')
            _profiler.start()

    def do_abort(self, line):
        global _profiler

        if _profiler is None:
            _profiler.abort()
