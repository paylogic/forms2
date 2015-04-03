"""Extends Django forms with the classes that support individual field access control and edit the SQLAlchemy models."""
__all__ = ('SAModelForm', 'FieldAccessForm', 'ModelChoiceField', 'FieldAccess', 'ModelMultipleChoiceField')

__version__ = '1.1.1'

try:
    from django import forms
    from django.forms.forms import DeclarativeFieldsMetaclass
    from forms2.sqlalchemy import BaseModelForm as SABaseModelForm, ModelChoiceField, ModelMultipleChoiceField
    from forms2.access import FieldAccess, FieldAccessMixin

    class SAModelForm(FieldAccessMixin, SABaseModelForm):

        """SQLAlchemy aware model form."""

        __metaclass__ = DeclarativeFieldsMetaclass

    class FieldAccessForm(forms.Form, FieldAccessMixin):

        """Field access aware form."""

        def __init__(self, instance, *args, **kwargs):
            self.instance = instance
            super(FieldAccessForm, self).__init__(*args, **kwargs)
except ImportError:
    pass
