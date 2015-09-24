from flagon import Flagon, request
app = Flagon('example1')

@app.before_request
def before_request():
    if request.endpoint == 'hello_world':
        if 'foo' not in request.view_args:
            request.view_args.update(foo='123')
    if request.endpoint == 'hello_world2':
        if 'foo2' in request.view_args:
            request.view_args.pop('foo2')

@app.route('/')
@app.route('/<foo>/bar')
def hello_world(foo):
    print 'hello', foo
    return 'Hello World!'

@app.route('/')
@app.route('/<foo2>/noarg')
def hello_world2():
    return 'Hello World!'

if __name__ == '__main__':
    app.run()
