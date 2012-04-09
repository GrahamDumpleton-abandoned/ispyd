import os
import flask
import time

from ispyd.manager import ShellManager
from ispyd.plugins.wsgi import WSGIApplicationWrapper

config_file = os.path.join(os.path.dirname(__file__), 'ispyd.ini')
shell_manager = ShellManager(config_file)

application = flask.Flask(__name__)
application.wsgi_app = WSGIApplicationWrapper(application.wsgi_app)

def function():
    raise RuntimeError('xxx')

@application.route("/")
def hello():
    time.sleep(0.05)
    function()
    return flask.render_template_string("Hello World!")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    application.run(host='0.0.0.0', port=port)
