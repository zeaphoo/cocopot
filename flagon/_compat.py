# -*- coding: utf-8 -*-
"""
    Some py2/py3 compatibility support based on a stripped down
    version of six so we don't have to depend on a specific version
    of it.

"""
import sys

PY2 = sys.version_info[0] == 2
_identity = lambda x: x

import sys
import operator
import functools
try:
    import builtins
except ImportError:
    import __builtin__ as builtins


if PY2:
    unichr = unichr
    text_type = unicode
    string_types = (str, unicode)
    integer_types = (int, long)
    int_to_byte = chr

    exec('def reraise(tp, value, tb=None):\n raise tp, value, tb')

    from itertools import imap, izip, ifilter
    range_type = xrange

    from StringIO import StringIO
    from cStringIO import StringIO as BytesIO

else:
    unichr = chr
    text_type = str
    string_types = (str, )
    integer_types = (int, )

    def reraise(tp, value, tb=None):
        if value.__traceback__ is not tb:
            raise value.with_traceback(tb)
        raise value

    imap = map
    izip = zip
    ifilter = filter
    range_type = range

    from io import StringIO, BytesIO

# Some helpers for string/byte handling
def to_bytes(s, enc='utf8'):
    if s is None:
        return None
    return s.encode(enc) if isinstance(s, text_type) else bytes(s)


def to_unicode(s, enc='utf8', err='strict'):
    if s is None:
        return None
    if isinstance(s, bytes):
        return s.decode(enc, err)
    else:
        return text_type(s)

to_native = to_bytes if PY2 else to_unicode
