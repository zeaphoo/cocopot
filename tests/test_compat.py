import pytest

from cocopot._compat import *
import copy
import traceback
import sys

def test_compat():
    assert to_bytes(None) == None
    assert to_unicode(None) == None
    with pytest.raises(ZeroDivisionError):
        try:
            s = 1/0
        except:
            exc_type, exc_value, tb = sys.exc_info()
            reraise(exc_type, exc_value, tb)

    with pytest.raises(ZeroDivisionError):
        try:
            s = 1/0
        except:
            exc_type, exc_value, tb = sys.exc_info()
            reraise(exc_type, exc_value, None)
