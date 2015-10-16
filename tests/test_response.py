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


def test_redirect():
    r = redirect('http://example.com/foo/new', 302)
    assert r.status_line == '302 Found'
    assert r.headers['location'] == 'http://example.com/foo/new'
    r = redirect('http://example.com/foo/new2', 301)
    assert r.status_line == '301 Moved Permanently'
    assert r.headers['location'] == 'http://example.com/foo/new2'
