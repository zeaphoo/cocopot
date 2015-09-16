import pytest

from flagon import Flagon, Blueprint, request, g
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
