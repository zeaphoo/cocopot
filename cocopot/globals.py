# -*- coding: utf-8 -*-
"""
    Defines all the global objects that are proxies to the current
    active context.
"""

from functools import partial
from .local import LocalStack, LocalProxy
from .utils import ConfigDict

def _lookup_req_object(name):
    top = _request_ctx_stack.top
    if top is None:
        raise RuntimeError('working outside of request context')
    return getattr(top, name)

# context locals
_request_ctx_stack = LocalStack()
request = LocalProxy(partial(_lookup_req_object, 'request'))
current_app = LocalProxy(partial(_lookup_req_object, 'app'))
g = LocalProxy(partial(_lookup_req_object, 'g'))
config = ConfigDict()
