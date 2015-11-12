import pytest

from flagon.datastructures import MultiDict, WSGIHeaders, FileUpload, FormsDict
import base64
from flagon._compat import PY2, to_unicode, to_bytes, BytesIO
import tempfile
import os

def test_basic_multidict():
    d = MultiDict([('a', 'b'), ('a', 'c')])
    assert d['a'] == 'b'
    assert d.getlist('a') == ['b', 'c']
    assert ('a' in d) == True
    if PY2:
        assert list(iter(d)) == list(iter({'a':['b', 'c']}))
        assert list(d.iterkeys()) == ['a']
        assert list(d.itervalues()) == ['b']
        assert list(d.iteritems()) == [('a', 'b')]

    d = MultiDict([('a', 'b'), ('a', 'c')], a='dddd')
    assert d['a'] == 'b'
    assert d.getlist('a') == ['b', 'c', 'dddd']
    assert len(d) == 1
    assert list(d.keys()) == ['a']
    assert list(d.values()) == ['b']
    d.replace('a', 'ee')
    assert d['a'] == 'ee'
    assert d.getlist('a') == ['ee']
    assert d.get('foo') == None

    del d['a']
    assert len(d) == 0


def test_wsgiheaders():
    env = {
        'REQUEST_METHOD':       'POST',
        'SCRIPT_NAME':          '/foo',
        'PATH_INFO':            '/bar',
        'QUERY_STRING':         'a=1&b=2',
        'SERVER_NAME':          'test.flagon.org',
        'SERVER_PORT':          '80',
        'HTTP_HOST':            'test.flagon.org',
        'SERVER_PROTOCOL':      'http',
        'CONTENT_TYPE':         'text/plain; charset=utf-8',
        'CONTENT_LENGTH':       '0',
        'wsgi.url_scheme':      'http',
        'HTTP_X_FORWARDED_FOR': '5.5.5.5',
    }
    user, pwd = 'marc', 'secret'
    basic = to_unicode(base64.b64encode(to_bytes('%s:%s' % (user, pwd))))
    env['HTTP_AUTHORIZATION'] = 'basic %s' % basic
    env['HTTP_COOKIE'] = 'a=a; a=b'
    w = WSGIHeaders(env)
    assert w.raw('authorization') == 'basic %s' % basic
    assert w.raw('content_type') == 'text/plain; charset=utf-8'
    assert w.raw('cookie') == 'a=a; a=b'
    assert w.raw('range') == None

    assert w['authorization'] == 'basic %s' % basic
    assert w['content_type'] == 'text/plain; charset=utf-8'

    with pytest.raises(TypeError):
        w['content_type'] = 'text/plain'

    with pytest.raises(TypeError):
        del w['range']

    assert len(w) == len(w.keys())
    assert len(w) == 6

def test_formsdict():
    form = FormsDict({'a': '111', 'b':123, 'c':b'xxx'}.items())
    assert form.a == '111'
    assert form.b == 123
    assert form.c == 'xxx'
    assert form.d == ''


def test_fileupload():
    f = FileUpload(BytesIO(to_bytes('a'*256)), 'a.txt', 'a a a.txt', headers={'Content-Type': 'text/plain', 'Content-Length': 256})
    dstpath = '%s/%s'%(tempfile.mkdtemp(), f.name)
    f.save(dstpath)
    with open(dstpath, 'rb') as df:
        assert df.read() == to_bytes('a'*256)
    try:
        os.unlink(dstpath)
    except:
        raise
