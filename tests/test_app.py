# -*- coding: utf-8 -*-
import pytest

from flagon import Flagon, Blueprint, request, g, abort
from flagon.testing import FlagonClient
import copy
import traceback

env1 = {
    'REQUEST_METHOD':       'GET',
    'SCRIPT_NAME':          '',
    'PATH_INFO':            '/foo/bar',
    'QUERY_STRING':         'a=1&b=2',
    'SERVER_NAME':          'test.flagon.org',
    'SERVER_PORT':          80,
    'HTTP_HOST':            'test.flagon.org',
    'SERVER_PROTOCOL':      'http',
    'CONTENT_TYPE':         '',
    'CONTENT_LENGTH':       '0',
    'wsgi.url_scheme':      'http'
}

def start_response(x, y):
    print x, y

def test_basic_app():
    app = Flagon()
    @app.before_request
    def before_request1():
        print 'before_request'
        g.a = 1

    @app.before_request
    def before_request2():
        print 'before_request2'
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
        print traceback.format_exc()
        return '500'

    assert app.before_request_funcs[None][0] == before_request1
    assert app.before_request_funcs[None][1] == before_request2
    assert app.after_request_funcs[None][0] == after_request2
    assert app.after_request_funcs[None][1] == after_request1

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

    @bp.errorhandler(Exception)
    def bp_errorhandler(exception):
        pass

    app.register_blueprint(bp)
    assert app.before_request_funcs[None][2] == bp_app_before_request
    assert app.before_request_funcs['foo'][0] == bp_before_request

    env = copy.deepcopy(env1)
    env['PATH_INFO'] = '/hello'
    assert app(env, start_response)  == 'ok'
    env = copy.deepcopy(env1)
    env['PATH_INFO'] = '/foo/bar'
    assert app(env, start_response)  == 'bar'
    env = copy.deepcopy(env1)
    env['PATH_INFO'] = '/foo2'
    assert app(env, start_response)  == '404'

def test_blueprint_errorhandler():
    app = Flagon()

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
    assert app(env, start_response)  == 'bar'

    env = copy.deepcopy(env1)
    env['PATH_INFO'] = '/foo/bar2'
    assert app(env, start_response)  == 'bar2'


def test_blueprint():
    app = Flagon()

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
    assert app(env, start_response)  == 'bar'

    env = copy.deepcopy(env1)
    env['PATH_INFO'] = '/foo/bar2'
    assert app(env, start_response)  == 'bar2'

    env = copy.deepcopy(env1)
    env['PATH_INFO'] = '/foo2/bar'
    assert app(env, start_response)  == 'bar'

    env = copy.deepcopy(env1)
    env['PATH_INFO'] = '/foo2/bar2'
    assert app(env, start_response)  == 'bar2'

def test_unicode_route():
    app = Flagon()

    @app.route(u'/地球')
    def hello():
        return u'你好地球'

    c = FlagonClient(app)
    r = c.open(u'/地球')
    assert r[0] == u'你好地球'
    assert r[1] == '200 OK'
