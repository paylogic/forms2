"""Tests configuration."""
from django.conf import settings

try:
    from django.conf import empty
except ImportError:
    empty = None

from . import django_settings_test


def pytest_configure():
    settings._wrapped = empty
    settings.configure(django_settings_test)
