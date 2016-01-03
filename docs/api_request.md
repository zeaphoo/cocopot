#class Request(environ, populate_request=True)




##var **view_args**



##var **endpoint**



##var **charset**



##var **encoding_errors**



##var **remote_route**



##var **is_secure**



##var **is_xhr**



##var **blueprint**

The name of the current blueprint

##var **mimetype**

Like `content_type` but without parameters (eg, without
charset, type etc.).  For example if the content
type is ``text/html; charset=utf-8`` the mimetype would be
``'text/html'``.

##var **remote_addr**

The remote address of the client.

##var **is_xhr**

True if the request was triggered via a JavaScript XMLHttpRequest.
This only works with libraries that support the `X-Requested-With`
header and set it to "XMLHttpRequest".  Libraries that do that are
prototype, jQuery and Mochikit and probably some more.

##var **script_name**

The initial portion of the URL's `path` that was removed by a higher
level (server or routing middleware) before the application was
called. This script path is returned with leading and tailing
slashes. 

##var **json**

If the mimetype is `application/json` this will contain the
parsed JSON data.  Otherwise this will be `None`.

The `get_json` method should be used instead.

##var **environ**



##var **full_path**

Requested path as unicode, including the query string.

##var **content_type**



##var **is_secure**

`True` if the request is secure.

##var **query_string**



##var **url_charset**

The charset that is assumed for URLs.  Defaults to the value
of `charset`.

##var **data**



##var **method**



##var **mimetype_params**

The mimetype parameters as dict.  For example if the content
type is ``text/html; charset=utf-8`` the params would be
``{'charset': 'utf-8'}``.

##var **input_stream**



##def **get_input_stream**()



##def **get_content_length**()

Returns the content length from the WSGI environment as
integer.  If it's not available `None` is returned.

##def **iter_chunked**(read, bufsize)



##def **get_data**(cache=True, as_text=False)

This reads the buffered incoming data from the client into one
bytestring.  By default this is cached but that behavior can be
changed by setting `cache` to `False`.

Usually it's a bad idea to call this method without checking the
content length first as a client could send dozens of megabytes or more
to cause memory problems on the server.

If `as_text` is set to `True` the return value will be a decoded
unicode string.

##def **iter_body**(read, bufsize)



##def **get_cookie**(key)

Return the content of a cookie. 

##def **parse_form_data**()



##def **get_host**()

Return the real host for the given WSGI environment.  This first checks
the `X-Forwarded-Host` header, then the normal `Host` header, and finally
the `SERVER_NAME` environment variable (using the first one it finds).

##def **close**()

Closes associated resources of this request object.  This
closes all file handles explicitly.  You can also use the request
object in a with statement with will automatically close it.

##def **get_current_url**(root_only=False, strip_querystring=False, host_only=False)

A handy helper function that recreates the full URL as IRI for the
current request or parts of it.  Here an example:

    >>> get_current_url()
    'http://localhost/script/?param=foo'
    >>> get_current_url(root_only=True)
    'http://localhost/script/'
    >>> get_current_url(host_only=True)
    'http://localhost/'
    >>> get_current_url(strip_querystring=True)
    'http://localhost/script/'

##def **get_json**(force=False, silent=False, cache=True)

Parses the incoming JSON request data and returns it.  If
parsing fails the `on_json_loading_failed` method on the
request object will be invoked.  By default this function will
only load the json data if the mimetype is ``application/json``
but this can be overriden by the `force` parameter.

Args:

  * force: if set to `True` the mimetype is ignored.
  * silent: if set to `False` this method will fail silently
               and return `False`.
  * cache: if set to `True` the parsed JSON data is remembered
              on the request.