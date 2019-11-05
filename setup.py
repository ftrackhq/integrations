# :coding: utf-8
# :copyright: Copyright (c) 2015 ftrack

import os
import sys
import re
import glob
import shutil

import tempfile
import fileinput

from setuptools import setup, find_packages, Command
from setuptools.command.test import test as TestCommand
from pkg_resources import parse_version
import pip

if parse_version(pip.__version__) < parse_version('19.3.0'):
    raise ValueError('Pip should be version 19.3.0 or higher')

from pip._internal import main as pip_main

FTRACK_LOCATION_COMPATIBILITY = '0.3.3'

PLUGIN_NAME = 'ftrack-connect-rv-{0}'

ROOT_PATH = os.path.dirname(
    os.path.realpath(__file__)
)

RESOURCE_PATH = os.path.join(
    ROOT_PATH, 'resource'
)

HOOK_PATH = os.path.join(
    RESOURCE_PATH, 'hook'
)


SOURCE_PATH = os.path.join(
    ROOT_PATH, 'source'
)

RVPKG_SOURCE_PATH = os.path.join(
    RESOURCE_PATH, 'plugin'
)

BUILD_PATH = os.path.join(
    ROOT_PATH, 'build'
)

STAGING_PATH = os.path.join(
    BUILD_PATH, PLUGIN_NAME
)

README_PATH = os.path.join(ROOT_PATH, 'README.rst')

with open(os.path.join(
    SOURCE_PATH, 'ftrack_connect_rv', '_version.py')
) as _version_file:
    VERSION = re.match(
        r'.*__version__ = \'(.*?)\'', _version_file.read(), re.DOTALL
    ).group(1)

# Update staging path with the plugin version
STAGING_PATH = STAGING_PATH.format(VERSION)

class BuildPlugin(Command):
    '''Build plugin.'''
    description = 'Download dependencies and build plugin .'
    user_options = []

    def copytree(self, src, dst, symlinks=False, ignore=None):
        for item in os.listdir(src):
            s = os.path.join(src, item)
            d = os.path.join(dst, item)
            if os.path.isdir(s):
                shutil.copytree(s, d, symlinks, ignore)
            else:
                shutil.copy2(s, d)

    def initialize_options(self):
        '''Initialize options.'''
        self.rvpkg_staging = os.path.join(tempfile.mkdtemp(), 'rvpkg')

    def finalize_options(self):
        '''Finalize options.'''
        pass

    def _build_release(self):
        '''Copy the hook and the source code.'''

        # Copy hooks.
        shutil.copytree(
            HOOK_PATH,
            os.path.join(STAGING_PATH, 'hook')
        )

        # Copy sources.
        shutil.copytree(
            SOURCE_PATH,
            os.path.join(
                STAGING_PATH, 'dependencies'
            )
        )

    def _build_release_zip(self):
        '''Build zip file for ftrack-connect-rv.'''

        shutil.make_archive(
            os.path.join(
                BUILD_PATH,
                PLUGIN_NAME.format(VERSION)
            ),
            'zip',
            STAGING_PATH
        )

    def _build_rvpkg(self):
        '''Build rv plugin package.'''

        # Copy plugin files
        self.copytree(
            RVPKG_SOURCE_PATH,
            self.rvpkg_staging,
        )

        # Strip off patch version from the tool: M.m rather than M.m.p
        rvpkg_version = '.'.join(VERSION.split('.'))
        plugin_name = 'ftrack-{0}'.format(rvpkg_version)

        plugin_destination_path = BUILD_PATH

        if not os.path.exists(plugin_destination_path):
            os.makedirs(plugin_destination_path)

        if not os.path.exists(os.path.join(self.rvpkg_staging, 'PACKAGE')):
            raise IOError('no PACKAGE file in {0}'.format(self.rvpkg_staging))

        package_file_path = os.path.join(self.rvpkg_staging, 'PACKAGE')
        package_file = fileinput.input(package_file_path, inplace=True)
        for line in package_file:
            if '{VERSION}' in line:
                sys.stdout.write(line.format(VERSION=VERSION))
            else:
                sys.stdout.write(line)

        zip_destination_file_path = os.path.join(
            plugin_destination_path, plugin_name
        )

        rvpkg_destination_file_path = os.path.join(
            plugin_destination_path, plugin_name + '.rvpkg'
        )

        # prepare zip with rv plugin
        zip_name = shutil.make_archive(
            base_name=zip_destination_file_path,
            format='zip',
            root_dir=self.rvpkg_staging
        )

        shutil.move(
            zip_name,
            rvpkg_destination_file_path
        )

    def run(self):
        '''Run the build step.'''

        # Clean staging path.
        shutil.rmtree(STAGING_PATH, ignore_errors=True)
        pip_main.main(
            [
                'install',
                '.',
                '--target',
                os.path.join(self.rvpkg_staging, 'dependencies')
            ]
        )

        shutil.make_archive(
            os.path.join(self.rvpkg_staging, 'dependencies'),
            'zip',
            os.path.join(self.rvpkg_staging, 'dependencies')
        )
        shutil.rmtree(os.path.join(self.rvpkg_staging, 'dependencies'))

        # Build rv plugin.
        self._build_rvpkg()
        # Build source code and hooks.
        self._build_release()
        # Prepare the final zip with release version.
        self._build_release_zip()


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


# Configuration.
setup(
    name='ftrack-connect-rv',
    version=VERSION,
    description='Repository for ftrack connect rv.',
    long_description=open(README_PATH).read(),
    keywords='',
    url='https://bitbucket.org/ftrack/ftrack-connect-rv',
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
    ],
    install_requires=[
        'ftrack-python-api >= 1, < 2',
        'appdirs == 1.4.0',
        (
            'ftrack-location-compatibility @ https://bitbucket.org/'
            'ftrack/ftrack-location-compatibility/get/{0}.zip#egg='
            'ftrack-location-compatibility-{0}'
        ).format(FTRACK_LOCATION_COMPATIBILITY)
    ],
    tests_require=[
        'pytest >= 2.3.5, < 3'
    ],
    cmdclass={
        'test': PyTest,
        'build_plugin': BuildPlugin,
    },
    data_files=[
        (
            'ftrack_connect_rv_resource/hook',
            glob.glob(os.path.join(ROOT_PATH, 'resource', 'hook', '*.py'))
        )
    ]
)
