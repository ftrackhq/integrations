# :coding: utf-8
# :copyright: Copyright (c) 2016 ftrack

import os
import sys
import re
import subprocess
import fileinput

from setuptools import setup, find_packages, Command
from distutils.command.build import build as BuildCommand
from setuptools.command.bdist_egg import bdist_egg as BuildEggCommand
from setuptools.command.test import test as TestCommand


ROOT_PATH = os.path.dirname(os.path.realpath(__file__))
SOURCE_PATH = os.path.join(ROOT_PATH, 'source')
README_PATH = os.path.join(ROOT_PATH, 'README.rst')
RESOURCE_PATH = os.path.join(
    ROOT_PATH, 'resource'
)
RESOURCE_TARGET_PATH = os.path.join(
    SOURCE_PATH, 'ftrack_connect_pipeline', 'ui', 'resource.py'
)

# Read version from source.
with open(os.path.join(
    SOURCE_PATH, 'ftrack_connect_pipeline', '_version.py')
) as _version_file:
    VERSION = re.match(
        r'.*__version__ = \'(.*?)\'', _version_file.read(), re.DOTALL
    ).group(1)


# Custom commands.
class PyTest(TestCommand):
    '''Pytest command.'''

    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        '''Import pytest and run.'''
        import pytest
        errno = pytest.main(self.test_args)
        raise SystemExit(errno)


# Custom commands.
class BuildResources(Command):
    '''Build additional resources.'''

    user_options = []

    def initialize_options(self):
        '''Configure default options.'''

    def finalize_options(self):
        '''Finalize options to be used.'''
        self.sass_path = os.path.join(RESOURCE_PATH, 'sass')
        self.css_path = RESOURCE_PATH
        self.resource_source_path = os.path.join(
            RESOURCE_PATH, 'resource.qrc'
        )
        self.resource_target_path = RESOURCE_TARGET_PATH

    def _replace_imports_(self):
        '''Replace imports in resource files to QtExt instead of QtCore.

        This allows the resource file to work with many different versions of
        Qt.

        '''
        replace = 'from QtExt import QtCore'
        for line in fileinput.input(self.resource_target_path, inplace=True):
            if 'import QtCore' in line:
                # Calling print will yield a new line in the resource file.
                print line.replace(line, replace)
            else:
                # Calling print will yield a new line in the resource file.
                print line

    def run(self):
        '''Run build.'''
        try:
            import scss
        except ImportError:
            raise RuntimeError(
                'Error compiling sass files. Could not import "scss". '
                'Check you have the pyScss Python package installed.'
            )

        compiler = scss.Scss(
            search_paths=[self.sass_path]
        )

        themes = [
            'style_dark'
        ]

        for theme in themes:
            scss_source = os.path.join(self.sass_path, '{0}.scss'.format(theme))
            css_target = os.path.join(self.css_path, '{0}.css'.format(theme))

            compiled = compiler.compile(
                scss_file=scss_source
            )
            with open(css_target, 'w') as file_handle:
                file_handle.write(compiled)
                print('Compiled {0}'.format(css_target))

        try:
            import PySide
            pyside_rcc_command = os.path.join(
                os.path.dirname(PySide.__file__),
                'pyside-rcc'
            )

            # On Windows, pyside-rcc is not automatically available on the
            # PATH so try to find it manually.
            if sys.platform == 'win32':
                pyside_rcc_command += '.exe'

            subprocess.check_call([
                pyside_rcc_command,
                '-o',
                self.resource_target_path,
                self.resource_source_path
            ])
        except (subprocess.CalledProcessError, OSError):
            raise RuntimeError(
                'Error compiling resource.py using pyside-rcc. Possibly '
                'pyside-rcc could not be found. You might need to manually add '
                'it to your PATH. See README for more information.'
            )

        self._replace_imports_()


class BuildEgg(BuildEggCommand):
    '''Custom egg build to ensure resources built.

    .. note::

        Required because when this project is a dependency for another project,
        only bdist_egg will be called and *not* build.

    '''

    def run(self):
        '''Run egg build ensuring build_resources called first.'''
        self.run_command('build_resources')
        BuildEggCommand.run(self)


class Build(BuildCommand):
    '''Custom build to pre-build resources.'''

    def run(self):
        '''Run build ensuring build_resources called first.'''
        self.run_command('build_resources')
        BuildCommand.run(self)


# Configuration.
setup(
    name='ftrack-connect-pipeline',
    version=VERSION,
    description='Common building blocks for building pipeline development',
    long_description=open(README_PATH).read(),
    keywords='ftrack',
    url='https://bitbucket.org/ftrack/ftrack-connect-pipeline',
    author='ftrack',
    author_email='support@ftrack.com',
    license='Apache License (2.0)',
    packages=find_packages(SOURCE_PATH),
    package_dir={
        '': 'source'
    },
    setup_requires=[
        'qtext',
        'pyScss >= 1.2.0, < 2',
        'PySide >= 1.2.2, < 2',
    ],
    build_sphinx_requires=[
        'sphinx >= 1.2.2, < 2',
        'sphinx_rtd_theme >= 0.1.6, < 2',
        'lowdown >= 0.1.0, < 2'
    ],
    build_resources_requires=[
        'qtext'
        'pyScss >= 1.2.0, < 2'
    ],
    install_requires=[
        'appdirs == 1.4.0',
        'qtext'
    ],
    tests_require=[
        'pytest >= 2.3.5, < 3',
        'PySide == 1.2.2',
        'ftrack-python-api',
        'pyblish-base'
    ],
    cmdclass={
        'build': Build,
        'bdist_egg': BuildEgg,
        'build_resources': BuildResources,
        'test': PyTest
    },
    dependency_links=[
        'git+https://bitbucket.org/ftrack/qtext/get/0.1.0.zip#egg=QtExt-0.1.0'
    ],
    zip_safe=False
)
