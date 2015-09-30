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
    assert r[0] == 'ok'
    assert r[1] == '200 OK'
