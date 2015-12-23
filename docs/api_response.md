#Module cocopot.response


##var **HTTP_STATUS_CODES**



##var **PY2**



##var **integer_types**



##var **string_types**



##def **jsonify**(*args, **kwargs)

Creates a `Response` with the JSON representation of
the given arguments with an`application/json` mimetype.  The
arguments to this function are the same as to the `dict`
constructor.
Example usage:

    from cocopot import jsonify
    @app.route('/_get_current_user')
    def get_current_user():
        return jsonify(username=g.user.username,
                       email=g.user.email,
                       id=g.user.id)

This will send a JSON response like this to the browser:

    {
        "username": "admin",
        "email": "admin@localhost",
        "id": 42
    }

##def **make_response**(*args)



##def **redirect**(location, code=302)

Returns a response object (a WSGI application) that, if called,
redirects the client to the target location.  Supported codes are 301,
302, 303, 305, and 307.
Args:

  * location: the location the response should redirect to.
  * code: the redirect status code. defaults to 302.
##class Response(body='', status=None, headers=None, **more_headers)

Storage class for a response body as well as headers and cookies.
This class does support dict-like case-insensitive item-access to
headers, but is NOT a dict. Most notably, iterating over a response
yields parts of the body and not the headers.

Args:

  * body: The response body as one of the supported types.
  * status: Either an HTTP status code (e.g. 200) or a status line
               including the reason phrase (e.g. '200 OK').
  * headers: A dictionary or a list of name-value pairs.

Additional keyword arguments are added to the list of headers.
Underscores in the header name are replaced with dashes.


###var **status**



###var **content_length**



###var **default_content_type**



###var **default_status**



###var **bad_headers**



###var **expires**



###var **content_type**



###var **status**



###var **body**



###var **headerlist**

WSGI conform list of (header, value) tuples. 

###var **status_code**

The HTTP status code as an integer (e.g. 404).

###var **charset**

Return the charset specified in the content-type header (default: utf8). 

###var **status_line**

The HTTP status line as a string (e.g. ``404 Not Found``).

###var **headers**

An instance of `HeaderDict`, a case-insensitive dict-like
view on the response headers. 

###def **set_header**(name, value)

Create a new response header, replacing any previously defined
headers with the same name. 

###def **set_cookie**(name, value, secret=None, **options)

Create a new cookie or replace an old one. If the `secret` parameter is
set, create a `Signed Cookie` (described below).

Args:

  * name: the name of the cookie.
  * value: the value of the cookie.
  * secret: a signature key required for signed cookies.

Additionally, this method accepts all RFC 2109 attributes that are
supported by `cookie.Morsel`, including:

  * max_age: maximum age in seconds. (default: None)
  * expires: a datetime object or UNIX timestamp. (default: None)
  * domain: the domain that is allowed to read the cookie. (default: current domain)
  * path: limits the cookie to a given path (default: current path)
  * secure: limit the cookie to HTTPS connections (default: off).
  * httponly: prevents client-side javascript to read this cookie (default: off).

If neither `expires` nor `max_age` is set (default), the cookie will
expire at the end of the browser session (as soon as the browser
window is closed).
Signed cookies may store any pickle-able object and are
cryptographically signed to prevent manipulation. Keep in mind that
cookies are limited to 4kb in most browsers.
Warning: Signed cookies are not encrypted (the client can still see
the content) and not copy-protected (the client can restore an old
cookie). The main intention is to make pickling and unpickling
save, not to store secret information at client side.

###def **init_with**(rv, status)



###def **add_header**(name, value)

Add an additional response header, not removing duplicates. 

###def **delete_cookie**(key, **kwargs)

Delete a cookie. Be sure to use the same `domain` and `path`
settings as used to create the cookie. 

###def **get_header**(name, default=None)

Return the value of a previously defined header. If there is no
header with that name, return a default value. 

###def **close**()



###def **copy**(cls=None)

Returns a copy of self. 

###def **iter_headers**()

Yield (header, value) tuples, skipping headers that are not
allowed with the current response status code. 
