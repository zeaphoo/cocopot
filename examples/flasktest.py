
from flask import Flask, request, g, abort

app = Flask(__name__)

@app.before_request
def before_request():
    abort(400)

@app.after_request
def after_request(response):
    print 'after_request', response
    return response


@app.teardown_request
def teardown_request(exc):
    print 'teardown_request', exc

@app.route('/')
def hello():
    return 'hello'


app.run(port=3000)
