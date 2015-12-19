#Module cocopot.blueprints
Blueprints are the recommended way to implement larger or more
pluggable applications.
##class Blueprint(name, url_prefix=None, url_defaults=None)

Represents a blueprint.
    


###var **url_prefix**



###var **register_options**



###var **name**



###var **url_defaults**



###var **app**



###var **view_functions**



###var **deferred_functions**



###def **after_app_request**(f)

Like `Cocopot.after_request` but for a blueprint.  Such a function
is executed after each request, even if outside of the blueprint.

###def **endpoint**(endpoint)

Like `Cocopot.endpoint` but for a blueprint.  This does not
prefix the endpoint with the blueprint name, this has to be done
explicitly by the user of this method.  If the endpoint is prefixed
with a `.` it will be registered to the current blueprint, otherwise
it's an application independent endpoint.

###def **teardown_app_request**(f)

Like `Cocopot.teardown_request` but for a blueprint.  Such a
function is executed when tearing down each request, even if outside of
the blueprint.

###def **before_app_request**(f)

Like `Cocopot.before_request`.  Such a function is executed
before each request, even if outside of a blueprint.

###def **route**(rule, **options)

Like `Cocopot.route` but for a blueprint.
        

###def **register**(app, options)

Called by `Cocopot.register_blueprint` to register a blueprint
on the application.  This can be overridden to customize the register
behavior.  Keyword arguments from
`~cocopot.Cocopot.register_blueprint` are directly forwarded to this
method in the `options` dictionary.

###def **errorhandler**(code_or_exception)

Registers an error handler that becomes active for this blueprint
only.  Please be aware that routing does not happen local to a
blueprint so an error handler for 404 usually is not handled by
a blueprint unless it is caused inside a view function.  Another
special case is the 500 internal server error which is always looked
up from the application.

Otherwise works as the `Cocopot.errorhandler` decorator
of the `Cocopot` object.

###def **record**(func)

Registers a function that is called when the blueprint is
registered on the application.  This function is called with the
state as argument as returned by the `make_setup_state`
method.

###def **app_errorhandler**(code)

Like `Cocopot.errorhandler` but for a blueprint.  This
handler is used for all requests, even if outside of the blueprint.

###def **add_url_rule**(rule, endpoint=None, view_func=None, **options)

Like `Cocopot.add_url_rule` but for a blueprint.
        

###def **before_request**(f)

Like `Cocopot.before_request` but for a blueprint.  This function
is only executed before each request that is handled by a function of
that blueprint.

###def **app_add_url_rule**(rule, endpoint=None, view_func=None, **options)

A helper method to register a rule (and optionally a view function)
to the application.  The endpoint is automatically prefixed with the
blueprint's name.

###def **after_request**(f)

Like `Cocopot.after_request` but for a blueprint.  This function
is only executed after each request that is handled by a function of
that blueprint.

###def **teardown_request**(f)

Like `Cocopot.teardown_request` but for a blueprint.  This
function is only executed when tearing down requests handled by a
function of that blueprint.  Teardown request functions are executed
when the request context is popped, even when no actual request was
performed.
