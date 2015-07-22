# -*- coding: utf-8 -*-
"""
    flagon.datastructures
"""
import re
import sys
import codecs
import mimetypes
from copy import deepcopy
from itertools import repeat
from collections import MutableMapping as DictMixin
from ._compat import PY2


class MultiDict(DictMixin):
    """ This dict stores multiple values per key, but behaves exactly like a
        normal dict in that it returns only the newest value for any given key.
        There are special methods available to access the full list of values.

        Basic Usage:

        >>> d = MultiDict([('a', 'b'), ('a', 'c')])
        >>> d
        MultiDict([('a', 'b'), ('a', 'c')])
        >>> d['a']
        'b'
        >>> d.getlist('a')
        ['b', 'c']
        >>> 'a' in d
        True
    """

    def __init__(self, *a, **kwargs):
        self.dict = {}
        for pl in a:
            for k, v in pl:
                l = self.dict.setdefault(k, [])
                l.append(v)
        for k, v in kwargs.items():
            l = self.dict.setdefault(k, [])
            l.append(v)
        #self.dict = dict((k, [v]) for (k, v) in dict(*a, **k).items())
        print 'init', self.dict

    def __len__(self):
        return len(self.dict)

    def __iter__(self):
        return iter(self.dict)

    def __contains__(self, key):
        return key in self.dict

    def __delitem__(self, key):
        del self.dict[key]

    def __getitem__(self, key):
        print self.dict[key]
        return self.dict[key][0]

    def __setitem__(self, key, value):
        self.append(key, value)

    def keys(self):
        return self.dict.keys()

    if PY2:
        def values(self):
            return [v[0] for v in self.dict.values()]

        def items(self):
            return [(k, v[0]) for k, v in self.dict.items()]

        def iterkeys(self):
            return self.dict.iterkeys()

        def itervalues(self):
            return (v[0] for v in self.dict.itervalues())

        def iteritems(self):
            return ((k, v[0]) for k, v in self.dict.iteritems())

        def iterallitems(self):
            return ((k, v) for k, vl in self.dict.iteritems() for v in vl)

        def allitems(self):
            return [(k, v) for k, vl in self.dict.iteritems() for v in vl]

    else:
        def values(self):
            return (v[0] for v in self.dict.values())

        def items(self):
            return ((k, v[0]) for k, v in self.dict.items())

        def allitems(self):
            return ((k, v) for k, vl in self.dict.items() for v in vl)

        iterkeys = keys
        itervalues = values
        iteritems = items
        iterallitems = allitems


    def get(self, key, default=None, index=0, type=None):
        """ Return the most recent value for a key.
            :param default: The default value to be returned if the key is not
                   present or the type conversion fails.
            :param index: An index for the list of available values.
            :param type: If defined, this callable is used to cast the value
                    into a specific type. Exception are suppressed and result in
                    the default value to be returned.
        """
        try:
            print self.dict[key]
            val = self.dict[key][index]
            return type(val) if type else val
        except Exception:
            pass
        return default

    def append(self, key, value):
        """ Add a new value to the list of values for this key. """
        self.dict.setdefault(key, []).append(value)

    def replace(self, key, value):
        """ Replace the list of values with a single value. """
        self.dict[key] = [value]

    def getall(self, key):
        """ Return a (possibly empty) list of values for a key. """
        return self.dict.get(key) or []

    #: Aliases for WTForms to mimic other multi-dict APIs (Django)
    getone = get
    getlist = getall


class FormsDict(MultiDict):
    """ This :class:`MultiDict` subclass is used to store request form data.
        Additionally to the normal dict-like item access methods (which return
        unmodified data as native strings), this container also supports
        attribute-like access to its values. Attributes are automatically de-
        or recoded to match :attr:`input_encoding` (default: 'utf8'). Missing
        attributes default to an empty string. """

    #: Encoding used for attribute values.
    input_encoding = 'utf8'
    #: If true (default), unicode strings are first encoded with `latin1`
    #: and then decoded to match :attr:`input_encoding`.
    recode_unicode = True

    def _fix(self, s, encoding=None):
        if isinstance(s, unicode) and self.recode_unicode:  # Python 3 WSGI
            return s.encode('latin1').decode(encoding or self.input_encoding)
        elif isinstance(s, bytes):  # Python 2 WSGI
            return s.decode(encoding or self.input_encoding)
        else:
            return s

    def decode(self, encoding=None):
        """ Returns a copy with all keys and values de- or recoded to match
            :attr:`input_encoding`. Some libraries (e.g. WTForms) want a
            unicode dictionary. """
        copy = FormsDict()
        enc = copy.input_encoding = encoding or self.input_encoding
        copy.recode_unicode = False
        for key, value in self.allitems():
            copy.append(self._fix(key, enc), self._fix(value, enc))
        return copy

    def getunicode(self, name, default=None, encoding=None):
        """ Return the value as a unicode string, or the default. """
        try:
            return self._fix(self[name], encoding)
        except (UnicodeError, KeyError):
            return default

    def __getattr__(self, name, default=unicode()):
        # Without this guard, pickle generates a cryptic TypeError:
        if name.startswith('__') and name.endswith('__'):
            return super(FormsDict, self).__getattr__(name)
        return self.getunicode(name, default=default)
