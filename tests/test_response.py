import pytest

from flagon.response import Response, make_response
from flagon.datastructures import MultiDict
import copy


def test_basic_response():
    r = make_response('text')
    assert r.body == 'text'
    assert r._status_line == '200 OK'
    r = make_response('redirect', 302)
    assert r._status_line == '302 Found'
