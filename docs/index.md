

# write your first cocopot app

Let's start with a very basic "Hello World" example:

```python
from cocopot import Cocopot
app = Cocopot()

@app.route("/")
def hello():
    return "Hello World!"

if __name__ == "__main__":
    app.run(host='localhost', port=8080)

```

This is it. Run this script, visit http://localhost:8080/hello and you will see "Hello World!" in your browser.
