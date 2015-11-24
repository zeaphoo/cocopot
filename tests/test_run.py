import pytest

from cocopot import Cocopot, Blueprint, request, g, abort
from cocopot._compat import to_bytes
import copy
import traceback
import sys
import time
import socket
import random
import os
from subprocess import Popen, PIPE
import signal
try:
    from urllib.request import urlopen
except:
    from urllib2 import urlopen

serverscript = os.path.join(os.path.dirname(__file__), 'servertest.py')

def ping(server, port):
    ''' Check if a server accepts connections on a specific TCP port '''
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.connect((server, port))
        return True
    except socket.error:
        return False
    finally:
        s.close()

def fetch(port, url):
    try:
        return urlopen('http://127.0.0.1:%d/%s' % (port, url)).read()
    except Exception as e:
        return repr(e)

def start_server(port):
    # Start servertest.py in a subprocess
    cmd = [sys.executable, serverscript, '127.0.0.1', str(port)]
    cmd += sys.argv[1:] # pass cmdline arguments to subprocesses
    p = Popen(cmd, stdout=PIPE, stderr=PIPE)
    # Wait for the socket to accept connections
    for i in range(30):
        time.sleep(0.1)
        # Accepts connections?
        if ping('127.0.0.1', port): return ('ok', p)
        # Server died for some reason...
        rv = p.poll()
        if rv != None: break
    rv = p.poll()
    if rv is None:
        raise AssertionError("Server took too long to start up.")
    if rv is 3: # Port in use
        return ('port in use', None)
    raise AssertionError("Server exited with error code %d" % rv)

def test_run():
    p = None
    for port in range(18800, 18900):
        r, p = start_server(port)
        if r == 'ok' and p:
            break
    assert to_bytes('ok') == fetch(port, 'test')
    os.kill(p.pid, signal.SIGTERM)
    while p.poll() == None:
        os.kill(p.pid, signal.SIGTERM)
        time.sleep(1)
