# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack


import os
import sys
import re
import shutil
import subprocess
import fileinput
import sys
import subprocess

from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand
import setuptools
from distutils.spawn import find_executable

ROOT_PATH = os.path.dirname(os.path.realpath(__file__))
SOURCE_PATH = os.path.join(ROOT_PATH, 'source')
README_PATH = os.path.join(ROOT_PATH, 'README.md')

RESOURCE_PATH = os.path.join(ROOT_PATH, 'resource')
STYLE_PATH = os.path.join(RESOURCE_PATH, 'style')
RESOURCE_TARGET_PATH = os.path.join(
    SOURCE_PATH, 'ftrack_connect_pipeline_qt', 'ui', 'resource.py'
)
BOOTSTRAP_PATH = os.path.join(RESOURCE_PATH, 'bootstrap')
PLUGINS_PATH = os.path.join(RESOURCE_PATH, 'plugins')
DEFINITIONS_PATH = os.path.join(RESOURCE_PATH, 'definitions')

HOOK_PATH = os.path.join(ROOT_PATH, 'hook')

BUILD_PATH = os.path.join(ROOT_PATH, 'build')


# Custom commands.
class BuildResources(setuptools.Command):
    '''Build additional resources.'''

    user_options = []

    def initialize_options(self):
        '''Configure default options.'''

    def finalize_options(self):
        '''Finalize options to be used.'''
        self.sass_path = os.path.join(STYLE_PATH, 'sass')
        self.css_path = STYLE_PATH
        self.resource_source_path = os.path.join(STYLE_PATH, 'resource.qrc')
        self.resource_target_path = RESOURCE_TARGET_PATH

    def _replace_imports_(self):
        '''Replace imports in resource files to Qt instead of QtCore.

        This allows the resource file to work with many different versions of
        Qt.

        '''
        replace = r'from Qt import QtCore'
        for line in fileinput.input(
            self.resource_target_path, inplace=True, mode='r'
        ):
            if r'import QtCore' in line:
                # Calling print will yield a new line in the resource file.
                sys.stdout.write(line.replace(line, replace))
            else:
                sys.stdout.write(line)

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


class BuildPlugin(setuptools.Command):
    '''Build plugin.'''

    description = 'Download dependencies and build plugin .'

    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        self.run_command('build_resources')

        '''Run the build step.'''
        import setuptools_scm

        release = setuptools_scm.get_version(version_scheme='post-release')
        VERSION = '.'.join(release.split('.')[:3])
        global STAGING_PATH
        STAGING_PATH = os.path.join(
            BUILD_PATH, 'ftrack-connect-pipeline-qt-{}'.format(VERSION)
        )

        '''Run the build step.'''
        # Clean staging path
        shutil.rmtree(STAGING_PATH, ignore_errors=True)

        # Copy resource files except style
        # bootstrap
        shutil.copytree(
            BOOTSTRAP_PATH, os.path.join(STAGING_PATH, 'resource', 'bootstrap')
        )
        # plugins
        shutil.copytree(
            PLUGINS_PATH, os.path.join(STAGING_PATH, 'resource', 'plugins')
        )
        # definitions
        shutil.copytree(
            DEFINITIONS_PATH,
            os.path.join(STAGING_PATH, 'resource', 'definitions'),
        )

        # Copy plugin files
        shutil.copytree(HOOK_PATH, os.path.join(STAGING_PATH, 'hook'))
        dependencies_path = os.path.join(STAGING_PATH, 'dependencies')

        os.makedirs(dependencies_path)

        subprocess.check_call(
            [
                sys.executable,
                '-m',
                'pip',
                'install',
                '.',
                '--target',
                dependencies_path,
            ]
        )

        shutil.make_archive(
            os.path.join(
                BUILD_PATH, 'ftrack-connect-pipeline-qt-{0}'.format(VERSION)
            ),
            'zip',
            STAGING_PATH,
        )


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


version_template = '''
# :coding: utf-8
# :copyright: Copyright (c) 2017-2020 ftrack

__version__ = {version!r}
'''


# Configuration.
setup(
    name='ftrack-connect-pipeline-qt',
    description='Ftrack qt pipeline integration framework.',
    long_description=open(README_PATH).read(),
    keywords='ftrack',
    url='https://bitbucket.org/ftrack/ftrack-connect-pipeline-qt',
    author='ftrack',
    author_email='support@ftrack.com',
    license='Apache License (2.0)',
    packages=find_packages(SOURCE_PATH),
    package_dir={'': 'source'},
    use_scm_version={
        'write_to': 'source/ftrack_connect_pipeline_qt/_version.py',
        'write_to_template': version_template,
        'version_scheme': 'post-release',
    },
    python_requires='<3.10',
    setup_requires=[
        'PySide2 == 5.12.6',
        'Qt.py >=1.0.0, < 2',
        'pyScss >= 1.2.0, < 2',
        'sphinx >= 1.8.5, < 4',
        'sphinx_rtd_theme >= 0.1.6, < 2',
        'lowdown >= 0.1.0, < 2',
        'setuptools >= 44.0.0',
        'setuptools_scm',
    ],
    install_requires=['Qt.py >=1.0.0, < 2'],
    tests_require=['pytest >= 2.3.5, < 3'],
    cmdclass={
        'test': PyTest,
        'build_plugin': BuildPlugin,
        'build_resources': BuildResources,
        'test': PyTest,
    },
    zip_safe=False,
)
