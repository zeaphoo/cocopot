import os
import re
from ._compat import text_type, PY2, to_unicode, to_native, BytesIO
import cgi
if PY2:
    from urlparse import urljoin, SplitResult as UrlSplitResult
    from urllib import urlencode, quote as urlquote, unquote as urlunquote
else:
    from urllib.parse import urljoin, SplitResult as UrlSplitResult
    from urllib.parse import urlencode, quote as urlquote, unquote as urlunquote
    urlunquote = functools.partial(urlunquote, encoding='latin1')
from tempfile import TemporaryFile

MEMFILE_MAX = 4*1024*1024

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

def get_host(environ):
    """Return the real host for the given WSGI environment.  This first checks
    the `X-Forwarded-Host` header, then the normal `Host` header, and finally
    the `SERVER_NAME` environment variable (using the first one it finds).

    Optionally it verifies that the host is in a list of trusted hosts.
    If the host is not in there it will raise a
    :exc:`~flagon.exceptions.SecurityError`.

    :param environ: the WSGI environment to get the host of.
    :param trusted_hosts: a list of trusted hosts, see :func:`host_is_trusted`
                          for more information.
    """
    if 'HTTP_X_FORWARDED_HOST' in environ:
        rv = environ['HTTP_X_FORWARDED_HOST'].split(',', 1)[0].strip()
    elif 'HTTP_HOST' in environ:
        rv = environ['HTTP_HOST']
    else:
        rv = environ['SERVER_NAME']
        if (environ['wsgi.url_scheme'], environ['SERVER_PORT']) not \
           in (('https', '443'), ('http', '80')):
            rv += ':' + environ['SERVER_PORT']
    return rv


def get_content_length(environ):
    """Returns the content length from the WSGI environment as
    integer.  If it's not available `None` is returned.

    .. versionadded:: 0.9

    :param environ: the WSGI environ to fetch the content length from.
    """
    content_length = environ.get('CONTENT_LENGTH')
    if content_length is not None:
        try:
            return max(0, int(content_length))
        except (ValueError, TypeError):
            pass

def get_current_url(environ, root_only=False, strip_querystring=False, host_only=False):
    """A handy helper function that recreates the full URL as IRI for the
    current request or parts of it.  Here an example:

    >>> from flagon.test import create_environ
    >>> env = create_environ("/?param=foo", "http://localhost/script")
    >>> get_current_url(env)
    'http://localhost/script/?param=foo'
    >>> get_current_url(env, root_only=True)
    'http://localhost/script/'
    >>> get_current_url(env, host_only=True)
    'http://localhost/'
    >>> get_current_url(env, strip_querystring=True)
    'http://localhost/script/'

    :param environ: the WSGI environment to get the current URL from.
    :param root_only: set `True` if you only want the root URL.
    :param strip_querystring: set to `True` if you don't want the querystring.
    :param host_only: set to `True` if the host URL should be returned.
    :param trusted_hosts: a list of trusted hosts, see :func:`host_is_trusted`
                          for more information.
    """
    tmp = [environ['wsgi.url_scheme'], '://', get_host(environ)]
    cat = tmp.append
    if host_only:
        return uri_to_iri(''.join(tmp) + '/')
    cat(url_quote(wsgi_get_bytes(environ.get('SCRIPT_NAME', ''))).rstrip('/'))
    cat('/')
    if not root_only:
        cat(url_quote(wsgi_get_bytes(environ.get('PATH_INFO', '')).lstrip(b'/')))
        if not strip_querystring:
            qs = get_query_string(environ)
            if qs:
                cat('?' + qs)
    return uri_to_iri(''.join(tmp))


def get_input_stream(environ):
    try:
        read_func = environ['wsgi.input'].read
    except KeyError:
        environ['wsgi.input'] = BytesIO()
        return environ['wsgi.input']
    body_iter = self._iter_chunked if self.chunked else self._iter_body
    body, body_size, is_temp_file = BytesIO(), 0, False
    for part in body_iter(read_func, MEMFILE_MAX):
        body.write(part)
        body_size += len(part)
        if not is_temp_file and body_size > MEMFILE_MAX:
            body, tmp = TemporaryFile(mode='w+b'), body
            body.write(tmp.getvalue())
            del tmp
            is_temp_file = True
    environ['wsgi.input'] = body
    body.seek(0)
    return body


def parse_form_data(body, environ, content_type='application/x-www-form-urlencoded', charset='utf-8',
                    errors='replace', max_content_length=None, silent=True):

    post = FormsDict()
    # We default to application/x-www-form-urlencoded for everything that
    # is not multipart and take the fast path (also: 3.1 workaround)
    if not content_type.startswith('multipart/'):
        pairs = urldecode(to_native(body, 'latin1'))
        for key, value in pairs:
            post[key] = value
        return post

    safe_env = {'QUERY_STRING': ''}  # Build a safe environment for cgi
    for key in ('REQUEST_METHOD', 'CONTENT_TYPE', 'CONTENT_LENGTH'):
        if key in environ: safe_env[key] = environ[key]
    args = dict(fp=body, environ=safe_env, keep_blank_values=True)
    if not PY2:
        args['encoding'] = 'utf8'
    data = cgi.FieldStorage(**args)
    environ['_cgi.FieldStorage'] = data  #http://bugs.python.org/issue18394
    data = data.list or []
    for item in data:
        if item.filename:
            post[item.name] = FileUpload(item.file, item.name,
                                         item.filename, item.headers)
        else:
            post[item.name] = item.value
    return post
