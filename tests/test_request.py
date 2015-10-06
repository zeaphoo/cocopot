import pytest

from flagon.request import Request
from flagon.exceptions import BadRequest, NotFound, MethodNotAllowed
from flagon.datastructures import MultiDict, FormsDict
from flagon._compat import BytesIO
import copy

env1 = {
    'REQUEST_METHOD':       'GET',
    'SCRIPT_NAME':          '/foo',
    'PATH_INFO':            '/bar',
    'QUERY_STRING':         'a=1&b=2',
    'SERVER_NAME':          'test.flagon.org',
    'SERVER_PORT':          80,
    'HTTP_HOST':            'test.flagon.org',
    'SERVER_PROTOCOL':      'http',
    'CONTENT_TYPE':         'text/plain; charset=utf-8',
    'CONTENT_LENGTH':       '0',
    'wsgi.url_scheme':      'http'
}

def test_basic_request():
    env = dict(copy.deepcopy(env1))
    req = Request(env)
    assert 'flagon.request' in env
    assert req.args == MultiDict({'a':'1', 'b':'2'}.items())
    assert req.values == MultiDict({'a':'1', 'b':'2'}.items())
    assert req.path == '/bar'
    assert req.full_path == '/foo/bar'
    assert req.script_root == '/foo'
    assert req.url == 'http://test.flagon.org/foo/bar?a=1&b=2'
    assert req.base_url == 'http://test.flagon.org/foo/bar'
    assert req.root_url == 'http://test.flagon.org/foo/'
    assert req.host_url == 'http://test.flagon.org/'
    assert req.host == 'test.flagon.org'
    assert req.get_data() == ''
    assert req.blueprint == None
    assert req.mimetype == 'text/plain'
    assert req.mimetype_params == {'charset': 'utf-8'}
    assert req.get_json() == None
    assert req.content_length == 0
    assert req.authorization == None

def test_form_data():
    env = dict(copy.deepcopy(env1))
    form_data = 'c=1&d=woo'
    env['CONTENT_TYPE'] = 'application/x-www-form-urlencoded'
    env['wsgi.input'] = BytesIO(form_data)
    env['CONTENT_LENGTH'] = len(form_data)
    req = Request(env)
    assert req.args == MultiDict({'a':'1', 'b':'2'}.items())
    assert req.form == FormsDict({'c':'1', 'd':'woo'}.items())
    assert req.values == MultiDict({'a':'1', 'b':'2', 'c':'1', 'd':'woo'}.items())
