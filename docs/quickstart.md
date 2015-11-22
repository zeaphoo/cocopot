
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
In Flagon this information is provided by the global request object. If you have some experience with Python you might be wondering how that object can be global and how Flagon manages to still be threadsafe. The answer is request context locals.

First of all you have to import it:

```python
from flagon import request
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

# Redirects and Errors

To redirect a user to another endpoint, use the redirect() function; to abort a request early with an error code, use the abort() function:

from flagon import abort, redirect

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

# Blueprints

# Error Handle

# Sessions

# Testing

# Deployment
