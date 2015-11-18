
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


# Dynamic Routes

# Request Data

# Response

# Blueprints

# Error Handle

# Sessions

# Testing

# Deployment
