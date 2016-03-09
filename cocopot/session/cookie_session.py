
from .base import BaseSession
import hashlib
from .utils import sign_payload, validate_payload, load_payload, dump_payload
from .globals import session_config


class SecureCookieSession(BaseSession):
    salt = 'cookie-session'

    def __init__(self):
        pass

    def decode_session(self, data):
        validated, ret = validate_payload(data)
        if validated:
            return load_payload(ret)
        return None

    def encode_session(self):
        s = dump_payload(data)
        return sign_payload(s, session_config.get('secret_key'), salt)

    def open(self, request):
        value = request.get_cookie('session') or ''
        data = self.decode_session(value) or {}
        self.update(data)


    def save(self, response):
        data = self.encode_session(dict(self))
        response.set_cookie('session', data)
