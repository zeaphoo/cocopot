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

    def fix_tuple_repr(obj):
        def __repr__(self):
            cls = self.__class__
            return '%s(%s)' % (cls.__name__, ', '.join(
                '%s=%r' % (field, self[index])
                for index, field in enumerate(cls._fields)
            ))
        obj.__repr__ = __repr__
        return obj

    def implements_iterator(cls):
        cls.next = cls.__next__
        del cls.__next__
        return cls

    def implements_to_string(cls):
        cls.__unicode__ = cls.__str__
        cls.__str__ = lambda x: x.__unicode__().encode('utf-8')
        return cls

    from itertools import imap, izip, ifilter
    range_type = xrange

    from StringIO import StringIO
    from cStringIO import StringIO as BytesIO
    NativeStringIO = BytesIO

    def make_literal_wrapper(reference):
        return lambda x: x

    def normalize_string_tuple(tup):
        """Normalizes a string tuple to a common type. Following Python 2
        rules, upgrades to unicode are implicit.
        """
        if any(isinstance(x, text_type) for x in tup):
            return tuple(to_unicode(x) for x in tup)
        return tup

    def try_coerce_native(s):
        """Try to coerce a unicode string to native if possible. Otherwise,
        leave it as unicode.
        """
        try:
            return to_native(s)
        except UnicodeError:
            return s

    wsgi_get_bytes = _identity

    def wsgi_decoding_dance(s, charset='utf-8', errors='replace'):
        return s.decode(charset, errors)

    def wsgi_encoding_dance(s, charset='utf-8', errors='replace'):
        if isinstance(s, bytes):
            return s
        return s.encode(charset, errors)

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

    fix_tuple_repr = _identity
    implements_iterator = _identity
    implements_to_string = _identity
    imap = map
    izip = zip
    ifilter = filter
    range_type = range

    from io import StringIO, BytesIO
    NativeStringIO = StringIO

    def make_literal_wrapper(reference):
        if isinstance(reference, text_type):
            return lambda x: x
        return lambda x: x.encode('latin1')

    def normalize_string_tuple(tup):
        """Ensures that all types in the tuple are either strings
        or bytes.
        """
        tupiter = iter(tup)
        is_text = isinstance(next(tupiter, None), text_type)
        for arg in tupiter:
            if isinstance(arg, text_type) != is_text:
                raise TypeError('Cannot mix str and bytes arguments (got %s)'
                    % repr(tup))
        return tup

    try_coerce_native = _identity

    def wsgi_get_bytes(s):
        return s.encode('latin1')

    def wsgi_decoding_dance(s, charset='utf-8', errors='replace'):
        return s.encode('latin1').decode(charset, errors)

    def wsgi_encoding_dance(s, charset='utf-8', errors='replace'):
        if isinstance(s, bytes):
            return s.decode('latin1', errors)
        return s.encode(charset).decode('latin1', errors)


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
