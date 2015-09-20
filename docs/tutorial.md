

# write your first flagon app

```python
from flagon import Flagon
app = Flagon()

@app.route("/")
def hello():
    return "Hello World!"

if __name__ == "__main__":
    app.run()

```
