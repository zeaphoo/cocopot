from flagon import Flagon, request
app = Flagon('example1')

@app.before_request
def before_request():
    if 'foo' not in request.view_args:
        request.view_args.update(foo='123')

@app.route('/')
@app.route('/<foo>/bar')
def hello_world(foo):
    print 'hello', foo
    return 'Hello World!'

if __name__ == '__main__':
    app.run()
