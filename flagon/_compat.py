# -*- coding: utf-8 -*-
"""
    flagon._compat
    ~~~~~~~~~~~~~

    Some py2/py3 compatibility support based on a stripped down
    version of six so we don't have to depend on a specific version
    of it.

    :copyright: (c) 2013 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
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

    iterkeys = lambda d, *args, **kwargs: d.iterkeys(*args, **kwargs)
    itervalues = lambda d, *args, **kwargs: d.itervalues(*args, **kwargs)
    iteritems = lambda d, *args, **kwargs: d.iteritems(*args, **kwargs)

    iterlists = lambda d, *args, **kwargs: d.iterlists(*args, **kwargs)
    iterlistvalues = lambda d, *args, **kwargs: d.iterlistvalues(*args, **kwargs)

    iter_bytes = lambda x: iter(x)

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

    iterkeys = lambda d, *args, **kwargs: iter(d.keys(*args, **kwargs))
    itervalues = lambda d, *args, **kwargs: iter(d.values(*args, **kwargs))
    iteritems = lambda d, *args, **kwargs: iter(d.items(*args, **kwargs))

    iterlists = lambda d, *args, **kwargs: iter(d.lists(*args, **kwargs))
    iterlistvalues = lambda d, *args, **kwargs: iter(d.listvalues(*args, **kwargs))

    int_to_byte = operator.methodcaller('to_bytes', 1, 'big')

    def iter_bytes(b):
        return map(int_to_byte, b)

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
    if x is None:
        return None
    return s.encode(enc) if isinstance(s, unicode) else bytes(s)


def to_unicode(s, enc='utf8', err='strict'):
    if x is None:
        return None
    if isinstance(s, bytes):
        return s.decode(enc, err)
    else:
        return unicode(s)

to_native = to_bytes if PY2 else to_unicode
