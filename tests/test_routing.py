import pytest

from cocopot.routing import Router
from cocopot.exceptions import BadRequest, NotFound, MethodNotAllowed

def test_basic_routing():
    r = Router()
    r.add('/', endpoint='index')
    r.add('/foo', endpoint='foo')
    r.add('/bar/', endpoint='bar')
    assert r.match('/') == ('index', {})
    assert r.match('/foo') == ('foo', {})
    assert r.match('/bar/') == ('bar', {})
    pytest.raises(NotFound, lambda: r.match('/blub'))
    pytest.raises(MethodNotAllowed, lambda: r.match('/foo', method='POST'))

def test_basic_routing2():
    r = Router(strict=True)
    r.add('/', endpoint='index')
    r.add('/foo', endpoint='foo')
    r.add('/bar/', endpoint='bar')
    assert r.match('/') == ('index', {})
    assert r.match('/foo') == ('foo', {})
    assert r.match('/bar/') == ('bar', {})
    pytest.raises(NotFound, lambda: r.match('/blub'))
    pytest.raises(MethodNotAllowed, lambda: r.match('/foo', method='POST'))


def test_dynamic_routing():
    r = Router()
    r.add('/<name>', endpoint='index')
    r.add('/foo/<string:name2>', endpoint='foo')
    r.add('/bar/<int:bar>', endpoint='bar')
    r.add('/float/<float:bar2>', endpoint='bar2')
    r.add('/path/<path:bar3>', endpoint='bar3')
    assert r.match('/foo') == ('index', {'name': 'foo'})
    assert r.match('/foo/bar') == ('foo', {'name2': 'bar'})
    assert r.match('/bar/20') == ('bar', {'bar': 20})
    assert r.match('/float/20.333') == ('bar2', {'bar2': 20.333})
    assert r.match('/path/foo/bar/xxx') == ('bar3', {'bar3': 'foo/bar/xxx'})


def test_default_values():
    r = Router()
    r.add('/<name>', endpoint='index', defaults={'foo': 1234, 'name':'bar'})
    assert r.match('/foo') == ('index', {'name': 'foo', 'foo': 1234})
