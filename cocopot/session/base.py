
class SessionConfig(object):
    def __init__(self, **kwargs):
        pass

class ModelDict(dict):
    def __init__(self, *a, **k):
        super(ModelDict, self).__init__(*a, **k)
        self.dirty = False

    def __setitem__(self, *a, **k):
        self.mark_dirty()
        super(ModelDict, self).__setitem__(*a, **k)

    def __delitem__(self, *a, **k):
        self.mark_dirty()
        super(ModelDict, self).__delitem__(*a, **k)

    def mark_clean(self):
        self.dirty = False

    def mark_dirty(self):
        self.dirty = True

    def clear(self, *a, **k):
        self.mark_dirty()
        super(ModelDict, self).clear(*a, **k)

    def pop(self, *a, **k):
        self.mark_dirty()
        super(ModelDict, self).pop(*a, **k)

    def popitem(self, *a, **k):
        self.mark_dirty()
        super(ModelDict, self).popitem(*a, **k)

    def setdefault(self, *a, **k):
        self.mark_dirty()
        super(ModelDict, self).setdefault(*a, **k)

    def update(self, *a, **k):
        self.mark_dirty()
        super(ModelDict, self).update(*a, **k)

    def __repr__(self):
        return '<%s %s>' % (
            self.__class__.__name__,
            dict.__repr__(self)
        )

class BaseSession(ModelDict):
    def __init__(self):
        pass

    def open(self, request):
        raise NotImplementedError()

    def save(self, response):
        raise NotImplementedError()
