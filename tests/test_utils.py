import pytest

from flagon.utils import ConfigDict
import copy
import traceback

def test_config():
    c = ConfigDict()
    c.debug = True
    assert c.debug == True
    assert c['debug'] == True

    c['app'] = ConfigDict({'a': 1, 'b': 'foo'})
    assert c.app.a == 1
    assert c.app.b == 'foo'
    assert 'app' in c

    del c.app
    assert 'app' not in c


def test_cached_property():
    pass
