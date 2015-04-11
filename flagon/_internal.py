# -*- coding: utf-8 -*-
"""
    flagon._internal
    ~~~~~~~~~~~~~~~~~~

    This module provides internally used helpers and constants.

    :copyright: (c) 2014 by the Werkzeug Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""

from __future__ import absolute_import
import re
import string
import inspect
from weakref import WeakKeyDictionary
from datetime import datetime, date
from itertools import chain

from flagon._compat import iter_bytes, text_type, BytesIO, int_to_byte, \
     range_type, to_native


_logger = None
_empty_stream = BytesIO()
_signature_cache = WeakKeyDictionary()
_epoch_ord = date(1970, 1, 1).toordinal()
_cookie_params = set((b'expires', b'path', b'comment',
                      b'max-age', b'secure', b'httponly',
                      b'version'))
_legal_cookie_chars = (string.ascii_letters +
                       string.digits +
                       u"!#$%&'*+-.^_`|~:").encode('ascii')

_cookie_quoting_map = {
    b',' : b'\\054',
    b';' : b'\\073',
    b'"' : b'\\"',
    b'\\' : b'\\\\',
}
for _i in chain(range_type(32), range_type(127, 256)):
    _cookie_quoting_map[int_to_byte(_i)] = ('\\%03o' % _i).encode('latin1')


_octal_re = re.compile(b'\\\\[0-3][0-7][0-7]')
_quote_re = re.compile(b'[\\\\].')
_legal_cookie_chars_re = b'[\w\d!#%&\'~_`><@,:/\$\*\+\-\.\^\|\)\(\?\}\{\=]'
_cookie_re = re.compile(b"""(?x)
    (?P<key>[^=]+)
    \s*=\s*
    (?P<val>
        "(?:[^\\\\"]|\\\\.)*" |
         (?:.*?)
    )
    \s*;
