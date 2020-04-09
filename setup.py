# :coding: utf-8
# :copyright: Copyright (c) 2018 ftrack

import os
import sys
import re
import shutil
from pkg_resources import parse_version
import pip

if parse_version(pip.__version__) < parse_version('19.3.0'):
    raise ValueError('Pip should be version 19.3.0 or higher')

import subprocess
from pip._internal import main as pip_main

from setuptools import setup, find_packages, Command

import fileinput

ROOT_PATH = os.path.dirname(os.path.realpath(__file__))
SOURCE_PATH = os.path.join(ROOT_PATH, 'source')
README_PATH = os.path.join(ROOT_PATH, 'README.rst')
RESOURCE_PATH = os.path.join(ROOT_PATH, 'resource')
RESOURCE_TARGET_PATH = os.path.join(
    SOURCE_PATH, 'ftrack_connect_nuke_studio', 'resource.py'
)
HIERO_PLUGIN_PATH = os.path.join(RESOURCE_PATH, 'plugin')
BUILD_PATH = os.path.join(ROOT_PATH, 'build')
STAGING_PATH = os.path.join(BUILD_PATH, 'ftrack-connect-nuke-studio-plugin-{0}')
HOOK_PATH = os.path.join(RESOURCE_PATH, 'hook')
APPLICATION_HOOK_PATH = os.path.join(RESOURCE_PATH, 'application_hook')


# Read version from source.
with open(os.path.join(
    SOURCE_PATH, 'ftrack_connect_nuke_studio', '_version.py'
)) as _version_file:
    VERSION = re.match(
        r'.*__version__ = \'(.*?)\'', _version_file.read(), re.DOTALL
    ).group(1)


# ensure result plugin has the version set
STAGING_PATH = STAGING_PATH.format(VERSION)


# Custom commands.
class BuildResources(Command):
    '''Build additional resources.'''

    user_options = []

    def initialize_options(self):
        '''Configure default options.'''

    def finalize_options(self):
        '''Finalize options to be used.'''
        self.resource_source_path = os.path.join(
            RESOURCE_PATH, 'resource.qrc'
        )
        self.resource_target_path = RESOURCE_TARGET_PATH

    def _replace_imports_(self):
        '''Replace imports in resource files to QtExt instead of QtCore.

        This allows the resource file to work with many different versions of
        Qt.

        '''
        replace = 'from Qt import QtCore'
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
            pyside_rcc_command = 'pyside-rcc'

            # On Windows, pyside-rcc is not automatically available on the
            # PATH so try to find it manually.
            if sys.platform == 'win32':
                import PySide
                pyside_rcc_command = os.path.join(
                    os.path.dirname(PySide.__file__),
                    'pyside-rcc.exe'
                )

            subprocess.check_call([
                pyside_rcc_command,
                '-o',
                self.resource_target_path,
                self.resource_source_path
            ])
        except (subprocess.CalledProcessError, OSError) as error:
            raise RuntimeError(
                'Error compiling resource.py using pyside-rcc. Possibly '
                'pyside-rcc could not be found. You might need to manually add '
                'it to your PATH. See README for more information.'
                'error : {}'.format(error)
            )

        self._replace_imports_()


class BuildPlugin(Command):
    '''Build plugin.'''

    description = 'Download dependencies and build plugin .'

    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        '''Run the build step.'''
        # Clean staging path
        shutil.rmtree(STAGING_PATH, ignore_errors=True)

        # build resources
        self.run_command('build_resources')

        # Copy plugin files
        shutil.copytree(
            HIERO_PLUGIN_PATH,
            os.path.join(STAGING_PATH, 'resource')
        )

        # Copy hook files
        shutil.copytree(
            HOOK_PATH,
            os.path.join(STAGING_PATH, 'hook')
        )

        # Copy applipcation hooks files
        shutil.copytree(
            APPLICATION_HOOK_PATH,
            os.path.join(STAGING_PATH, 'application_hook')
        )

        pip_main.main(
            [
                'install',
                '.',
                '--target',
                os.path.join(STAGING_PATH, 'dependencies')
            ]
        )

        result_path = shutil.make_archive(
            os.path.join(
                BUILD_PATH,
                'ftrack-connect-nuke-studio-{0}'.format(VERSION)
            ),
            'zip',
            STAGING_PATH
        )

        print 'Result: ' + result_path


# Call main setup.
setup(
    name='ftrack-connect-nuke-studio',
    version=VERSION,
    description='ftrack integration with NUKE STUDIO.',
    long_description=open(README_PATH).read(),
    keywords='ftrack, integration, connect, the foundry, nuke, studio',
    url='https://bitbucket.org/ftrack/ftrack-connect-nuke-studio',
    author='ftrack',
    author_email='support@ftrack.com',
    license='Apache License (2.0)',
    packages=find_packages(SOURCE_PATH),
    package_dir={
        '': 'source'
    },
    setup_requires=[
        'sphinx >= 1.2.2, < 2',
        'sphinx_rtd_theme >= 0.1.6, < 2',
        'lowdown >= 0.1.0, < 1',
        'mock >= 1.3, < 2'
    ],
    install_requires=[
        'appdirs == 1.4.0',
        'lucidity >= 1.5, < 2',
        'opentimelineio ==0.11',
        'qt.py >=1.0.0, < 2'
    ],
    tests_require=[
    ],
    zip_safe=False,
    cmdclass={
        'build_plugin': BuildPlugin,
        'build_resources': BuildResources

    },
)
