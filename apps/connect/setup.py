# :coding: utf-8
# :copyright: Copyright (c) 2014 ftrack

import sys
import os
import subprocess
import re
import glob
import shutil

from pkg_resources import parse_version
from setuptools import setup, find_packages, Command
from distutils.command.build import build as BuildCommand
from setuptools.command.bdist_egg import bdist_egg as BuildEggCommand
from distutils.command.clean import clean as CleanCommand
from setuptools.command.test import test as TestCommand
import distutils.dir_util
import distutils
import fileinput
from distutils.spawn import find_executable
from pkg_resources import get_distribution, DistributionNotFound


ROOT_PATH = os.path.dirname(os.path.realpath(__file__))

RESOURCE_PATH = os.path.join(ROOT_PATH, 'resource')

SOURCE_PATH = os.path.join(ROOT_PATH, 'source')

DISTRIBUTION_PATH = os.path.join(ROOT_PATH, 'dist')

RESOURCE_TARGET_PATH = os.path.join(
    SOURCE_PATH, 'ftrack_connect', 'ui', 'resource.py'
)

README_PATH = os.path.join(os.path.dirname(__file__), 'README.md')
PACKAGES_PATH = os.path.join(os.path.dirname(__file__), 'source')

FONTS_PATH = os.path.join(RESOURCE_PATH, 'font')
FONTS_TARGET_PATH = os.path.join(SOURCE_PATH, 'ftrack_connect', 'fonts')


# Read version from source.
try:
    release = get_distribution('ftrack-connect').version
    # take major/minor/patch
    VERSION = '.'.join(release.split('.')[:3])
except DistributionNotFound:
    # package is not installed
    VERSION = 'Unknown version'


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
        self.resource_source_path = os.path.join(RESOURCE_PATH, 'resource.qrc')
        self.resource_target_path = RESOURCE_TARGET_PATH

    def _replace_imports_(self):
        '''Replace imports in resource files to Qt instead of QtCore.

        This allows the resource file to work with many different versions of
        Qt.

        '''
        replace = r'from ftrack_connect.qt import QtCore'
        for line in fileinput.input(
            self.resource_target_path, inplace=True, mode='r'
        ):
            if r'import QtCore' in line:
                # Calling print will yield a new line in the resource file.
                sys.stdout.write(line.replace(line, replace))
            else:
                sys.stdout.write(line)

    def _copy_fonts(self):
        if os.path.exists(FONTS_TARGET_PATH):
            shutil.rmtree(FONTS_TARGET_PATH)

        shutil.copytree(FONTS_PATH, FONTS_TARGET_PATH)

    def run(self):
        '''Run build.'''
        try:
            import scss
        except ImportError:
            raise RuntimeError(
                'Error compiling sass files. Could not import "scss". '
                'Check you have the pyScss Python package installed.'
            )

        compiler = scss.Scss(search_paths=[self.sass_path])

        themes = ['style_light', 'style_dark']
        for theme in themes:
            scss_source = os.path.join(
                self.sass_path, '{0}.scss'.format(theme)
            )
            css_target = os.path.join(self.css_path, '{0}.css'.format(theme))

            compiled = compiler.compile(scss_file=scss_source)
            with open(css_target, 'w') as file_handle:
                file_handle.write(compiled)
                print('Compiled {0}'.format(css_target))

        try:
            pyside_rcc_command = 'pyside2-rcc'
            executable = None

            # Check if the command for pyside*-rcc is in executable paths.
            if find_executable(pyside_rcc_command):
                executable = pyside_rcc_command

            if not executable:
                raise IOError('Not executable found for pyside2-rcc ')

            # Use the first occurrence if more than one is found.
            cmd = [
                executable,
                '-o',
                self.resource_target_path,
                self.resource_source_path,
            ]
            print('running : {}'.format(cmd))
            subprocess.check_call(cmd)

        except (subprocess.CalledProcessError, OSError):
            raise RuntimeError(
                'Error compiling resource.py using pyside-rcc. Possibly '
                'pyside-rcc could not be found. You might need to manually add '
                'it to your PATH. See README for more information.'
            )

        self._replace_imports_()
        self._copy_fonts()


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


class Clean(CleanCommand):
    '''Custom clean to remove built resources and distributions.'''

    def run(self):
        '''Run clean.'''
        relative_resource_path = os.path.relpath(
            RESOURCE_TARGET_PATH, ROOT_PATH
        )
        if os.path.exists(relative_resource_path):
            os.remove(relative_resource_path)
        else:
            distutils.log.warn(
                '\'{0}\' does not exist -- can\'t clean it'.format(
                    relative_resource_path
                )
            )

        if self.all:
            relative_distribution_path = os.path.relpath(
                DISTRIBUTION_PATH, ROOT_PATH
            )
            if os.path.exists(relative_distribution_path):
                distutils.dir_util.remove_tree(
                    relative_distribution_path, dry_run=self.dry_run
                )
            else:
                distutils.log.warn(
                    '\'{0}\' does not exist -- can\'t clean it'.format(
                        relative_distribution_path
                    )
                )

        CleanCommand.run(self)


class PyTest(TestCommand):
    '''Pytest command.'''

    def finalize_options(self):
        '''Finalize options to be used.'''
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        '''Import pytest and run.'''
        import pytest

        raise SystemExit(pytest.main(self.test_args))


version_template = '''
# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

__version__ = {version!r}
'''

# General configuration.
configuration = dict(
    name='ftrack-connect',
    description='Core for ftrack connect.',
    long_description=open(README_PATH).read(),
    keywords='ftrack, connect, publish',
    url='https://bitbucket.org/ftrack/ftrack-connect',
    author='ftrack',
    author_email='support@ftrack.com',
    license='Apache License (2.0)',
    packages=find_packages(PACKAGES_PATH),
    include_package_data=True,
    use_scm_version={
        'write_to': 'source/ftrack_connect/_version.py',
        'write_to_template': version_template,
        'version_scheme': 'post-release',
    },
    package_dir={'': 'source'},
    setup_requires=[
        'PySide2 >=5, <6',
        'Qt.py >=1.0.0, < 2',
        'pyScss >= 1.2.0, < 2',
        'sphinx >= 1.8.5, < 4',
        'sphinx_rtd_theme >= 0.1.6, < 1',
        'lowdown >= 0.1.0, < 1',
        'setuptools>=45.0.0',
        'setuptools_scm',
    ],
    install_requires=[
        'clique==1.6.1',
        'PySide2 >=5, <6',
        'Riffle >= 1.0.1',
        'ftrack-python-api',
        'arrow >= 0.4.6, < 1',
        'appdirs >= 1.4, < 1.5',
        'requests >= 2, <3',
        'lowdown >= 0.1.0, < 1',
        'Qt.py >=1.0.0, < 2',
        'qtawesome',
    ],
    tests_require=['pytest >= 2.3.5, < 3'],
    cmdclass={
        'build': Build,
        'build_ext': Build,
        'build_resources': BuildResources,
        'bdist_egg': BuildEgg,
        'clean': Clean,
        'test': PyTest,
    },
    entry_points={
        'console_scripts': [
            'ftrack-connect = ftrack_connect.__main__:main',
        ],
    },
    options={},
    data_files=[
        (
            'ftrack_connect_resource/hook',
            [
                os.path.relpath(path)
                for path in glob.glob(
                    os.path.join(RESOURCE_PATH, 'hook', '*.py')
                )
            ],
        ),
    ],
    zip_safe=False,
    python_requires=">=3, <4.0",
)


# Call main setup.
setup(**configuration)