""")


class _Missing(object):

    def __repr__(self):
        return 'no value'

    def __reduce__(self):
        return '_missing'

_missing = _Missing()


def _get_environ(obj):
    env = getattr(obj, 'environ', obj)
    assert isinstance(env, dict), \
        '%r is not a WSGI environment (has to be a dict)' % type(obj).__name__
    return env


def _log(type, message, *args, **kwargs):
    """Log into the internal flagon. logger."""
    global _logger
    if _logger is None:
        import logging
        _logger = logging.getLogger('flagon')
        # Only set up a default log handler if the
        # end-user application didn't set anything up.
        if not logging.root.handlers and _logger.level == logging.NOTSET:
            _logger.setLevel(logging.INFO)
            handler = logging.StreamHandler()
            _logger.addHandler(handler)
    getattr(_logger, type)(message.rstrip(), *args, **kwargs)


def _parse_signature(func):
    """Return a signature object for the function."""
    if hasattr(func, 'im_func'):
        func = func.im_func

    # if we have a cached validator for this function, return it
    parse = _signature_cache.get(func)
    if parse is not None:
        return parse

    # inspect the function signature and collect all the information
    positional, vararg_var, kwarg_var, defaults = inspect.getargspec(func)
    defaults = defaults or ()
    arg_count = len(positional)
    arguments = []
    for idx, name in enumerate(positional):
        if isinstance(name, list):
            raise TypeError('cannot parse functions that unpack tuples '
                            'in the function signature')
        try:
            default = defaults[idx - arg_count]
        except IndexError:
            param = (name, False, None)
        else:
            param = (name, True, default)
        arguments.append(param)
    arguments = tuple(arguments)

    def parse(args, kwargs):
        new_args = []
        missing = []
        extra = {}

        # consume as many arguments as positional as possible
        for idx, (name, has_default, default) in enumerate(arguments):
            try:
                new_args.append(args[idx])
            except IndexError:
                try:
                    new_args.append(kwargs.pop(name))
                except KeyError:
                    if has_default:
                        new_args.append(default)
                    else:
                        missing.append(name)
            else:
                if name in kwargs:
                    extra[name] = kwargs.pop(name)

        # handle extra arguments
        extra_positional = args[arg_count:]
        if vararg_var is not None:
            new_args.extend(extra_positional)
            extra_positional = ()
        if kwargs and not kwarg_var is not None:
            extra.update(kwargs)
            kwargs = {}

        return new_args, kwargs, missing, extra, extra_positional, \
               arguments, vararg_var, kwarg_var
    _signature_cache[func] = parse
    return parse


def _date_to_unix(arg):
    """Converts a timetuple, integer or datetime object into the seconds from
    epoch in utc.
    """
    if isinstance(arg, datetime):
        arg = arg.utctimetuple()
    elif isinstance(arg, (int, long, float)):
        return int(arg)
    year, month, day, hour, minute, second = arg[:6]
    days = date(year, month, 1).toordinal() - _epoch_ord + day - 1
    hours = days * 24 + hour
    minutes = hours * 60 + minute
    seconds = minutes * 60 + second
    return seconds


class _DictAccessorProperty(object):
    """Baseclass for `environ_property` and `header_property`."""
    read_only = False

    def __init__(self, name, default=None, load_func=None, dump_func=None,
                 read_only=None, doc=None):
        self.name = name
        self.default = default
        self.load_func = load_func
        self.dump_func = dump_func
        if read_only is not None:
            self.read_only = read_only
        self.__doc__ = doc

    def __get__(self, obj, type=None):
        if obj is None:
            return self
        storage = self.lookup(obj)
        if self.name not in storage:
            return self.default
        rv = storage[self.name]
        if self.load_func is not None:
            try:
                rv = self.load_func(rv)
            except (ValueError, TypeError):
                rv = self.default
        return rv

    def __set__(self, obj, value):
        if self.read_only:
            raise AttributeError('read only property')
        if self.dump_func is not None:
            value = self.dump_func(value)
        self.lookup(obj)[self.name] = value

    def __delete__(self, obj):
        if self.read_only:
            raise AttributeError('read only property')
        self.lookup(obj).pop(self.name, None)

    def __repr__(self):
        return '<%s %s>' % (
            self.__class__.__name__,
            self.name
        )


def _cookie_quote(b):
    buf = bytearray()
    all_legal = True
    _lookup = _cookie_quoting_map.get
    _push = buf.extend

    for char in iter_bytes(b):
        if char not in _legal_cookie_chars:
            all_legal = False
            char = _lookup(char, char)
        _push(char)

    if all_legal:
        return bytes(buf)
    return bytes(b'"' + buf + b'"')


def _cookie_unquote(b):
    if len(b) < 2:
        return b
    if b[:1] != b'"' or b[-1:] != b'"':
        return b

    b = b[1:-1]

    i = 0
    n = len(b)
    rv = bytearray()
    _push = rv.extend

    while 0 <= i < n:
        o_match = _octal_re.search(b, i)
        q_match = _quote_re.search(b, i)
        if not o_match and not q_match:
            rv.extend(b[i:])
            break
        j = k = -1
        if o_match:
            j = o_match.start(0)
        if q_match:
            k = q_match.start(0)
        if q_match and (not o_match or k < j):
            _push(b[i:k])
            _push(b[k + 1:k + 2])
            i = k + 2
        else:
            _push(b[i:j])
            rv.append(int(b[j + 1:j + 4], 8))
            i = j + 4

    return bytes(rv)


def _cookie_parse_impl(b):
    """Lowlevel cookie parsing facility that operates on bytes."""
    i = 0
    n = len(b)

    while i < n:
        match = _cookie_re.search(b + b';', i)
        if not match:
            break

        key = match.group('key').strip()
        value = match.group('val')
        i = match.end(0)

        # Ignore parameters.  We have no interest in them.
        if key.lower() not in _cookie_params:
            yield _cookie_unquote(key), _cookie_unquote(value)


def _encode_idna(domain):
    # If we're given bytes, make sure they fit into ASCII
    if not isinstance(domain, text_type):
        domain.decode('ascii')
        return domain

    # Otherwise check if it's already ascii, then return
    try:
        return domain.encode('ascii')
    except UnicodeError:
        pass

    # Otherwise encode each part separately
    parts = domain.split('.')
    for idx, part in enumerate(parts):
        parts[idx] = part.encode('idna')
    return b'.'.join(parts)


def _decode_idna(domain):
    # If the input is a string try to encode it to ascii to
    # do the idna decoding.  if that fails because of an
    # unicode error, then we already have a decoded idna domain
    if isinstance(domain, text_type):
        try:
            domain = domain.encode('ascii')
        except UnicodeError:
            return domain

    # Decode each part separately.  If a part fails, try to
    # decode it with ascii and silently ignore errors.  This makes
    # most sense because the idna codec does not have error handling
    parts = domain.split(b'.')
    for idx, part in enumerate(parts):
        try:
            parts[idx] = part.decode('idna')
        except UnicodeError:
            parts[idx] = part.decode('ascii', 'ignore')

    return '.'.join(parts)


def _make_cookie_domain(domain):
    if domain is None:
        return None
    domain = _encode_idna(domain)
    if b':' in domain:
        domain = domain.split(b':', 1)[0]
    if b'.' in domain:
        return domain
    raise ValueError(
        'Setting \'domain\' for a cookie on a server running locally (ex: '
        'localhost) is not supported by complying browsers. You should '
        'have something like: \'127.0.0.1 localhost dev.localhost\' on '
        'your hosts file and then point your server to run on '
        '\'dev.localhost\' and also set \'domain\' for \'dev.localhost\''
    )
