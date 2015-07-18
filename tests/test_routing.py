import pytest

from flagon.routing import Router
from flagon.exceptions import BadRequest, NotFound, MethodNotAllowed

def test_basic_routing():
    print('test_basic_routing')
    r = Router()
    r.add('/', endpoint='index')
    r.add('/foo', endpoint='foo')
    r.add('/bar/', endpoint='bar')
    assert r.match('/') == ('index', {})
    assert r.match('/foo') == ('foo', {})
    assert r.match('/bar/') == ('bar', {})
    pytest.raises(NotFound, lambda: r.match('/blub'))
    pytest.raises(MethodNotAllowed, lambda: r.match('/foo', method='POST'))
