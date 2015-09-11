

def run_simple(hostname, port, app, **kwargs):
    from wsgiref.simple_server import make_server
    from wsgiref.simple_server import WSGIRequestHandler, WSGIServer
    import socket

    class FixedHandler(WSGIRequestHandler):
        def address_string(self):  # Prevent reverse DNS lookups please.
            return self.client_address[0]

        def log_request(*args, **kw):
            return WSGIRequestHandler.log_request(*args, **kw)

    srv = make_server(hostname, port, app, WSGIServer, FixedHandler)
    try:
        app.logger.info(' * Running on %s://%s:%d/ %s'%('http', hostname, port, '(Press CTRL+C to quit)'))
        srv.serve_forever()
    except KeyboardInterrupt:
        srv.server_close()
        raise
