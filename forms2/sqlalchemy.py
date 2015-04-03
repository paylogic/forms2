"""Django forms for SQLAlchemy.

Implements Base model form class that can create initials based on the instance and save the instance, taking
into account field-to-attribute additional mapping.

"""
from __future__ import absolute_import
from django import forms
from django.core.validators import EMPTY_VALUES
try:
    from django.utils.encoding import force_text
except ImportError:
    from django.utils.encoding import force_unicode as force_text
import logging
from sqlalchemy import __version__ as sa_version

logger = logging.getLogger(__name__)


def model_to_dict(instance, keys, mapping=None):
    """Return a dict containing the data in ``instance`` suitable for passing as a Form's ``initial`` keyword argument.

    ``keys`` is an optional list of field names. If provided, only the named
    fields will be included in the returned dict.

    ``mapping`` is an optional dictionary that maps field names to attribute names,
    for example {'field': 'instance.child.field'}.

    """
    data = {}
    mapping = mapping or {}
    for key in keys:
        resolved = mapping.get(key, key)
        bits = resolved.split('.')
        obj = instance
        for bit in bits[:-1]:
            obj = getattr(obj, bit)
        value = getattr(obj, bits[-1], None)
        if value is not None:
            data[key] = value
    return data


def dict_to_model(instance, data, mapping=None):
    """Assign the values in the data dictonary to an instance.

    ``data`` is the cleaned data of the form.

    ``mapping`` is an optional dictionary that maps field names to attribute names,
    for example {'field': 'instance.child.field'}.

    """
    mapping = mapping or {}
    for key, value in data.items():
        key = mapping.get(key, key)
        bits = key.split('.')
        obj = instance
        for bit in bits[:-1]:
            obj = getattr(obj, bit)
        setattr(obj, bits[-1], value)


class BaseModelForm(forms.Form):

    """Base class for the SQLAlchemy model form.

    It implements initials based on the instance and save the instance, taking
    into account field-to-attribute additional mapping.

    By default, save() will call self.save_instance().
    It is necessary to override save_instance() with your own implementation.
    save_instance() is responsible for writing self.instance to the database.
    """

    def __init__(self, instance=None, data=None, files=None, *args, **kwargs):
        self._meta = self.Meta
        self.instance = instance or self._meta.model()
        mapping = getattr(self._meta, 'mapping', {})

        if data is None and files is None:
            initial = model_to_dict(self.instance, self.base_fields.keys(), mapping)
            initial.update(kwargs.pop('initial', {}))
            kwargs['initial'] = initial
        super(BaseModelForm, self).__init__(*args, data=data, files=files, **kwargs)

    def save(self):
        """Update self.instance with the data in cleaned_data and call self.save_instance()."""
        mapping = getattr(self._meta, 'mapping', {})
        ignored_keys = frozenset(('disabled', 'readonly'))
        data = dict((k, v) for k, v in self.cleaned_data.items()
                    if not ignored_keys.intersection(self.fields[k].widget.attrs))
        dict_to_model(self.instance, data, mapping)
        self.save_instance()

    def save_instance(self):
        """Save self.instance. Override this method to manage the saving process yourself."""
        self.instance.save()


class ModelChoiceField(forms.ModelChoiceField):

    """SQLAlchemy compatible multiple choice field."""

    def __init__(self, *args, **kwargs):
        self._label_from_instance = kwargs.pop('label_from_instance', None)
        super(ModelChoiceField, self).__init__(*args, **kwargs)

    @property
    def queryset(self):
        if callable(self._queryset):
            self._queryset = self._queryset(self)
        return self._queryset

    @queryset.setter
    def queryset(self, value):
        self._queryset = value
        self.widget.choices = self.choices

    def __deepcopy__(self, memo):
        result = super(forms.ChoiceField, self).__deepcopy__(memo)
        result.queryset = result._queryset
        return result

    def label_from_instance(self, obj):
        if self._label_from_instance:
            return self._label_from_instance(obj)
        return super(ModelChoiceField, self).label_from_instance(obj)

    @property
    def primary_key(self):
        if self.queryset is not None:
            if sa_version >= '0.8':
                from sqlalchemy import inspect
                return inspect(self.queryset._entities[0].entities[0]).primary_key[0]
            return self.queryset._entities[0].entity.primary_key[0]

    def prepare_value(self, value):
        if self.primary_key is not None:
            return getattr(value, self.primary_key.name, value)

    def to_python(self, value):
        if value in EMPTY_VALUES:
            return None
        value = self.queryset.filter(self.primary_key == value).first()
        if not value:
            raise forms.ValidationError(self.error_messages['invalid_choice'])
        return value


class ModelMultipleChoiceField(ModelChoiceField, forms.ModelMultipleChoiceField):

    """SQLAlchemy compatible multiple choice field."""

    def clean(self, value):
        if self.required and not value:
            raise forms.ValidationError(self.error_messages['required'])
        elif not self.required and not value:
            return []
        if not isinstance(value, (list, tuple)):
            raise forms.ValidationError(self.error_messages['list'])

        qs = self.queryset.filter(self.primary_key.in_(value))
        key = self.primary_key.name
        pks = set([force_text(getattr(o, key)) for o in qs])
        for val in value:
            if force_text(val) not in pks:
                try:
                    error_message = self.error_messages['invalid_choice'] % val
                except TypeError:
                    error_message = self.error_messages['invalid_choice'] % dict(value=value)
                raise forms.ValidationError(error_message)
        # Since this overrides the inherited ModelChoiceField.clean
        # we run custom validators here
        self.run_validators(value)
        return list(qs)

    def prepare_value(self, value):
        if hasattr(value, '__iter__'):
            return [super(ModelMultipleChoiceField, self).prepare_value(v) for v in value]
        return super(ModelMultipleChoiceField, self).prepare_value(value)
