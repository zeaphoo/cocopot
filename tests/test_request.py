import pytest

from flagon.request import Request
from flagon.exceptions import BadRequest, NotFound, MethodNotAllowed
import copy

env1 = {
    'REQUEST_METHOD':       'GET',
    'SCRIPT_NAME':          '/foo',
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

def test_basic_request():
    env = dict(copy.deepcopy(env1))
    req = Request(env)
    assert 'flagon.request' in env
