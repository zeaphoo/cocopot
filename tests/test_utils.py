import pytest

from flagon.utils import ConfigDict, cached_property
import copy
import traceback

def test_config():
    c = ConfigDict()
    c.debug = True
    assert c.debug == True
    assert c['debug'] == True
    c.debug = False
    assert c.debug == False
    assert c['debug'] == False

    c['app'] = ConfigDict({'a': 1, 'b': 'foo'})
    assert c.app.a == 1
    assert c.app.b == 'foo'
    assert 'app' in c

    del c.app
    assert 'app' not in c
    with pytest.raises(AttributeError):
        app = c.app
        del c.app


def test_cached_property():
    class Foo(object):
        def __init__(self):
            self.num = 1

        @cached_property
        def foo(self):
            self.num += 1
            return self.num

    f = Foo()
    assert f.foo == 2
    assert f.foo == 2
