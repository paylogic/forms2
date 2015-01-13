"""Package entry point."""
from os.path import abspath, dirname, join

from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand
import sys

from forms2 import __version__


class ToxTestCommand(TestCommand):

    """Test command which runs tox under the hood."""

    user_options = [('tox-args=', 'a', "Arguments to pass to tox")]

    def initialize_options(self):
        """Initialize options and set their defaults."""
        TestCommand.initialize_options(self)
        self.tox_args = '--recreate'

    def finalize_options(self):
        """Add options to the test runner (tox)."""
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        """Invoke the test runner (tox)."""
        # import here, cause outside the eggs aren't loaded
        import tox
        import shlex
        errno = tox.cmdline(args=shlex.split(self.tox_args))
        sys.exit(errno)

long_description = []

for text_file in ['README.rst', 'CHANGES.rst']:
    with open(join(dirname(abspath(__file__)), text_file), 'r') as f:
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
    cmdclass={'test': ToxTestCommand},
    include_package_data=True,
    keywords='django forms extensions sqlalchemy acl',
)
