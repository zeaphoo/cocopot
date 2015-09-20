# -*- coding: utf-8 -*-
"""
    This module implements various utilities for WSGI applications.  Most of
    them are used by the request and response wrappers but especially for
    middleware development it makes sense to use them without the wrappers.
"""
import re
import os
import sys
import pkgutil
from ._compat import unichr, text_type, string_types, reraise, PY2, to_unicode, to_native, BytesIO
try:
    import simplejson as json
except:
    import json
import functools
if PY2:
    from urlparse import urljoin, SplitResult as UrlSplitResult
    from urllib import urlencode, quote as urlquote, unquote as urlunquote
else:
    from urllib.parse import urljoin, SplitResult as UrlSplitResult
    from urllib.parse import urlencode, quote as urlquote, unquote as urlunquote
    urlunquote = functools.partial(urlunquote, encoding='latin1')


def urldecode(qs):
    r = []
    for pair in qs.replace(';', '&').split('&'):
        if not pair: continue
        nv = pair.split('=', 1)
        if len(nv) != 2: nv.append('')
        key = urlunquote(nv[0].replace('+', ' '))
        value = urlunquote(nv[1].replace('+', ' '))
        r.append((key, value))
    return r

class cached_property(object):
    """ A property that is only computed once per instance and then replaces
        itself with an ordinary attribute. Deleting the attribute resets the
        property. """

    def __init__(self, func):
        self.__doc__ = getattr(func, '__doc__')
        self.func = func

    def __get__(self, obj, cls=None):
        if obj is None: return self
        if self.func.__name__ not in obj.__dict__:
            value = obj.__dict__[self.func.__name__] = self.func(obj)
        else:
            value = obj.__dict__[self.func.__name__]
        return value
