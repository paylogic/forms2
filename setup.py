"""Package entry point."""
import codecs
from os.path import abspath, dirname, join

from setuptools import setup, find_packages

from forms2 import __version__


long_description = []

for text_file in ['README.rst', 'CHANGES.rst']:
    with codecs.open(join(dirname(abspath(__file__)), text_file), 'r', encoding='utf-8') as f:
        long_description.append(f.read())

setup(
    name='forms2',
    description='Extra features for Django Forms',
    long_description='\n'.join(long_description),
    version=__version__,
    author='Paylogic International',
    author_email='developers@paylogic.com',
    license='MIT',
    install_requires=[
        'Django',
        'SQLAlchemy'
    ],
    packages=find_packages(exclude=['ez_setup', 'tests']),
    dependency_links=[],
    tests_require=['tox'],
    include_package_data=True,
    keywords='django forms extensions sqlalchemy acl',
)
