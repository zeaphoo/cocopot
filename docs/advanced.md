# Request Context

## Object Proxies

Some of the objects like `request, g` provided by Cocopot are proxies to other objects. The reason behind this is that these proxies are shared between threads and they have to dispatch to the actual object bound to a thread behind the scenes as necessary.

```python
from cocopot import request, g
app = Cocopot()

@app.before_request
def before_request():
    g.foo = 'ok'

@app.route('/hello')
def hello_world():
    return g.foo
```

## Request Hooks and Processing

Cocopot application provides `before_request, after_request, teardown_request` callbacks in request processing.

The before_request callbacks does not need any parameters, in this callback, request context has been created, so request and g object is available. It is often check session, create necessary db connection and etc.

```Python
@app.before_request
def before_request():
    g.db = DBConnection() #
```



# Errors

What happens if an error occurs during request processing? The behavior is quite simple:

Before each request, before_request() functions are executed. If one of these functions return a response, the other functions are no longer called. In any case however the return value is treated as a replacement for the view’s return value.

If the before_request() functions did not return a response, the regular request handling kicks in and the view function that was matched has the chance to return a response.

The return value of the view is then converted into an actual response object and handed over to the after_request() functions which have the chance to replace it or modify it in place.

At the end of the request the teardown_request() functions are executed. This always happens, even in case of an unhandled exception down the road or if a before-request handler was not executed yet or at all (for example in test environments sometimes you might want to not execute before-request callbacks).


Now what happens on errors? If an exception is not caught, the 500 internal server handler is called.
