try:
    import simplejson as json
except:
    import json
import sys
import hmac
import zlib
import time
import base64
from datetime import datetime

# 2011/01/01 in UTC
EPOCH = 1293840000

class BadPayload(Exception):
    def __init__(self, message, original_error=None):
        Exception.__init__(self, message)
        #: If available, the error that indicates why the payload
        #: was not valid.  This might be `None`.
        self.original_error = original_error

class SignatureExpired(Exception):
    def __init__(self, message, payload=None):
        Exception.__init__(self, message)
        self.payload = payload

def to_bytes(s, encoding='utf-8', errors='strict'):
    if isinstance(s, text_type):
        s = s.encode(encoding, errors)
    return s

def base64_encode(string):
    """base64 encodes a single bytestring (and is tolerant to getting
    called with a unicode string).
    The resulting bytestring is safe for putting into URLs.
    """
    string = to_bytes(string)
    return base64.urlsafe_b64encode(string).strip(b'=')


def base64_decode(string):
    """base64 decodes a single bytestring (and is tolerant to getting
    called with a unicode string).
    The result is also a bytestring.
    """
    string = to_bytes(string, encoding='ascii', errors='ignore')
    return base64.urlsafe_b64decode(string + b'=' * (-len(string) % 4))

def load_payload(payload):
    decompress = False
    if payload.startswith(b'.'):
        payload = payload[1:]
        decompress = True
    try:
        jsondata = base64_decode(payload)
    except Exception as e:
        raise BadPayload('Could not base64 decode the payload because of '
            'an exception', original_error=e)
    if decompress:
        try:
            jsondata = zlib.decompress(jsondata)
        except Exception as e:
            raise BadPayload('Could not zlib decompress the payload before '
                'decoding the payload', original_error=e)
    return json.loads(jsondata)

def dump_payload(data):
    json = json.dumps(data, separators=(',', ':'))
    is_compressed = False
    compressed = zlib.compress(json)
    if len(compressed) < (len(json) - 1):
        json = compressed
        is_compressed = True
    base64d = base64_encode(json)
    if is_compressed:
        base64d = b'.' + base64d
    return base64d

def gen_signature(value, key, salt):
    value = to_bytes(value)
    mac = hmac.new(key, msg=salt, digestmod=hashlib.sha1)
    key = mac.digest()
    mac = hmac.new(key, msg=value, digestmod=hashlib.sha1)
    sig = mac.digest()
    return base64_encode(sig)

def sign_payload(value, key, salt):
    sep = "."
    ts = int(time.time() - EPOCH)
    value = '%s%s%s'%(value, sep, ts)
    return value + sep + gen_signature(value)

def format_time(ts):
    return time.strftime("%Y-%m-%d %H:%M:%S UTC", ts)

def validate_payload(value, key, salt, max_age=None):
    parts = value.rsplit(".", 1)
    if len(parts) != 2:
        return False, None
    signature = parts[-1]
    value = parts[0]
    if gen_signature(value, key, salt) != signature:
        try:
            ts = int(value.rsplit(".", 1)[-1])
        except:
            return False, "timestamp not valid"
        if max_age is not None:
            age = int(time.time() - EPOCH) - ts
            if age > max_age:
                raise SignatureExpired(
                    'Signature age %s > %s seconds, Expired at %s' % (age, max_age, format_time(int(time.time())+EPOCH)),
                    payload=value)
        return False, "Signature %s wrong!"%(signature)
    return True, value
