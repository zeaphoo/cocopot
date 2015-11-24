import pytest

from cocopot.request import Request
from cocopot.exceptions import BadRequest, NotFound, MethodNotAllowed
from cocopot.datastructures import MultiDict, FormsDict
from cocopot._compat import BytesIO, to_native, to_bytes, to_unicode
import base64
import copy
import inspect
import json

env1 = {
    'REQUEST_METHOD':       'POST',
    'SCRIPT_NAME':          '/foo',
    'PATH_INFO':            '/bar',
    'QUERY_STRING':         'a=1&b=2',
    'SERVER_NAME':          'test.cocopot.org',
    'SERVER_PORT':          '80',
    'HTTP_HOST':            'test.cocopot.org',
    'SERVER_PROTOCOL':      'http',
    'CONTENT_TYPE':         'text/plain; charset=utf-8',
    'CONTENT_LENGTH':       '0',
    'wsgi.url_scheme':      'http'
}


def test_basic_request():
    env = dict(copy.deepcopy(env1))
    req = Request(env)
    assert 'cocopot.request' in env
    assert req.args == MultiDict({'a':'1', 'b':'2'}.items())
    assert req.values == MultiDict({'a':'1', 'b':'2'}.items())
    assert req.path == '/bar'
    assert req.full_path == '/foo/bar'
    assert req.script_root == '/foo'
    assert req.url == 'http://test.cocopot.org/foo/bar?a=1&b=2'
    assert req.base_url == 'http://test.cocopot.org/foo/bar'
    assert req.root_url == 'http://test.cocopot.org/foo/'
    assert req.host_url == 'http://test.cocopot.org/'
    assert req.host == 'test.cocopot.org'
    assert req.get_data() == b''
    assert req.get_data(as_text=True) == ''
    assert req.blueprint == None
    assert req.mimetype == 'text/plain'
    assert req.mimetype_params == {'charset': 'utf-8'}
    assert req.get_json() == None
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
    assert req.method == "POST"
    assert req.url_charset == 'utf-8'
    assert "Content-Length" in req.headers
    assert "Request" in repr(req)

def test_basic_request2():
    env = dict(copy.deepcopy(env1))
    env['HTTP_X_FORWARDED_HOST'] = 'test.cocopot.org'
    req = Request(env)
    assert req.host == 'test.cocopot.org'
    env['HTTP_X_FORWARDED_HOST'] = 'test.cocopot.org, a.proxy.org'
    req = Request(env)
    assert req.host == 'test.cocopot.org'
    env = dict(copy.deepcopy(env1))
    env.pop('HTTP_HOST')
    env['SERVER_PORT'] = '8080'
    req = Request(env)
    assert req.host == 'test.cocopot.org:8080'

def test_basic_error():
    env = dict(copy.deepcopy(env1))
    env['wsgi.input'] = BytesIO(to_bytes('a'*20))
    env['CONTENT_LENGTH'] = '20a'
    req = Request(env)
    assert req.content_length == 0


def test_cookie_dict():
    """ Environ: Cookie dict """
    t = dict()
    t['a=a']      = {'a': 'a'}
    t['a=a; b=b'] = {'a': 'a', 'b':'b'}
    t['a=a; a=b'] = {'a': 'b'}
    for k, v in t.items():
        env = dict(copy.deepcopy(env1))
        env.update({'HTTP_COOKIE': k})
        req = Request(env)
        for n in v:
            assert v[n] == req.cookies[n]
            assert v[n] == req.get_cookie(n)

def test_form_data():
    env = dict(copy.deepcopy(env1))
    form_data = 'c=1&d=woo'
    env['CONTENT_TYPE'] = 'application/x-www-form-urlencoded'
    env['wsgi.input'] = BytesIO(to_bytes(form_data))
    env['CONTENT_LENGTH'] = len(form_data)
    req = Request(env)
    assert req.input_stream == env['wsgi.input']
    assert req.args == MultiDict({'a':'1', 'b':'2'}.items())
    assert req.form == FormsDict({'c':'1', 'd':'woo'}.items())
    assert req.form.c == '1'
    assert req.form.d == 'woo'
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
    env['wsgi.input'] = BytesIO(to_bytes(form_data))
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
    assert req.close() == None


