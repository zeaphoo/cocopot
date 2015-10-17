import pytest

from flagon.response import Response, make_response, redirect
from flagon.datastructures import MultiDict
import copy


def test_basic_response():
    r = make_response('text')
    assert r.body == 'text'
    assert r.status_line == '200 OK'
    assert r.status_code == 200
    r = make_response('redirect', 302)
    assert r.status_line == '302 Found'
    assert r.status_code == 302

    r = make_response('', 999)
    assert r.status_line == '999 Unknown'
    assert r.status_code == 999

    with pytest.raises(ValueError):
        r = make_response('', 1099)
        r = make_response('', 99)

    r = make_response('', '999 Who knows?') # Illegal, but acceptable three digit code
    assert r.status_line == '999 Who knows?'
    assert r.status_code == 999

    with pytest.raises(ValueError):
        r = make_response('', '555')
    assert r.status_line == '999 Who knows?'
    assert r.status_code == 999

def test_set_cookie():
    r = Response()
    r.set_cookie('name1', 'value', max_age=5)
    r.set_cookie('name2', 'value 2', path='/foo')
    cookies = [value for name, value in r.headerlist
               if name.title() == 'Set-Cookie']
    cookies.sort()
    assert cookies[0] == 'name1=value; Max-Age=5'
    assert cookies[1] == 'name2="value 2"; Path=/foo'

def test_set_cookie_maxage():
    import datetime
    r = Response()
    r.set_cookie('name1', 'value', max_age=5)
    r.set_cookie('name2', 'value', max_age=datetime.timedelta(days=1))
    cookies = sorted([value for name, value in r.headerlist
               if name.title() == 'Set-Cookie'])
    assert cookies[0] == 'name1=value; Max-Age=5'
    assert cookies[1] == 'name2=value; Max-Age=86400'

def test_set_cookie_expires():
    import datetime
    r = Response()
    r.set_cookie('name1', 'value', expires=42)
    r.set_cookie('name2', 'value', expires=datetime.datetime(1970,1,1,0,0,43))
    cookies = sorted([value for name, value in r.headerlist
               if name.title() == 'Set-Cookie'])
    assert cookies[0] == 'name1=value; expires=Thu, 01 Jan 1970 00:00:42 GMT'
    assert cookies[1] == 'name2=value; expires=Thu, 01 Jan 1970 00:00:43 GMT'

def test_set_cookie_secure():
    r = Response()
    r.set_cookie('name1', 'value', secure=True)
    r.set_cookie('name2', 'value', secure=False)
    cookies = sorted([value for name, value in r.headerlist
               if name.title() == 'Set-Cookie'])
    assert cookies[0] == 'name1=value; secure'
    assert cookies[1] == 'name2=value'

def test_set_cookie_httponly():
    r = Response()
    r.set_cookie('name1', 'value', httponly=True)
    r.set_cookie('name2', 'value', httponly=False)
    cookies = sorted([value for name, value in r.headerlist
               if name.title() == 'Set-Cookie'])
    assert cookies[0] == 'name1=value; httponly'
    assert cookies[1] == 'name2=value'

def test_delete_cookie():
    response = Response()
    response.set_cookie('name', 'value')
    response.delete_cookie('name')
    cookies = [value for name, value in response.headerlist
               if name.title() == 'Set-Cookie']
    assert 'name=;' in cookies[0]

def test_redirect():
    r = redirect('http://example.com/foo/new', 302)
    assert r.status_line == '302 Found'
    assert r.headers['location'] == 'http://example.com/foo/new'
    r = redirect('http://example.com/foo/new2', 301)
    assert r.status_line == '301 Moved Permanently'
    assert r.headers['location'] == 'http://example.com/foo/new2'
