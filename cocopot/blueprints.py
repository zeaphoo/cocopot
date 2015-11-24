# -*- coding: utf-8 -*-
"""
    Blueprints are the recommended way to implement larger or more
    pluggable applications.

"""
from functools import update_wrapper

class Blueprint(object):
    """Represents a blueprint.
    """

    def __init__(self, name, url_prefix=None, url_defaults=None):
        self.app = None
        self.name = name
        self.url_prefix = url_prefix
        self.deferred_functions = []
        self.view_functions = {}
        self.url_defaults = url_defaults or {}
        self.register_options = {}

    def record(self, func):
        """Registers a function that is called when the blueprint is
        registered on the application.  This function is called with the
        state as argument as returned by the `make_setup_state`
        method.
        """
        if self.app:
            from warnings import warn
            warn('The blueprint was already registered once '
                         'but is getting modified now.  These changes '
                         'will not show up.')
        self.deferred_functions.append(func)


    def register(self, app, options):
        """Called by `Cocopot.register_blueprint` to register a blueprint
        on the application.  This can be overridden to customize the register
        behavior.  Keyword arguments from
        `~cocopot.Cocopot.register_blueprint` are directly forwarded to this
        method in the `options` dictionary.
        """
        self.app = app
        self.register_options = options or {}
        for deferred in self.deferred_functions:
            deferred(self)

    def route(self, rule, **options):
        """Like `Cocopot.route` but for a blueprint.
        """
        def decorator(f):
            endpoint = options.pop("endpoint", f.__name__)
            self.add_url_rule(rule, endpoint, f, **options)
            return f
        return decorator

    def add_url_rule(self, rule, endpoint=None, view_func=None, **options):
        """Like `Cocopot.add_url_rule` but for a blueprint.
        """
        if endpoint:
            assert '.' not in endpoint, "Blueprint endpoint's should not contain dot's"
        self.record(lambda s:
            s.app_add_url_rule(rule, endpoint, view_func, **options))

    def app_add_url_rule(self, rule, endpoint=None, view_func=None, **options):
        """A helper method to register a rule (and optionally a view function)
        to the application.  The endpoint is automatically prefixed with the
        blueprint's name.
        """
        url_prefix = self.register_options.get('url_prefix') or self.url_prefix
        if url_prefix:
            rule = url_prefix + rule
        if endpoint is None:
            endpoint = view_func.__name__
        defaults = self.url_defaults
        if 'defaults' in options:
            defaults = dict(defaults, **options.pop('defaults'))
        self.app.add_url_rule(rule, '%s.%s' % (self.name, endpoint),
                              view_func, defaults=defaults, **options)

    def endpoint(self, endpoint):
        """Like `Cocopot.endpoint` but for a blueprint.  This does not
        prefix the endpoint with the blueprint name, this has to be done
        explicitly by the user of this method.  If the endpoint is prefixed
        with a `.` it will be registered to the current blueprint, otherwise
        it's an application independent endpoint.
        """
        def decorator(f):
            def register_endpoint(self):
                self.app.view_functions['%s.%s' % (self.name, endpoint)] = f
            self.record(register_endpoint)
            return f
        return decorator


    def before_request(self, f):
        """Like `Cocopot.before_request` but for a blueprint.  This function
        is only executed before each request that is handled by a function of
        that blueprint.
        """
        self.record(lambda s: s.app.before_request_funcs
            .setdefault(self.name, []).append(f))
        return f

    def before_app_request(self, f):
        """Like `Cocopot.before_request`.  Such a function is executed
        before each request, even if outside of a blueprint.
        """
        self.record(lambda s: s.app.before_request_funcs
            .setdefault(None, []).append(f))
        return f

    def after_request(self, f):
        """Like `Cocopot.after_request` but for a blueprint.  This function
        is only executed after each request that is handled by a function of
        that blueprint.
        """
        self.record(lambda s: s.app.after_request_funcs
            .setdefault(self.name, []).append(f))
        return f

    def after_app_request(self, f):
        """Like `Cocopot.after_request` but for a blueprint.  Such a function
        is executed after each request, even if outside of the blueprint.
        """
        self.record(lambda s: s.app.after_request_funcs
            .setdefault(None, []).append(f))
        return f

    def teardown_request(self, f):
        """Like `Cocopot.teardown_request` but for a blueprint.  This
        function is only executed when tearing down requests handled by a
        function of that blueprint.  Teardown request functions are executed
        when the request context is popped, even when no actual request was
        performed.
        """
        self.record(lambda s: s.app.teardown_request_funcs
            .setdefault(self.name, []).append(f))
        return f

    def teardown_app_request(self, f):
        """Like `Cocopot.teardown_request` but for a blueprint.  Such a
        function is executed when tearing down each request, even if outside of
        the blueprint.
        """
        self.record(lambda s: s.app.teardown_request_funcs
            .setdefault(None, []).append(f))
        return f

    def app_errorhandler(self, code):
        """Like `Cocopot.errorhandler` but for a blueprint.  This
        handler is used for all requests, even if outside of the blueprint.
        """
        def decorator(f):
            self.record(lambda s: s.app.errorhandler(code)(f))
            return f
        return decorator


    def errorhandler(self, code_or_exception):
        """Registers an error handler that becomes active for this blueprint
        only.  Please be aware that routing does not happen local to a
        blueprint so an error handler for 404 usually is not handled by
        a blueprint unless it is caused inside a view function.  Another
        special case is the 500 internal server error which is always looked
        up from the application.

        Otherwise works as the `Cocopot.errorhandler` decorator
        of the `Cocopot` object.
        """
        def decorator(f):
            self.record(lambda s: s.app._register_error_handler(
                self.name, code_or_exception, f))
            return f
        return decorator
