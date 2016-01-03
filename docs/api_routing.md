#class Router(strict=False)

A Router is an ordered collection of route->endpoint pairs. It is used to
efficiently match WSGI requests against a number of routes and return
the first endpoint that satisfies the request. The endpoint may be anything,
usually a string, ID or callable object. A route consists of a path-rule
and a HTTP method.
The path-rule is either a static path (e.g. `/contact`) or a dynamic
path that contains wildcards (e.g. `/wiki/<page>`). The wildcard syntax
and details on the matching order are described in docs:`routing`.


##var **rule_syntax**



##var **filters**



##var **dynamic_patterns**



##var **strict_order**



##var **dynamic_routes**



##var **static_routes**



##def **add_filter**(name, func)

Add a filter. The provided function is called with the configuration
string as parameter and must return a (regexp, to_python, to_url) tuple.
The first element is a string, the last two are callables or None. 

##def **add**(rule, endpoint, methods=['GET'], defaults=None)

Add a new rule or replace the endpoint for an existing rule. 

##def **match**(path, method='GET')

Return a (endpoint, url_args) tuple or raise HTTPException(400/404/405). 