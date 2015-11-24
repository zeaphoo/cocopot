import pytest

from cocopot.utils import ConfigDict, cached_property
import copy
import traceback

def test_config_isdict():
    d, m = dict(), ConfigDict()
    d['key'], m['key'] = 'value', 'value'
    d['k2'], m['k2'] = 'v1', 'v1'
    d['k2'], m['k2'] = 'v2', 'v2'
    assert d.keys() == m.keys()
    assert list(d.values()) == list(m.values())
    assert d.get('key') == m.get('key')
    assert d.get('cay') == m.get('cay')
    assert list(iter(d)) == list(iter(m))
    assert [k for k in d] == [k for k in m]
    assert len(d) == len(m)
    assert ('key' in d) == ('key' in m)
    assert ('cay' in d) == ('cay' in m)
    with pytest.raises(KeyError):
        m['cay']

def test_config():
    c = ConfigDict()
    c.__class__
    c.debug = True
    assert c.get('debug') == True
    assert c.debug == True
    assert c['debug'] == True
    c.debug = False
    assert c.debug == False
    assert c['debug'] == False

    c['app'] = ConfigDict({'a': 1, 'b': 'foo'})
    assert c.app.a == 1
    assert c.app.b == 'foo'
    assert 'app' in c
    assert 1 not in c

    del c.app
    assert 'app' not in c
    with pytest.raises(AttributeError):
        assert c.foo == 1
        del c.foo
        assert getattr(c, 'foo') == None
        app = c.app
        setattr(c, 1, '1')
        del c.app
        del c[1]


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
    assert getattr(f, 'foo') == 2
