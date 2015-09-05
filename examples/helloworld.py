from flagon import Flagon
app = Flagon()

@app.route('/')
def hello_world():
    print 'hello'
    return 'Hello World!'

if __name__ == '__main__':
    app.run()
