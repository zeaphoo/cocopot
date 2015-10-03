# -*- coding: utf-8 -*-
from flagon import Flagon
app = Flagon('hello')

@app.route('/')
def hello_world():
    print 'hello'
    return 'Hello World!'

@app.route(u'/地球')
def hello_world2():
    return 'hello'

if __name__ == '__main__':
    app.run()
