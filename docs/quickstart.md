
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

# Request Data

# Response

# Blueprints

# Error Handle

# Sessions

# Testing

# Deployment
