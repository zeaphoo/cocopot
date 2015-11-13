[![Build Status](https://travis-ci.org/zeaphoo/flagon.svg)](https://travis-ci.org/zeaphoo/flagon)
[![Coverage Status](https://coveralls.io/repos/zeaphoo/flagon/badge.svg?branch=master&service=github)](https://coveralls.io/github/zeaphoo/flagon?branch=master)

# Flagon: Python Web Framework

Flagon is a fast, simple and lightweight WSGI micro web-framework for Python. It provide similar interface with Flask. It's intended for focus on mobile service development, which not handle html rendering


* **Routing:** Requests to function-call mapping with support for clean and  dynamic URLs.
* **No built-in Templates**
* **Utilities:** Convenient access to form data, file uploads, cookies, headers and other HTTP-related metadata.


## Example: "Hello World" in a flagon

```python
from flagon import Flagon
app = Flagon()

@app.route("/hello")
def hello():
    return "Hello World!"

if __name__ == "__main__":
    app.run()

```


Run this script or paste it into a Python console, then point your browser to `<http://localhost:8080/hello>`. That's it.


## Download and Install


Install the latest stable release with ``pip install flagon``, ``easy_install -U flagon``. There are no hard dependencies other than the Python standard library. Flagon runs with **Python 2.6+ and 3.3+**. 0.1 will be released soon.


## License

Code and documentation are available according to the MIT License (see LICENSE__).
