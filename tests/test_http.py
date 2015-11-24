import pytest

from cocopot.http import parse_content_type, parse_auth, parse_date, http_date, html_quote, parse_range_header
from cocopot.exceptions import abort, HTTPException, MethodNotAllowed
import copy
import time
from datetime import datetime

def test_content_type():
    r = parse_content_type('text/plain')
    assert r == ('text/plain', {})
    r = parse_content_type('text/plain; chartset=utf-8')
    assert r == ('text/plain', {'chartset': 'utf-8'})

def test_http_date():
    t = time.time()
    assert http_date(t) == time.strftime("%a, %d %b %Y %H:%M:%S GMT", time.gmtime(t))

def test_auth():
    assert None == parse_auth(':')
    assert None == parse_auth('basic n:m')

def test_range_header():
    rv = list(parse_range_header('bytes=52'))
    assert rv == []

    rv = list(parse_range_header('bytes=52-', 1000))
    assert rv == [(52, 1000)]

    rv = list(parse_range_header('bytes=52a-', 1000))
    assert rv == []

    rv = list(parse_range_header('bytes=52-99', 1000))
    assert rv == [(52, 100)]

    rv = list(parse_range_header('bytes=52-99,-1000', 2000))
    assert rv == [(52, 100), (1000, 2000)]

    rv = list(parse_range_header('bytes = 1 - 100', 1000))
    assert rv == []

    rv = list(parse_range_header('AWesomes=0-999', 1000))
    assert rv == []

def test_html():
    assert '"&lt;&#039;&#13;&#10;&#9;&quot;\\&gt;"' == html_quote('<\'\r\n\t"\\>')

def test_exception():
    exc = HTTPException()
    assert exc.get_description() == 'Unknown http exception'
    assert exc.name == 'Unknown Error'
    assert exc.get_body() == 'Unknown http exception'
    s = repr(exc)
