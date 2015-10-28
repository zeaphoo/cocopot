import pytest

from flagon.datastructures import MultiDict

def test_basic_multidict():
    d = MultiDict([('a', 'b'), ('a', 'c')])
    assert d['a'] == 'b'
    assert d.getlist('a') == ['b', 'c']
    assert ('a' in d) == True

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
