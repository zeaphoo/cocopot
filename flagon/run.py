

def run_simple(hostname, port, application, **kwargs):
    from wsgiref.simple_server import make_server
    from wsgiref.simple_server import WSGIRequestHandler, WSGIServer
    import socket

    class FixedHandler(WSGIRequestHandler):
        def address_string(self):  # Prevent reverse DNS lookups please.
            return self.client_address[0]

        def log_request(*args, **kw):
            return WSGIRequestHandler.log_request(*args, **kw)

    srv = make_server(hostname, port, application, WSGIServer, FixedHandler)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        srv.server_close()
        raise
