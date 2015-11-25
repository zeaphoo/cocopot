
# Request Routing

In the last chapter we built a very simple web application with only a single route. Here is the routing part of the "Hello World" example again:

```python
    @app.route('/hello')
    def hello():
        return "Hello World!"
```

The `route` decorator links an URL path to a callback function, and adds a new route to the Application `app`. An application with just one route is kind of boring, though. Let's add some more:

```python
    @app.route('/')
    @app.route('/hello/<name>')
    def greet(name='Stranger'):
        return 'Hello %s, how are you?'%(name)
```

This example demonstrates two things: You can bind more than one route to a single callback, and you can add wildcards to URLs and access them via keyword arguments.


# Variable Rules

To add variable parts to a URL you can mark these special sections as <variable_name>. Such a part is then passed as a keyword argument to your function. Optionally a converter can be used by specifying a rule with <converter:variable_name>. Here are some nice examples:

```python
@app.route('/user/<username>')
def show_user_profile(username):
    # show the user profile for that user
    return 'User %s' % username

@app.route('/post/<int:post_id>')
def show_post(post_id):
    # show the post with the given id, the id is an integer
    return 'Post %d' % post_id
```

The following converters exist:

| converter | behavior |
|-----------|----------|
| int | accepts integers |
| float | like int but for floating point values |
| path | like the default but also accepts slashes |

# HTTP Methods

HTTP (the protocol web applications are speaking) knows different methods for accessing URLs. By default, a route only answers to GET requests, but that can be changed by providing the methods argument to the route() decorator. Here are some examples:

```python
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        do_the_login()
    else:
        show_the_login_form()
```

If GET is present, HEAD will be added automatically for you. You don’t have to deal with that. It will also make sure that HEAD requests are handled as the HTTP RFC (the document describing the HTTP protocol) demands, so you can completely ignore that part of the HTTP specification.

Here is a quick introduction to HTTP methods and why they matter:

The HTTP method (also often called “the verb”) tells the server what the clients wants to do with the requested page. The following methods are very common:

GET
The browser tells the server to just get the information stored on that page and send it. This is probably the most common method.

HEAD
The browser tells the server to get the information, but it is only interested in the headers, not the content of the page. An application is supposed to handle that as if a GET request was received but to not deliver the actual content.

POST
The browser tells the server that it wants to post some new information to that URL and that the server must ensure the data is stored and only stored once. This is how HTML forms usually transmit data to the server.

PUT
Similar to POST but the server might trigger the store procedure multiple times by overwriting the old values more than once. Now you might be asking why this is useful, but there are some good reasons to do it this way. Consider that the connection is lost during transmission: in this situation a system between the browser and the server might receive the request safely a second time without breaking things. With POST that would not be possible because it must only be triggered once.

DELETE
Remove the information at the given location.

OPTIONS
Provides a quick way for a client to figure out which methods are supported by this URL.

# Request Data
In Cocopot this information is provided by the global request object. If you have some experience with Python you might be wondering how that object can be global and how Cocopot manages to still be threadsafe. The answer is request context locals.

First of all you have to import it:

```python
from cocopot import request
```

The current request method is available by using the method attribute. To access form data (data transmitted in a POST or PUT request) you can use the form attribute. Here is a full example of the two attributes mentioned above:

```python
@app.route('/login', methods=['POST', 'GET'])
def login():
    error = None
    if request.method == 'POST':
        if valid_login(request.form['username'],
                       request.form['password']):
            return log_the_user_in(request.form['username'])
        else:
            error = 'Invalid username/password'
    # the code below is executed if the request method
    # was GET or the credentials were invalid
    return 'error' if error else 'ok'
```

To access parameters submitted in the URL (?key=value) you can use the args attribute:

```python
searchword = request.args.get('key', '')
```

# Redirects and Aborts

To redirect a user to another endpoint, use the redirect() function; to abort a request early with an error code, use the abort() function:

from cocopot import abort, redirect

```python
@app.route('/')
def index():
    return redirect('/login')

@app.route('/login')
def login():
    abort(401)
    this_is_never_executed()
```

This is a rather pointless example because a user will be redirected from the index to a page they cannot access (401 means access denied) but it shows how that works.


# Response

The return value from a view function is automatically converted into a response object for you. If the return value is a string it’s converted into a response object with the string as response body, an 200 OK error code and a text/html mimetype. The logic that Cocopot applies to converting return values into response objects is as follows:

* If a response object of the correct type is returned it’s directly returned from the view.
* If it’s a string, a response object is created with that data and the default parameters.
* If a tuple is returned the items in the tuple can provide extra information. Such tuples have to be in the form (response, status, headers) where at least one item has to be in the tuple. The status value will override the status code and headers can be a list or dictionary of additional header values.
* If none of that works, Cocopot will assume the return value is a valid WSGI application and convert that into a response object.
* If you want to get hold of the resulting response object inside the view you can use the make_response() function.

Imagine you have a view like this:

```python
@app.route('/hello')
def hello():
    return 'ok', 200
```

You just need to wrap the return expression with make_response() and get the response object to modify it, then return it:

```python
@app.route('/hello')
def hello():
    resp = make_response('ok', 200)
    resp.headers['X-Something'] = 'A value'
    return resp
```

# Blueprints

A Blueprint object works similarly to a Cocopot application object, but it is not actually an application. Rather it is a blueprint of how to construct or extend an application.

## Why Blueprints?
Blueprints are intended for these cases:

* Factor an application into a set of blueprints. This is ideal for larger applications; a project could instantiate an application object, initialize several extensions, and register a collection of blueprints.
* Register a blueprint on an application at a URL prefix. Parameters in the URL prefix become common view arguments (with defaults) across all view functions in the blueprint.
* Register a blueprint multiple times on an application with different URL rules.
Provide template filters, static files, templates, and other utilities through blueprints. A blueprint does not have to implement applications or view functions.

A blueprint is not a pluggable app because it is not actually an application – it’s a set of operations which can be registered on an application, even multiple times. Why not have multiple application objects? You can do that, but your applications will be managed at the WSGI layer.


## Write Blueprint

This is what a very basic blueprint looks like. In this case we want to implement a blueprint that does simple return:

```python
from cocopot import Blueprint, abort

bp = Blueprint('blueprint1')

@bp.route('/show')
def show():
    return 'ok'
```

When you bind a function with the help of the `@bp.route` decorator the blueprint will record the intention of registering the function `show` on the application when it’s later registered. Additionally it will prefix the endpoint of the function with the name of the blueprint which was given to the Blueprint constructor.

## Registering Blueprints

So how do you register that blueprint? Like this:

```python
from cocopot import Cocopot
from yourapplication.blueprint1 import bp

app = Cocopot()
app.register_blueprint(bp)
```

Blueprints however can also be mounted at different locations:

```python
app.register_blueprint(bp, url_prefix='/blueprint1')
```

# Request Hooks



# Error Handle

By default all the error and exception will be wrapped as a default response,  If you want to customize the error returns, you can use the errorhandler() decorator:

```python
import json

@app.errorhandler(401)
def user_not_authed(error):
    return json.dumps({'status':'error', 'error':'login_required'}), 401

@app.errorhandler(Exception)
def server_exception(error):
    return  'server exception, we will fix it soon.', 500
```

The errorhandler() decorator can also be used in Blueprint, the only limitation is Blueprint can't handle 500 error, since it should be handled by the Application.

# Sessions

# Testing

# Deployment
