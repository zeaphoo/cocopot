

class EnvironBuilder(object):
    pass


class FlagonClinet(object):
    """
    """

    preserve_context = False

    def open(self, *args, **kwargs):
        as_tuple = kwargs.pop('as_tuple', False)
        buffered = kwargs.pop('buffered', False)
        follow_redirects = kwargs.pop('follow_redirects', False)
        builder = make_test_environ_builder(self.application, *args, **kwargs)
