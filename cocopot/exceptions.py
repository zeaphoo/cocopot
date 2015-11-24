# -*- coding: utf-8 -*-
"""
    This module implements a number of Python exceptions you can raise from
    within your views to trigger a standard non-200 response.

"""
import sys

from ._compat import integer_types, text_type
from .http import HTTP_STATUS_CODES, html_escape


class HTTPException(Exception):
    """
    Baseclass for all HTTP exceptions.  This exception can be called as WSGI
    application to render a default error page or you can catch the subclasses
    of it independently and render nicer error messages.
    """

    code = 555
    description = 'Unknown http exception'

    def __init__(self, description=None):
        Exception.__init__(self)
        if description is not None:
            self.description = description

    @property
    def name(self):
        """The status name."""
        return HTTP_STATUS_CODES.get(self.code, 'Unknown Error')

    def get_description(self):
        """Get the description."""
        return u'%s' % self.description

    def get_body(self):
        """Get the HTML body."""
        return text_type((u'%(description)s') % {
            'description':  self.get_description()
        })

    def get_headers(self):
        """Get a list of headers."""
        return [('Content-Type', 'text/plain')]


    def __str__(self):
        return '%d: %s' % (self.code, self.name)

    def __repr__(self):
        return '<%s \'%s\'>' % (self.__class__.__name__, self)


class RequestRedirect(HTTPException):

    """Raise if the map requests a redirect. This is for example the case if
    `strict_slashes` are activated and an url that requires a trailing slash.
    The attribute `new_url` contains the absolute destination url.
    """
    code = 301

    def __init__(self, new_url):
        self.new_url = new_url

    def get_headers(self):
        return [('Location', self.new_url), ('Content-Type', 'text/html')]

    def get_body(self):
        display_location = html_escape(self.new_url)
        body = text_type((
            '<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 3.2 Final//EN">\n'
            '<title>Redirecting...</title>\n'
            '<h1>Redirecting...</h1>\n'
            '<p>You should be redirected automatically to target URL: '
            '<a href="%s">%s</a>.  If not click the link.') % (html_escape(self.new_url), display_location))
        return body

class BadRequest(HTTPException):
    """*400* `Bad Request`

    Raise if the browser sends something to the application the application
    or server cannot handle.
    """
    code = 400
    description = (
        'The browser (or proxy) sent a request that this server could '
        'not understand.'
    )



class SecurityError(BadRequest):
    """Raised if something triggers a security error.  This is otherwise
    exactly like a bad request error.

    """


class Unauthorized(HTTPException):
    """*401* `Unauthorized`

    Raise if the user is not authorized.  Also used if you want to use HTTP
    basic auth.
    """
    code = 401
    description = (
        'The server could not verify that you are authorized to access '
        'the URL requested.  You either supplied the wrong credentials (e.g. '
        'a bad password), or your browser doesn\'t understand how to supply '
        'the credentials required.'
    )


class Forbidden(HTTPException):
    """*403* `Forbidden`

    Raise if the user doesn't have the permission for the requested resource
    but was authenticated.
    """
    code = 403
    description = (
        'You don\'t have the permission to access the requested resource. '
        'It is either read-protected or not readable by the server.'
    )


class NotFound(HTTPException):
    """*404* `Not Found`

    Raise if a resource does not exist and never existed.
    """
    code = 404
    description = (
        'The requested URL was not found on the server.  '
        'If you entered the URL manually please check your spelling and '
        'try again.'
    )


class MethodNotAllowed(HTTPException):
    """*405* `Method Not Allowed`

    Raise if the server used a method the resource does not handle.  For
    example `POST` if the resource is view only.  Especially useful for REST.

    The first argument for this exception should be a list of allowed methods.
    Strictly speaking the response would be invalid if you don't provide valid
    methods in the header which you can do with that list.
    """
    code = 405
    description = 'The method is not allowed for the requested URL.'

    def __init__(self, valid_methods=None, description=None):
        """Takes an optional list of valid http methods
        starting with cocopot."""
        HTTPException.__init__(self, description)
        self.valid_methods = valid_methods

    def get_headers(self):
        headers = HTTPException.get_headers(self)
        if self.valid_methods:
            headers.append(('Allow', ', '.join(self.valid_methods)))
        return headers


