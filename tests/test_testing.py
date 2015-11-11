# -*- coding: utf-8 -*-
import pytest

from flagon import Flagon, Blueprint, request, g, abort
from flagon.testing import FlagonClient
from flagon.datastructures import FileUpload
from flagon._compat import BytesIO, to_bytes
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

def test_client_formdata():
    app = Flagon()
    @app.route('/hello')
    def hello():
        return 'ok'

    c = FlagonClient(app)
    r = c.open('/hello', content_type='application/x-www-form-urlencoded', form={'c':1, 'd':'woo'})
    assert r[0] == b'ok'
    assert r[1] == '200 OK'

    files = {
        'a.txt':FileUpload(BytesIO(to_bytes('text default')), 'file1', 'a.txt', headers={'Content-Type': 'text/plain'}),
        'a.html':FileUpload(BytesIO(to_bytes('<!DOCTYPE html><title>Content of a.html.</title>')), 'file2', 'a.html', headers={'Content-Type': 'text/plain'}),
        'b.txt': 'b txt content'
    }
    c = FlagonClient(app)
    r = c.open('/hello', content_type='multipart/form-data',
                form={'text':'text default'},
                files=files)
    assert r[0] == b'ok'
    assert r[1] == '200 OK'

    c = FlagonClient(app)
    r = c.open('/hello', content_type='text/plain',
                input_stream = BytesIO())
    assert r[0] == b'ok'
    assert r[1] == '200 OK'


def test_client_error():
    app = Flagon()

    @app.route('/hello')
    def hello():
        return object()

    c = FlagonClient(app)
    r = c.open('/hello')
    assert r[1] == '500 Internal Server Error'
