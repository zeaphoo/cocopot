import pytest

from flagon.response import Response, make_response, redirect
from flagon.datastructures import MultiDict
import copy


def test_basic_response():
    r = make_response('text')
    assert r.body == 'text'
    assert r._status_line == '200 OK'
    r = make_response('redirect', 302)
    assert r._status_line == '302 Found'

def test_redirect():
    r = redirect('http://example.com/foo/new', 302)
    assert r._status_line == '302 Found'
    assert r.headers['location'] == 'http://example.com/foo/new'
    r = redirect('http://example.com/foo/new2', 301)
    assert r._status_line == '301 Moved Permanently'
    assert r.headers['location'] == 'http://example.com/foo/new2'
