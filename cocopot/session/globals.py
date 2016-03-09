
from .base import SessionConfig

session_config = SessionConfig()

from cocopot.local import LocalProxy

def create_session(*args):
    return None

def _lookup_session_object():
    from cocopot import request
    session = getattr(request, 'session')
    if not session:
        setattr(request, 'session', create_session(request))
    return getattr(request, 'session')


session = LocalProxy(_lookup_session_object)
