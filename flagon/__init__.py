# -*- coding: utf-8 -*-
"""
    flagon
    ~~~~~

    A microframework based on Werkzeug.  It's extensively documented
    and follows best practice patterns.

    :copyright: (c) 2011 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""

__version__ = '0.10.1'

# utilities we import from Werkzeug and Jinja2 that are unused
# in the module but are exported as public interface.
from .exceptions import abort
from .utils import redirect

from .app import Flagon, Request, Response
from .config import Config
from .helpers import url_for, flash, send_file, send_from_directory, \
    get_flashed_messages, make_response, safe_join, \
    stream_with_context
from .globals import current_app, g, request, session, _request_ctx_stack, \
     _app_ctx_stack
from .ctx import has_request_context, has_app_context, \
     after_this_request, copy_current_request_context
from .blueprints import Blueprint


# We're not exposing the actual json module but a convenient wrapper around
# it.
from . import json

# This was the only thing that flagon used to export at one point and it had
# a more generic name.
jsonify = json.jsonify

# backwards compat, goes away in 1.0
from .sessions import SecureCookieSession as Session
json_available = True
