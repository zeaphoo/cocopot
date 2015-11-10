import pytest

from flagon.http import parse_content_type, parse_auth, parse_date, http_date, html_quote, parse_range_header
from flagon.local import LocalStack, LocalProxy
from flagon._compat import PY2
import copy
import time
from datetime import datetime

def test_localstack():
    s = LocalStack()
    s.push(42)
    assert s.top == 42
    s.push(23)
    assert s.top == 23
    assert s.pop() == 23
    assert s.top == 42
    assert s.pop() == 42
    assert s.top == None
    assert s.pop() == None
    s._stack = {}
    assert s.pop() == None


def test_localproxy():
    class Foo(object):
        pass
    d = Foo()
    setattr(d, 'foo', {'a': '123', 'b':1234, 'c':55.5})
    p = LocalProxy(d, 'foo')
    assert repr(p) == repr(d.foo)
    assert bool(p) == bool(d.foo)
    assert dir(p) == dir(d.foo)
    d.foo = [1, 23, 34]
    assert p[1] == 23
    assert p[0:2] == [1, 23]
    del p[1]
    assert p[1] == 34
    del p[:]

    p = LocalProxy(object(), 'notexist')
    with pytest.raises(RuntimeError):
        p.notexist

    assert 'unbound>' in repr(p)
    assert bool(p) == False
    assert dir(p) == []

    if PY2:
        assert unicode(p) == repr(p)
