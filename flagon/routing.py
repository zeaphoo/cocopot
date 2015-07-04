
import warnings


class Router(object):
    """ A Router is an ordered collection of route->target pairs. It is used to
        efficiently match WSGI requests against a number of routes and return
        the first target that satisfies the request. The target may be anything,
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
        self.rules = []  # All rules in order
        self._groups = {}  # index of regexes to find them in dyna_routes
        self.builder = {}  # Data structure for the url builder
        self.static_routes = {}  # Search structure for static routes
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

    rule_syntax = re.compile('(?:<([a-zA-Z_][a-zA-Z_0-9]*:)?(?:([a-zA-Z_]+))>)')

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
            yield None, converter or 'string', variable
            offset, prefix = match.end(), ''
        if offset <= len(rule) or prefix:
            yield prefix + rule[offset:], None, None

    def add(self, rule, methods, target, defaults=None):
        """ Add a new rule or replace the target for an existing rule. """
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

        self.builder[rule] = builder

        if is_static and not self.strict_order:
            self.static[self.build(rule)] = (target, None)
            return

        try:
            re_pattern = re.compile('^(%s)$' % pattern)
            re_match = re_pattern.match
        except re.error:
            raise RouteSyntaxError("Could not add Route: %s (%s)" %
                                   (rule, _e()))

        if filters:

            def getargs(path):
                url_args = re_match(path).groupdict()
                for name, wildcard_filter in filters:
                    try:
                        url_args[name] = wildcard_filter(url_args[name])
                    except ValueError:
                        raise HTTPError(400, 'Path has wrong format.')
                return url_args
        elif re_pattern.groupindex:

            def getargs(path):
                return re_match(path).groupdict()
        else:
            getargs = None

        whole_rule = (rule, pattern, target, getargs)

        if (pattern, method) in self._groups:
            msg = 'Route <%s %s> overwrites a previously defined route'
            warnings.warn(msg % (method, rule), RuntimeWarning)
            self.dyna_routes[method][
                self._groups[pattern, method]] = whole_rule
        else:
            self.dyna_routes.setdefault(method, []).append(whole_rule)
            self._groups[pattern, method] = len(self.dyna_routes[method]) - 1

    def build(self, _name, *anons, **query):
        """ Build an URL by filling the wildcards in a rule. """
        builder = self.builder.get(_name)
        if not builder:
            raise RouteBuildError("No route with that name.", _name)
        try:
            for i, value in enumerate(anons):
                query['anon%d' % i] = value
            url = ''.join([f(query.pop(n)) if n else f for (n, f) in builder])
            return url if not query else url + '?' + urlencode(query)
        except KeyError:
            raise RouteBuildError('Missing URL argument: %r' % _e().args[0])

    def match(self, environ):
        """ Return a (target, url_args) tuple or raise HTTPError(400/404/405). """
        verb = environ['REQUEST_METHOD'].upper()
        path = environ['PATH_INFO'] or '/'

        if verb == 'HEAD':
            methods = ['PROXY', verb, 'GET', 'ANY']
        else:
            methods = ['PROXY', verb, 'ANY']

        for method in methods:
            if method in self.static and path in self.static[method]:
                target, getargs = self.static[method][path]
                return target, getargs(path) if getargs else {}
            elif method in self.dyna_regexes:
                for combined, rules in self.dyna_regexes[method]:
                    match = combined(path)
                    if match:
                        target, getargs = rules[match.lastindex - 1]
                        return target, getargs(path) if getargs else {}

        # No matching route found. Collect alternative methods for 405 response
        allowed = set([])
        nocheck = set(methods)
        for method in set(self.static) - nocheck:
            if path in self.static[method]:
                allowed.add(verb)
        for method in set(self.dyna_regexes) - allowed - nocheck:
            for combined, rules in self.dyna_regexes[method]:
                match = combined(path)
                if match:
                    allowed.add(method)
        if allowed:
            allow_header = ",".join(sorted(allowed))
            raise HTTPError(405, "Method not allowed.", Allow=allow_header)

        # No matching route and no alternative method found. We give up
        raise HTTPError(404, "Not found: " + repr(path))