class NotAcceptable(HTTPException):
    """*406* `Not Acceptable`

    Raise if the server can't return any content conforming to the
    `Accept` headers of the client.
    """
    code = 406

    description = (
        'The resource identified by the request is only capable of '
        'generating response entities which have content characteristics '
        'not acceptable according to the accept headers sent in the '
        'request.'
    )


class RequestTimeout(HTTPException):
    """*408* `Request Timeout`

    Raise to signalize a timeout.
    """
    code = 408
    description = (
        'The server closed the network connection because the browser '
        'didn\'t finish the request within the specified time.'
    )


class Conflict(HTTPException):
    """*409* `Conflict`

    Raise to signal that a request cannot be completed because it conflicts
    with the current state on the server.

    """
    code = 409
    description = (
        'A conflict happened while processing the request.  The resource '
        'might have been modified while the request was being processed.'
    )


class Gone(HTTPException):
    """*410* `Gone`

    Raise if a resource existed previously and went away without new location.
    """
    code = 410
    description = (
        'The requested URL is no longer available on this server and there '
        'is no forwarding address. If you followed a link from a foreign '
        'page, please contact the author of this page.'
    )


class LengthRequired(HTTPException):
    """*411* `Length Required`

    Raise if the browser submitted data but no ``Content-Length`` header which
    is required for the kind of processing the server does.
    """
    code = 411
    description = (
        'A request with this method requires a valid <code>Content-'
        'Length</code> header.'
    )


class PreconditionFailed(HTTPException):
    """*412* `Precondition Failed`

    Status code used in combination with ``If-Match``, ``If-None-Match``, or
    ``If-Unmodified-Since``.
    """
    code = 412
    description = (
        'The precondition on the request for the URL failed positive '
        'evaluation.'
    )


class RequestEntityTooLarge(HTTPException):
    """*413* `Request Entity Too Large`

    The status code one should return if the data submitted exceeded a given
    limit.
    """
    code = 413
    description = (
        'The data value transmitted exceeds the capacity limit.'
    )


class RequestURITooLarge(HTTPException):
    """*414* `Request URI Too Large`

    Like *413* but for too long URLs.
    """
    code = 414
    description = (
        'The length of the requested URL exceeds the capacity limit '
        'for this server.  The request cannot be processed.'
    )


class UnsupportedMediaType(HTTPException):
    """*415* `Unsupported Media Type`

    The status code returned if the server is unable to handle the media type
    the client transmitted.
    """
    code = 415
    description = (
        'The server does not support the media type transmitted in '
        'the request.'
    )


class RequestedRangeNotSatisfiable(HTTPException):
    """*416* `Requested Range Not Satisfiable`

    The client asked for a part of the file that lies beyond the end
    of the file.

    """
    code = 416
    description = (
        'The server cannot provide the requested range.'
    )


class ExpectationFailed(HTTPException):
    """*417* `Expectation Failed`

    The server cannot meet the requirements of the Expect request-header.

    """
    code = 417
    description = (
        'The server could not meet the requirements of the Expect header'
    )


class ImATeapot(HTTPException):
    """*418* `I'm a teapot`

    The server should return this if it is a teapot and someone attempted
    to brew coffee with it.

    """
    code = 418
    description = (
        'This server is a teapot, not a coffee machine'
    )


class UnprocessableEntity(HTTPException):
    """*422* `Unprocessable Entity`

    Used if the request is well formed, but the instructions are otherwise
    incorrect.
    """
    code = 422
    description = (
        'The request was well-formed but was unable to be followed '
        'due to semantic errors.'
    )


