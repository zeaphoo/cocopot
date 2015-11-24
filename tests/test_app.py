# -*- coding: utf-8 -*-
import pytest

from cocopot import Cocopot, Blueprint, request, g, abort
from cocopot._compat import to_bytes
from cocopot.request import Request
from cocopot.app import RequestContextGlobals, RequestContext
from cocopot.testing import FlagonClient
import copy
import traceback

env1 = {
    'REQUEST_METHOD':       'GET',
    'SCRIPT_NAME':          '',
    'PATH_INFO':            '/foo/bar',
    'QUERY_STRING':         'a=1&b=2',
    'SERVER_NAME':          'test.cocopot.org',
    'SERVER_PORT':          80,
    'HTTP_HOST':            'test.cocopot.org',
    'SERVER_PROTOCOL':      'http',
    'CONTENT_TYPE':         '',
    'CONTENT_LENGTH':       '0',
    'wsgi.url_scheme':      'http'
}

def test_context_globals():
    contextg = RequestContextGlobals()
    contextg.foo = 'foo'
    assert contextg.get('foo') == 'foo'
    assert 'foo' in contextg
    attrs = [key for key in contextg]
    assert attrs == ['foo']
    s = repr(contextg)

def test_request_context():
    env = copy.deepcopy(env1)
    r = Request(env)
    context = RequestContext(Cocopot(), env, r, foo='foo', bar=123)
    with context:
        assert g.foo == 'foo'
        assert g.bar == 123


def start_response(x, y):
    print((x, y))

def test_basic_app():
    app = Cocopot(__name__)
    assert app.name == 'tests.test_app'

    app.add_url_rule('/hello', 'hello', lambda x: 'ok')

    with pytest.raises(AssertionError):
        app.add_url_rule('/hello', 'hello', lambda x: 'ok')

    @app.endpoint('foo')
    def foo():
        return 'foo'
    app.add_url_rule('/foo', 'foo')

    def error_handler(exception):
        return '500'

    app.register_error_handler(Exception, error_handler)


def test_more_app():
    app = Cocopot()
    assert 'Cocopot' in repr(app)

    @app.before_request
    def before_request1():
        print('before_request')
        g.a = 1

    @app.before_request
    def before_request2():
        print('before_request2')
        g.b = 2

    @app.route('/hello')
    def hello():
        return 'ok'

    @app.after_request
    def after_request1(resp):
        return resp

    @app.after_request
    def after_request2(resp):
        return resp

    @app.errorhandler(404)
    def error_handler404(exception):
        return '404'

    @app.errorhandler(500)
    def error_handler500(exception):
        print(traceback.format_exc())
        return '500'

    @app.teardown_request
    def teardown_request(exc=None):
        pass

    assert app.before_request_funcs[None][0] == before_request1
    assert app.before_request_funcs[None][1] == before_request2
    assert app.after_request_funcs[None][0] == after_request2
    assert app.after_request_funcs[None][1] == after_request1

    bp = Blueprint('foo', url_prefix='/foo')
    @bp.before_request
    def bp_before_request():
        pass

    @bp.after_request
    def bp_after_request(resp):
        return resp

    @bp.teardown_request
    def bp_teardown_request(exc):
        pass

    @bp.route('/bar')
    def bar():
        return 'bar'

    @bp.before_app_request
    def bp_app_before_request():
        pass

    @bp.errorhandler(Exception)
    def bp_errorhandler(exception):
        pass

    app.register_blueprint(bp)
    assert app.before_request_funcs[None][2] == bp_app_before_request
    assert app.before_request_funcs['foo'][0] == bp_before_request

    env = copy.deepcopy(env1)
    env['PATH_INFO'] = '/hello'
    assert app(env, start_response)[0]  == b'ok'
    env = copy.deepcopy(env1)
    env['PATH_INFO'] = '/foo/bar'
    assert app(env, start_response)[0]  == b'bar'
    env = copy.deepcopy(env1)
    env['PATH_INFO'] = '/foo2'
    assert app(env, start_response)[0]  == b'404'

def test_basic_blueprint():
    app = Cocopot()
    bp = Blueprint('foo', url_prefix='/foo')

    @bp.before_request
    def bp_before_request():
        pass

    @bp.route('/bar')
    def bar():
        return 'bar'

    @bp.before_app_request
    def bp_app_before_request():
        pass

    @bp.after_request
    def bp_after_request(resp):
        pass

    @bp.after_app_request
    def bp_after_app_request(resp):
        pass

    @bp.teardown_request
    def bp_teardown_request(exc):
        pass

    @bp.teardown_app_request
    def bp_teardown_app_request(exc):
        pass

    @bp.errorhandler(Exception)
    def bp_errorhandler(exception):
        pass

    @bp.app_errorhandler(Exception)
    def bp_app_errorhandler(exception):
        pass

    @bp.endpoint('bbb')
    def bbb():
        return 'ok'

    app.register_blueprint(bp)

    assert app.view_functions['foo.bbb'] == bbb

    @bp.route('/bar2')
    def bar2():
        return 'bar2'

def test_blueprint_errorhandler():
    app = Cocopot()

    bp = Blueprint('foo', url_prefix='/foo')

    @bp.route('/bar')
    def bar():
        abort(400)
        return 'bar'

    @bp.route('/bar2')
    def bar2():
        i = 1/0
        return 'bar'

    @bp.errorhandler(400)
    def bp_errorhandler400(exception):
        return 'bar'

    @bp.errorhandler(Exception)
    def bp_errorhandler(exception):
        return 'bar2'

    app.register_blueprint(bp)

    env = copy.deepcopy(env1)
    env['PATH_INFO'] = '/foo/bar'
    assert app(env, start_response)[0]  == b'bar'

    env = copy.deepcopy(env1)
    env['PATH_INFO'] = '/foo/bar2'
    assert app(env, start_response)[0]  == b'bar2'


def test_blueprint():
    app = Cocopot()

    bp = Blueprint('foo', url_prefix='/foo')

    @bp.route('/bar')
    def bar():
        return 'bar'

    @bp.route('/bar2')
    def bar2():
        return 'bar2'

    app.register_blueprint(bp)
    app.register_blueprint(bp, url_prefix='/foo2')

    env = copy.deepcopy(env1)
    env['PATH_INFO'] = '/foo/bar'
    assert app(env, start_response)[0]  == b'bar'

    env = copy.deepcopy(env1)
    env['PATH_INFO'] = '/foo/bar2'
    assert app(env, start_response)[0]  == b'bar2'

    env = copy.deepcopy(env1)
    env['PATH_INFO'] = '/foo2/bar'
    assert app(env, start_response)[0]  == b'bar'

    env = copy.deepcopy(env1)
    env['PATH_INFO'] = '/foo2/bar2'
    assert app(env, start_response)[0]  == b'bar2'

def test_unicode_route():
    app = Cocopot()

    @app.route(u'/地球')
    def hello():
        return u'你好地球'

    c = FlagonClient(app)
    r = c.open(u'/地球')
    assert r[0] == to_bytes(u'你好地球')
    assert r[1] == '200 OK'
