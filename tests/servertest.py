if __name__ != '__main__':
    raise ImportError('This is not a module, but a script.')

import sys, os, socket

test_root = os.path.dirname(os.path.abspath(__file__))
os.chdir(test_root)
sys.path.insert(0, os.path.dirname(test_root))
sys.path.insert(0, test_root)

try:
    server = sys.argv[1]
    port   = int(sys.argv[2])

    if server == 'gevent':
        from gevent import monkey
        monkey.patch_all()

    from cocopot import Cocopot

    app = Cocopot()
    @app.route('/test')
    def test():
        return 'ok'
    app.run(host=server, port=port)
except socket.error:
    sys.exit(3)
except ImportError:
    sys.exit(128)
except KeyboardInterrupt:
    pass