class PreconditionRequired(HTTPException):
    """*428* `Precondition Required`

    The server requires this request to be conditional, typically to prevent
    the lost update problem, which is a race condition between two or more
    clients attempting to update a resource through PUT or DELETE. By requiring
    each client to include a conditional header ("If-Match" or "If-Unmodified-
    Since") with the proper value retained from a recent GET request, the
    server ensures that each client has at least seen the previous revision of
    the resource.
    """
    code = 428
    description = (
        'This request is required to be conditional; try using "If-Match" '
        'or "If-Unmodified-Since".'
    )


class TooManyRequests(HTTPException):
    """*429* `Too Many Requests`

    The server is limiting the rate at which this user receives responses, and
    this request exceeds that rate. (The server may use any convenient method
    to identify users and their request rates). The server may include a
    "Retry-After" header to indicate how long the user should wait before
    retrying.
    """
    code = 429
    description = (
        'This user has exceeded an allotted request count. Try again later.'
    )


class RequestHeaderFieldsTooLarge(HTTPException):
    """*431* `Request Header Fields Too Large`

    The server refuses to process the request because the header fields are too
    large. One or more individual fields may be too large, or the set of all
    headers is too large.
    """
    code = 431
    description = (
        'One or more header fields exceeds the maximum size.'
    )


class InternalServerError(HTTPException):
    """*500* `Internal Server Error`

    Raise if an internal server error occurred.  This is a good fallback if an
    unknown error occurred in the dispatcher.
    """
    code = 500
    description = (
        'The server encountered an internal error and was unable to '
        'complete your request.  Either the server is overloaded or there '
        'is an error in the application.'
    )


class NotImplemented(HTTPException):
    """*501* `Not Implemented`

    Raise if the application does not support the action requested by the
    browser.
    """
    code = 501
    description = (
        'The server does not support the action requested by the '
        'browser.'
    )


class BadGateway(HTTPException):
    """*502* `Bad Gateway`

    If you do proxying in your application you should return this status code
    if you received an invalid response from the upstream server it accessed
    in attempting to fulfill the request.
    """
    code = 502
    description = (
        'The proxy server received an invalid response from an upstream '
        'server.'
    )


class ServiceUnavailable(HTTPException):
    """*503* `Service Unavailable`

    Status code you should return if a service is temporarily unavailable.
    """
    code = 503
    description = (
        'The server is temporarily unable to service your request due to '
        'maintenance downtime or capacity problems.  Please try again '
        'later.'
    )


class GatewayTimeout(HTTPException):
    """*504* `Gateway Timeout`

    Status code you should return if a connection to an upstream server
    times out.
    """
    code = 504
    description = (
        'The connection to an upstream server timed out.'
    )


class HTTPVersionNotSupported(HTTPException):
    """*505* `HTTP Version Not Supported`

    The server does not support the HTTP protocol version used in the request.
    """
    code = 505
    description = (
        'The server does not support the HTTP protocol version used in the '
        'request.'
    )


default_exceptions = {}
__all__ = ['HTTPException']

def _find_exceptions():
    for name, obj in globals().items():
        try:
            is_http_exception = issubclass(obj, HTTPException)
        except TypeError:
            is_http_exception = False
        if not is_http_exception or obj.code is None:
            continue
        __all__.append(obj.__name__)
        old_obj = default_exceptions.get(obj.code, None)
        if old_obj is not None and issubclass(obj, old_obj):
            continue
        default_exceptions[obj.code] = obj
_find_exceptions()
del _find_exceptions


def abort(code, *args, **kwargs):
    mapping = default_exceptions
    if not args and not kwargs and not isinstance(code, integer_types):
        raise HTTPException(response=code)
    if code not in mapping:
        raise LookupError('no exception for %r' % code)
    raise mapping[code](*args, **kwargs)
