import pytest

from flagon import Flagon, Blueprint, request, g, abort
from flagon.testing import FlagonClient
import copy
import traceback

def test_client():
    app = Flagon()
    @app.before_request
    def before_request1():
        g.a = 1

    @app.before_request
    def before_request2():
        g.b = 2

    @app.route('/hello')
    def hello():
        return 'ok'

    c = FlagonClient(app)
    r = c.open('/hello')
    assert r[0] == b'ok'
    assert r[1] == '200 OK'

    r = c.open('/hello2')
    assert r[1] == '404 Not Found'

def test_client2():
    app = Flagon()
    @app.before_request
    def before_request1():
        return 'before_request_return'

    @app.route('/hello')
    def hello():
        return 'ok'

    c = FlagonClient(app)
    r = c.open('/hello')
    assert r[0] == b'before_request_return'
    assert r[1] == '200 OK'


def test_client_error():
    app = Flagon()

    @app.route('/hello')
    def hello():
        return object()

    c = FlagonClient(app)
    r = c.open('/hello')
    assert r[1] == '500 Internal Server Error'
