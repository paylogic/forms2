"""Individual field access support for the form.
The form class should define a mapping of the field names to a callable that returns enabled, readonly or excluded.

"""

from django.forms.widgets import Input, MultiWidget
from django.forms import MultiValueField


class FieldAccess(object):
    enabled = 1
    readonly = 2
    excluded = 3


class AccessFilter(object):
    """
    Wraps a filter function to provide infix operators.
    In filters, None is used to mean failure.
    """
    def __init__(self, func):
        self.func = func

    def __call__(self, *args, **kwargs):
        """Call the wrapped function"""
        return self.func(*args, **kwargs)

    def __or__(self, other):
        """Combines two filters, returns the first if it doesn't fail, the second otherwise."""
        @AccessFilter
        def f(*args, **kwargs):
            first = self(*args, **kwargs)
            if first is None:
                return other(*args, **kwargs)
            return first
        return f

    def __rshift__(self, next):
        """Binds the result of one filter to a function, returning a filter if the first doesn't fail."""
        @AccessFilter
        def f(*args, **kwargs):
            first = self(*args, **kwargs)
            if first is None:
                return None
            return next(first)(*args, **kwargs)
        return f

    def __and__(self, other):
        """Combines two filters, fails if one of the two fails, returns the second otherwise."""
        return self >> (lambda _: other)


def access_filter(f):
    """Decorator for AccessFilter class"""
    return AccessFilter(f)


@access_filter
def default(access):
    """Returns a filter that always returns the given access level."""
    return lambda *args, **kwargs: access


def expand_tuple_keys(dictionary):
    """Expands elements of the tuple keys to individual keys of the dictionary."""
    data = {}
    for k, v in dictionary.items():
        if isinstance(k, tuple):
            for x in k:
                data[x] = v
        else:
            data[k] = v
    return data


class FieldAccessMixin(object):
    """Mixin class that adds support of the individual field access."""

    def set_required(self, field, required):
        fields = [field]
        if isinstance(field, MultiValueField):
            fields += field.fields
        for field in fields:
            field.required = required

    def set_readonly(self, field):
        self.set_required(field, False)
        widgets = [field.widget]
        if isinstance(field.widget, MultiWidget):
            widgets += field.widget.widgets
        for widget in widgets:
            if isinstance(widget, (Input, MultiWidget)):
                widget.attrs['readonly'] = ''
            else:
                widget.attrs['disabled'] = ''

    def __init__(self, user=None, *args, **kwargs):
        super(FieldAccessMixin, self).__init__(*args, **kwargs)
        self.user = user
        self._meta = self.__class__.Meta
        access = expand_tuple_keys(getattr(self._meta, 'access', {}))
        for name, field in list(self.fields.items()):
            func = access.get(name, access.get(None, default(FieldAccess.enabled)))
            field_access = func(self.user, self.instance)
            if field_access == FieldAccess.readonly:
                self.set_readonly(field)
            elif field_access == FieldAccess.excluded:
                del self.fields[name]
