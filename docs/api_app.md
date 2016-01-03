#class Cocopot(import_name='')

The cocopot object implements a WSGI application and acts as the central
object.  Once it is created it will act as a central registry for
the view functions, the URL rules,  and more.

Usually you create a `Cocopot` instance in your main module or
in the `__init__.py` file of your package like this:

    from cocopot import Cocopot
    app = Cocopot()


##var **debug**



##var **log_format**



##var **blueprints**



##var **name**

The name of the application.  This is usually the import name
with the difference that it's guessed from the run file if the
import name is main.  This name is used as a display name when
Cocopot needs the name of the application.  It can be set and overridden
to change the value.

##var **config**



##var **before_request_funcs**



##var **view_functions**



##var **error_handler_spec**



##var **teardown_request_funcs**



##var **router**



##var **logger**



##var **import_name**



##var **after_request_funcs**



##def **create_logger**()

Creates a logger for the given application.  This logger works
similar to a regular Python logger but changes the effective logging
level based on the application's debug flag.  Furthermore this
function also removes all attached handlers in case there was a
logger with the log name before.

##def **before_request**(f)

Registers a function to run before each request.

##def **wsgi_app**(environ, start_response)

The actual WSGI application.  This is not implemented in
`__call__` so that middlewares can be applied without losing a
reference to the class.  So instead of doing this:

    app = MyMiddleware(app)

It's a better idea to do this instead:

    app.wsgi_app = MyMiddleware(app.wsgi_app)

Then you still have the original application object around and
can continue to call methods on it.

Args:

  * environ: a WSGI environment
  * start_response: a callable accepting a status code,
                       a list of headers and an optional
                       exception context to start the response

##def **handle_http_exception**(e)

Handles an HTTP exception.  By default this will invoke the
registered error handlers and fall back to returning the
exception as response.

##def **handle_user_exception**(e)

This method is called whenever an exception occurs that should be
handled.  A special case are `~cocopot.exception.HTTPException`\s which are forwarded by
this function to the `handle_http_exception` method.  This
function will either return a response value or reraise the
exception with the same traceback.

##def **process_response**(response)

Can be overridden in order to modify the response object
before it's sent to the WSGI server.  By default this will
call all the `after_request` decorated functions.

Args:

  * response: a `Response` object.

Returns:

  * a new response object or the same, has to be an
         instance of `Response`.

##def **run**(host=None, port=None, debug=True, **options)

Runs the application on a local development server.
Args:

  * host: the hostname to listen on. Set this to '0.0.0.0' to
             have the server available externally as well. Defaults to
             '127.0.0.1'.
  * port: the port of the webserver. Defaults to 5000 or the
             port defined in the SERVER_NAME` config variable if
             present.

##def **do_teardown_request**(exc=None)

Called after the actual request dispatching and will
call every as `teardown_request` decorated function.  This is
not actually called by the `Cocopot` object itself but is always
triggered when the request context is popped.  That way we have a
tighter control over certain resources under testing environments.

##def **log_exception**(exc_info)

Logs an exception.  This is called by `handle_exception`
if debugging is disabled and right before the handler is called.
The default implementation logs the exception as error on the
`logger`.

##def **errorhandler**(code_or_exception)

A decorator that is used to register a function give a given
error code.  Example:

    @app.errorhandler(404)
    def page_not_found(error):
        return 'This page does not exist', 404

You can also register handlers for arbitrary exceptions:

    @app.errorhandler(DatabaseError)
    def special_exception_handler(error):
        return 'Database connection failed', 500

You can also register a function as error handler without using
the `errorhandler` decorator.  The following example is
equivalent to the one above:

    def page_not_found(error):
        return 'This page does not exist', 404
    app.error_handler_spec[None][404] = page_not_found

Setting error handlers via assignments to `error_handler_spec`
however is discouraged as it requires fiddling with nested dictionaries
and the special case for arbitrary exception types.

The first `None` refers to the active blueprint.  If the error
handler should be application wide `None` shall be used.

##def **full_dispatch_request**()

Dispatches the request and on top of that performs request
pre and postprocessing as well as HTTP exception catching and
error handling.

##def **register_error_handler**(code_or_exception, f)

Alternative error attach function to the `errorhandler`
decorator that is more straightforward to use for non decorator
usage.

##def **endpoint**(endpoint)

A decorator to register a function as an endpoint.
Example:

    @app.endpoint('example.endpoint')
    def example():
        return "example"
Args:
    endpoint: the name of the endpoint

##def **register_blueprint**(blueprint, **options)

Registers a blueprint on the application.
        

##def **route**(rule, **options)

A decorator that is used to register a view function for a
given URL rule.  This does the same thing as `add_url_rule`
but is intended for decorator usage:

    @app.route('/')
    def index():
        return 'Hello World'

For more information refer to `url-route-registrations`.

Args:

  * rule: the URL rule as string
  * endpoint: the endpoint for the registered URL rule.  Cocopot
                 itself assumes the name of the view function as
                 endpoint

##def **handle_exception**(e)

Default exception handling that kicks in when an exception
occurs that is not caught.  In debug mode the exception will
be re-raised immediately, otherwise it is logged and the handler
for a 500 internal server error is used.  If no such handler
exists, a default 500 internal server error message is displayed.

##def **preprocess_request**()

Called before the actual request dispatching and will
call every as `before_request` decorated function.
If any of these function returns a value it's handled as
if it was the return value from the view and further
request handling is stopped.

##def **add_url_rule**(rule, endpoint=None, view_func=None, methods=None, **options)

Connects a URL rule.  Works exactly like the `route`
decorator.  If a view_func is provided it will be registered with the
endpoint.

Basically this example:

    @app.route('/')
    def index():
        pass

Is equivalent to the following:

    def index():
        pass
    app.add_url_rule('/', 'index', index)

If the view_func is not provided you will need to connect the endpoint
to a view function like so:

    app.view_functions['index'] = index

Internally `route` invokes `add_url_rule` so if you want
to customize the behavior via subclassing you only need to change
this method.

For more information refer to `url-route-registrations`.

Args:

  * rule : the URL rule as string
  * endpoint : the endpoint for the registered URL rule.
            Cocopot itself assumes the name of the view function as endpoint
  * view_func: the function to call when serving a request to the
            provided endpoint
  * options: methods is a list of methods this rule should be limited
            to (`GET`, `POST` etc.).

##def **after_request**(f)

Register a function to be run after each request.  Your function
must take one parameter, a `Response` object and return
a new response object.

##def **teardown_request**(f)

Register a function to be run at the end of each request,
regardless of whether there was an exception or not.  These functions
are executed when the request context is popped, even if not an
actual request was performed.

Generally teardown functions must take every necessary step to avoid
that they will fail.  If they do execute code that might fail they
will have to surround the execution of these code by try/except
statements and log occurring errors.

When a teardown function was called because of a exception it will
be passed an error object.