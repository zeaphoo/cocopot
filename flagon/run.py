

def run_simple(hostname, port, application, use_reloader=False,
               use_debugger=False):
    from wsgiref.simple_server import make_server
    from wsgiref.simple_server import WSGIRequestHandler, WSGIServer
    pass
