
import re
from .exceptions import BadRequest, NotFound, MethodNotAllowed

class RouteSyntaxError(Exception):
    pass

class Router(object):
    """ A Router is an ordered collection of route->endpoint pairs. It is used to
        efficiently match WSGI requests against a number of routes and return
        the first endpoint that satisfies the request. The endpoint may be anything,
        usually a string, ID or callable object. A route consists of a path-rule
        and a HTTP method.
        The path-rule is either a static path (e.g. `/contact`) or a dynamic
        path that contains wildcards (e.g. `/wiki/<page>`). The wildcard syntax
        and details on the matching order are described in docs:`routing`.
    """
    #: The current CPython regexp implementation does not allow more
    #: than 99 matching groups per regular expression.
    _MAX_GROUPS_PER_PATTERN = 99

    def __init__(self, strict=False):
        self.static_routes = {}  # Search structure for static routes
        self.dynamic_patterns = []
        self.dynamic_routes = {}
        #: If true, static routes are no longer checked first.
        self.strict_order = strict
        self.filters = {
            'string': lambda: (r'[^/]+', None, None),
            'int': lambda: (r'-?\d+', int, lambda x: str(int(x))),
            'float': lambda: (r'-?[\d.]+', float, lambda x: str(float(x))),
            'path': lambda: (r'.+?', None, None)
        }

    def add_filter(self, name, func):
        """ Add a filter. The provided function is called with the configuration
        string as parameter and must return a (regexp, to_python, to_url) tuple.
        The first element is a string, the last two are callables or None. """
        self.filters[name] = func

    rule_syntax = re.compile('(?:<([a-zA-Z_]+:)?(?:([a-zA-Z_][a-zA-Z_0-9]*))>)')

    def _itertokens(self, rule):
        offset, prefix = 0, ''
        for match in self.rule_syntax.finditer(rule):
            prefix += rule[offset:match.start()]
            g = match.groups()
            if prefix:
                yield prefix, None, None
            if g[1] is None:
                converter, variable = None, g[0]
            else:
                converter, variable = g[0], g[1]
            converter = converter[:-1] if converter else 'string'
            yield None, converter, variable
            offset, prefix = match.end(), ''
        if offset <= len(rule) or prefix:
            yield prefix + rule[offset:], None, None

    def add(self, rule, endpoint, methods=['GET'], defaults=None):
        """ Add a new rule or replace the endpoint for an existing rule. """
        pattern = ''  # Regular expression pattern with named groups
        filters = []  # Lists of wildcard input filters
        builder = []  # Data structure for the URL builder
        is_static = True

        for key, converter, variable in self._itertokens(rule):
            if converter:
                is_static = False
                mask, in_filter, out_filter = self.filters[converter]()
                pattern += '(?P<%s>%s)' % (variable, mask)
                if in_filter: filters.append((variable, in_filter))
                builder.append((variable, out_filter or str))
            elif key:
                pattern += re.escape(key)
                builder.append((None, key))

        rule_args = dict(endpoint=endpoint, rule=rule, filters=filters,
                        builder=builder, pattern=pattern, defaults=defaults)
        if is_static and not self.strict_order:
            self.static_routes[rule] = dict([(m.upper(), rule_args)for m in methods])
            return

        try:
            re_pattern = re.compile('^(%s)$' % pattern)
            re_match = re_pattern.match
        except re.error as _e:
            raise RouteSyntaxError("Could not add Route: %s (%s)" %
                                   (rule, _e()))

        rule_args['match'] = re_match

        self.dynamic_patterns.append(re_pattern)
        self.dynamic_routes[re_pattern] = dict([(m.upper(), rule_args)for m in methods])



    def match(self, path, method='GET'):
        """ Return a (endpoint, url_args) tuple or raise HTTPException(400/404/405). """
        rule_args = self.static_routes.get(path)
        url_args = {}
        if not rule_args:
            for re_pattern in self.dynamic_patterns:
                matched = re_pattern.match(path)
                if matched:
                    url_args = matched.groupdict()
                    rule_args = self.dynamic_routes[re_pattern]
                    break

        if not rule_args:
            raise NotFound("Not found: " + repr(path))

        if method not in rule_args:
            allow_header = ",".join(sorted(rule_args.keys()))
            raise MethodNotAllowed("Method not allowed. Allowed methods: %s"%(allow_header))

        args = rule_args[method]
        filters = args.get('filters')
        defaults = args.get('defaults') or {}
        if filters:
            for name, wildcard_filter in filters:
                try:
                    url_args[name] = wildcard_filter(url_args[name])
                except ValueError:
                    raise BadRequest('Path has wrong format.')
        for k, v in defaults.items():
            if k not in url_args:
                url_args[k] = v
        return args['endpoint'], url_args
