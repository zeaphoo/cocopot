import pytest

from flagon.request import Request
from flagon.exceptions import BadRequest, NotFound, MethodNotAllowed
from flagon.datastructures import MultiDict, FormsDict
from flagon._compat import BytesIO
import copy
import inspect

env1 = {
    'REQUEST_METHOD':       'POST',
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
    assert req.cookies == FormsDict()
    assert list(req.range) == []
    assert req.access_route == []
    assert req.is_xhr == False
    assert req.is_secure == False
    assert req.if_modified_since == None
    assert req.if_unmodified_since == None
    assert req.access_route == []
    assert req.remote_addr == None
    assert req.chunked == False

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

def test_multipart():
    env = dict(copy.deepcopy(env1))
    form_data = '''-----------------------------9051914041544843365972754266
Content-Disposition: form-data; name="text"

text default
-----------------------------9051914041544843365972754266
Content-Disposition: form-data; name="file1"; filename="a.txt"
Content-Type: text/plain

Content of a.txt.

-----------------------------9051914041544843365972754266
Content-Disposition: form-data; name="file2"; filename="a.html"
Content-Type: text/html

<!DOCTYPE html><title>Content of a.html.</title>

-----------------------------9051914041544843365972754266--
'''
    env['CONTENT_TYPE'] = 'multipart/form-data; boundary=---------------------------9051914041544843365972754266'
    env['wsgi.input'] = BytesIO(form_data)
    env['CONTENT_LENGTH'] = len(form_data)
    env['QUERY_STRING'] = ''
    req = Request(env)
    assert req.args == MultiDict()
    assert req.form == FormsDict({'text':'text default'}.items())
    assert req.values == MultiDict({'text':'text default'}.items())
    a_txt = req.files['file1']
    a_html = req.files['file2']
    assert a_txt.filename == 'a.txt'
    assert a_txt.headers['Content-Type'] == 'text/plain'
    assert a_html.filename == 'a.html'
    assert a_html.headers['Content-Type'] == 'text/html'


def _test_chunked(body, expect):
    env = dict(copy.deepcopy(env1))
    env['wsgi.input'] = BytesIO(body)
    env['HTTP_TRANSFER_ENCODING'] = 'chunked'
    env['QUERY_STRING'] = ''
    req = Request(env)
    assert req.chunked == True
    if inspect.isclass(expect) and issubclass(expect, Exception):
        with pytest.raises(BadRequest):
            req.get_data()
    else:
        assert req.data == expect

def test_chunked():
    _test_chunked('1\r\nx\r\nff\r\n' + 'y'*255 + '\r\n0\r\n',
                           'x' + 'y'*255)
    _test_chunked('8\r\nxxxxxxxx\r\n0\r\n','xxxxxxxx')
    _test_chunked('0\r\n', '')
    _test_chunked('8 ; foo\r\nxxxxxxxx\r\n0\r\n','xxxxxxxx')
    _test_chunked('8;foo\r\nxxxxxxxx\r\n0\r\n','xxxxxxxx')
    _test_chunked('8;foo=bar\r\nxxxxxxxx\r\n0\r\n','xxxxxxxx')
    _test_chunked('1\r\nx\r\n', BadRequest)
    _test_chunked('2\r\nx\r\n', BadRequest)
    _test_chunked('x\r\nx\r\n', BadRequest)
    _test_chunked('abcdefg', BadRequest)
