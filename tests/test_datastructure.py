import pytest

from flagon.datastructures import MultiDict
from flagon._compat import PY2

def test_basic_multidict():
    d = MultiDict([('a', 'b'), ('a', 'c')])
    assert d['a'] == 'b'
    assert d.getlist('a') == ['b', 'c']
    assert ('a' in d) == True
    if PY2:
        assert list(iter(d)) == list(iter({'a':['b', 'c']}))
        assert list(d.iterkeys()) == ['a']
        assert list(d.itervalues()) == ['b']
        assert list(d.iteritems()) == [('a', 'b')]

    d = MultiDict([('a', 'b'), ('a', 'c')], a='dddd')
    assert d['a'] == 'b'
    assert d.getlist('a') == ['b', 'c', 'dddd']
    assert len(d) == 1
    assert list(d.keys()) == ['a']
    assert list(d.values()) == ['b']
    d.replace('a', 'ee')
    assert d['a'] == 'ee'
    assert d.getlist('a') == ['ee']
    assert d.get('foo') == None

    del d['a']
    assert len(d) == 0
