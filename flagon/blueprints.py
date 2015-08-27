# -*- coding: utf-8 -*-
"""
    Blueprints are the recommended way to implement larger or more
    pluggable applications.

"""
from functools import update_wrapper

class Blueprint(object):
    """Represents a blueprint.
    """

    def __init__(self, name, import_name,
                 url_prefix=None, url_defaults=None):
        self.app = None
        self.name = name
        self.url_prefix = url_prefix
        self.deferred_functions = []
        self.view_functions = {}
        if url_defaults is None:
            url_defaults = {}
        self.url_values_defaults = url_defaults

    def record(self, func):
        """Registers a function that is called when the blueprint is
        registered on the application.  This function is called with the
        state as argument as returned by the `make_setup_state`
        method.
        """
        if self.app:
            from warnings import warn
            warn(Warning('The blueprint was already registered once '
                         'but is getting modified now.  These changes '
                         'will not show up.'))
        self.deferred_functions.append(func)


    def register(self, app, options, first_registration=False):
        """Called by `Flagon.register_blueprint` to register a blueprint
        on the application.  This can be overridden to customize the register
        behavior.  Keyword arguments from
        :func:`~flagon.Flagon.register_blueprint` are directly forwarded to this
        method in the `options` dictionary.
        """
        self.app = app
        for deferred in self.deferred_functions:
            deferred(self)

    def route(self, rule, **options):
        """Like `Flagon.route` but for a blueprint.  The endpoint for the
        :func:`url_for` function is prefixed with the name of the blueprint.
        """
        def decorator(f):
            endpoint = options.pop("endpoint", f.__name__)
            self.add_url_rule(rule, endpoint, f, **options)
            return f
        return decorator

    def add_url_rule(self, rule, endpoint=None, view_func=None, **options):
        """Like `Flagon.add_url_rule` but for a blueprint.  The endpoint for
        the :func:`url_for` function is prefixed with the name of the blueprint.
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
        if self.url_prefix:
            rule = self.url_prefix + rule
        if endpoint is None:
            endpoint = view_func.__name__
        defaults = self.url_defaults
        if 'defaults' in options:
            defaults = dict(defaults, **options.pop('defaults'))
        self.app.add_url_rule(rule, '%s.%s' % (self.blueprint.name, endpoint),
                              view_func, defaults=defaults, **options)

    def endpoint(self, endpoint):
        """Like `Flagon.endpoint` but for a blueprint.  This does not
        prefix the endpoint with the blueprint name, this has to be done
        explicitly by the user of this method.  If the endpoint is prefixed
        with a `.` it will be registered to the current blueprint, otherwise
        it's an application independent endpoint.
        """
        def decorator(f):
            def register_endpoint(state):
                state.app.view_functions[endpoint] = f
            self.record(register_endpoint)
            return f
        return decorator


    def before_request(self, f):
        """Like `Flagon.before_request` but for a blueprint.  This function
        is only executed before each request that is handled by a function of
        that blueprint.
        """
        self.record(lambda s: s.app.before_request_funcs
            .setdefault(self.name, []).append(f))
        return f

    def before_app_request(self, f):
        """Like `Flagon.before_request`.  Such a function is executed
        before each request, even if outside of a blueprint.
        """
        self.record(lambda s: s.app.before_request_funcs
            .setdefault(None, []).append(f))
        return f

    def after_request(self, f):
        """Like `Flagon.after_request` but for a blueprint.  This function
        is only executed after each request that is handled by a function of
        that blueprint.
        """
        self.record(lambda s: s.app.after_request_funcs
            .setdefault(self.name, []).append(f))
        return f

    def after_app_request(self, f):
        """Like `Flagon.after_request` but for a blueprint.  Such a function
        is executed after each request, even if outside of the blueprint.
        """
        self.record(lambda s: s.app.after_request_funcs
            .setdefault(None, []).append(f))
        return f

    def teardown_request(self, f):
        """Like `Flagon.teardown_request` but for a blueprint.  This
        function is only executed when tearing down requests handled by a
        function of that blueprint.  Teardown request functions are executed
        when the request context is popped, even when no actual request was
        performed.
        """
        self.record(lambda s: s.app.teardown_request_funcs
            .setdefault(self.name, []).append(f))
        return f

    def teardown_app_request(self, f):
        """Like `Flagon.teardown_request` but for a blueprint.  Such a
        function is executed when tearing down each request, even if outside of
        the blueprint.
        """
        self.record(lambda s: s.app.teardown_request_funcs
            .setdefault(None, []).append(f))
        return f

    def app_errorhandler(self, code):
        """Like `Flagon.errorhandler` but for a blueprint.  This
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

        Otherwise works as the `~flagon.Flagon.errorhandler` decorator
        of the `~flagon.Flagon` object.
        """
        def decorator(f):
            self.record(lambda s: s.app._register_error_handler(
                self.name, code_or_exception, f))
            return f
        return decorator
