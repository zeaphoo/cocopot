import pytest

from flagon.http import parse_content_type, parse_auth, parse_date, http_date
import copy

def test_content_type():
    r = parse_content_type('text/plain')
    assert r == ('text/plain', {})
    r = parse_content_type('text/plain; chartset=utf-8')
    assert r == ('text/plain', {'chartset': 'utf-8'})
