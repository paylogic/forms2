def record(*fields):
    """Generate a class that only allows attr names contained in `fields`"""
    class _Record(object):
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)

        def __setattr__(self, name, value):
            if not name in fields:
                raise AttributeError("Illegal attribute name {0}".format(name))
            super(_Record, self).__setattr__(name, value)

        def _asdict(self):
                dikt = {}
                for field in fields:
                    dikt[field] = getattr(self, field)
                return dikt
    return _Record
