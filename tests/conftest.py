import pytest

from django.conf import settings

try:
    from django.conf import empty
except ImportError:
    empty = None


@pytest.fixture(scope='session', autouse=True)
def django_settings():
    settings._wrapped = empty
    settings.configure()