def _test_chunked(body, expect):
    env = dict(copy.deepcopy(env1))
    env['wsgi.input'] = BytesIO(to_bytes(body))
    env['HTTP_TRANSFER_ENCODING'] = 'chunked'
    env['QUERY_STRING'] = ''
    req = Request(env)
    assert req.chunked == True
    if inspect.isclass(expect) and issubclass(expect, Exception):
        with pytest.raises(BadRequest):
            req.get_data()
    else:
        assert req.data == to_bytes(expect)

def test_chunked():
    _test_chunked('1\r\nx\r\nff\r\n' + 'y'*255 + '\r\n0\r\n',
                           'x' + 'y'*255)
    _test_chunked('8\r\nxxxxxxxx\r\n0\r\n','xxxxxxxx')
    _test_chunked('8\r\nxxxxxxxx\r\n'*1024*1024 + '0\r\n','xxxxxxxx'*1024*1024)
    _test_chunked('0\r\n', '')
    _test_chunked('8 ; foo\r\nxxxxxxxx\r\n0\r\n','xxxxxxxx')
    _test_chunked('8;foo\r\nxxxxxxxx\r\n0\r\n','xxxxxxxx')
    _test_chunked('8;foo=bar\r\nxxxxxxxx\r\n0\r\n','xxxxxxxx')
    _test_chunked('1\r\nx\r\n', BadRequest)
    _test_chunked('2\r\nx\r\n', BadRequest)
    _test_chunked('x\r\nx\r\n', BadRequest)
    _test_chunked('abcdefg', BadRequest)

def test_auth():
    user, pwd = 'marc', 'secret'
    basic = to_unicode(base64.b64encode(to_bytes('%s:%s' % (user, pwd))))
    env = dict(copy.deepcopy(env1))
    r = Request(env)
    assert r.authorization == None
    env['HTTP_AUTHORIZATION'] = 'basic %s' % basic
    r = Request(env)
    assert r.authorization == (user, pwd)

def test_remote_addr():
    ips = ['1.2.3.4', '2.3.4.5', '3.4.5.6']
    env = dict(copy.deepcopy(env1))
    env['HTTP_X_FORWARDED_FOR'] = ', '.join(ips)
    r = Request(env)
    assert r.remote_addr == ips[0]

    env = dict(copy.deepcopy(env1))
    env['HTTP_X_FORWARDED_FOR'] = ', '.join(ips)
    env['REMOTE_ADDR'] = ips[1]
    r = Request(env)
    assert r.remote_addr == ips[0]

    env = dict(copy.deepcopy(env1))
    env['REMOTE_ADDR'] = ips[1]
    r = Request(env)
    assert r.remote_addr == ips[1]

def test_remote_route():
    ips = ['1.2.3.4', '2.3.4.5', '3.4.5.6']
    env = dict(copy.deepcopy(env1))
    env['HTTP_X_FORWARDED_FOR'] = ', '.join(ips)
    r = Request(env)
    assert r.remote_route == ips

    env = dict(copy.deepcopy(env1))
    env['HTTP_X_FORWARDED_FOR'] = ', '.join(ips)
    env['REMOTE_ADDR'] = ips[1]
    r = Request(env)
    assert r.remote_route == ips

    env = dict(copy.deepcopy(env1))
    env['REMOTE_ADDR'] = ips[1]
    r = Request(env)
    assert r.remote_route == [ips[1],]


def test_json_header_empty_body():
    """Request Content-Type is application/json but body is empty"""
    env = dict(copy.deepcopy(env1))
    env['CONTENT_TYPE'] = 'application/json; charset=UTF-8'
    env['CONTENT_LENGTH'] = 0
    r = Request(env)
    assert r.json == None

def test_json_valid():
    """ Environ: Request.json property. """
    test = dict(a=5, b='test', c=[1,2,3])
    env = dict(copy.deepcopy(env1))
    env['CONTENT_TYPE'] = 'application/json; charset=UTF-8'
    env['wsgi.input'] = BytesIO(to_bytes(json.dumps(test)))
    env['CONTENT_LENGTH'] = str(len(json.dumps(test)))
    r = Request(env)
    assert r.json == test


def test_json_forged_header_issue616():
    test = dict(a=5, b='test', c=[1,2,3])
    env = dict(copy.deepcopy(env1))
    env['CONTENT_TYPE'] = 'text/plain;application/json'
    env['wsgi.input'] = BytesIO(to_bytes(json.dumps(test)))
    env['CONTENT_LENGTH'] = str(len(json.dumps(test)))
    r = Request(env)
    assert r.json == None
