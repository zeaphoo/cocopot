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
    assert c.open('/hello') == 'ok'
