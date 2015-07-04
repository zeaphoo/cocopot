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
