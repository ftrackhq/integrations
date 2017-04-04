# :coding: utf-8
# :copyright: Copyright (c) 2015 ftrack

import os
import sys
import re
import glob
import shutil
import pip
import tempfile
import fileinput

from setuptools import setup, find_packages, Command
from setuptools.command.test import test as TestCommand


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
    BUILD_PATH, 'plugin'
)

README_PATH = os.path.join(ROOT_PATH, 'README.rst')

with open(os.path.join(
    SOURCE_PATH, 'ftrack_connect_rv', '_version.py')
) as _version_file:
    VERSION = re.match(
        r'.*__version__ = \'(.*?)\'', _version_file.read(), re.DOTALL
    ).group(1)


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

    def _build_rvpkg(self):

        # build rvpkg

        # Copy plugin files
        self.copytree(
            RVPKG_SOURCE_PATH,
            self.rvpkg_staging,
        )

        # Strip off patch version from the tool: M.m rather than M.m.p
        rvpkg_version = '.'.join(VERSION.split('.')[:-1])
        plugin_name = 'ftrack-{0}'.format(rvpkg_version)

        staging_plugin_path = os.path.join(
            self.rvpkg_staging,
            plugin_name
        )

        destination_path = os.path.join(
            STAGING_PATH, 'package'
        )

        if not os.path.exists(destination_path):
            os.makedirs(destination_path)

        if not os.path.exists(os.path.join(self.rvpkg_staging, 'PACKAGE')):
            raise IOError('no PACKAGE file in {0}'.format(self.rvpkg_staging))

        package_file_path = os.path.join(self.rvpkg_staging, 'PACKAGE')
        package_file = fileinput.input(package_file_path, inplace=True)
        for line in package_file:
            if '{VERSION}' in line:
                sys.stdout.write(line.format(VERSION=VERSION))
            else:
                sys.stdout.write(line)

        # prepare zip with rv plugin
        shutil.make_archive(
            staging_plugin_path,
            'zip',
            self.rvpkg_staging
        )

        # rename to rvpkg and move in final destination
        source_file_path = staging_plugin_path + '.zip'
        destination_file_path = os.path.join(
            destination_path, plugin_name + '.rvpkg'
        )

        shutil.move(source_file_path, destination_file_path)

    def run(self):
        '''Run the build step.'''

        # Clean staging path.
        shutil.rmtree(STAGING_PATH, ignore_errors=True)
        pip.main(
            [
                'install',
                '.',
                '--target',
                os.path.join(self.rvpkg_staging, 'dependencies'),
                '--process-dependency-links'
            ]
        )

        # Add __init__.py in dependencies so we can use it as module.
        open(
            os.path.join(
                self.rvpkg_staging, 'dependencies', '__init__.py'
            ), 'a'
        )

        # Copy plugin files.
        shutil.copytree(
            HOOK_PATH,
            os.path.join(STAGING_PATH, 'hook')
        )

        self._build_rvpkg()

        # Build zip file for ftrack-connect-rv.
        shutil.make_archive(
            os.path.join(
                BUILD_PATH,
                'ftrack-connect-rv-{0}'.format(VERSION)
            ),
            'zip',
            STAGING_PATH
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
        'ftrack-location-compatibility >= 0.1.0',
        'ftrack-python-api >= 1, < 2',
    ],
    tests_require=[
        'pytest >= 2.3.5, < 3'
    ],
    cmdclass={
        'test': PyTest,
        'build_plugin': BuildPlugin,
    },
    dependency_links=[
        (
            'https://bitbucket.org/ftrack/ftrack-location-compatibility/get/0.1.0.zip'
            '#egg=ftrack-location-compatibility-0.1.0'
        )
    ],
    data_files=[
        (
            'ftrack_connect_rv_resource/hook',
            glob.glob(os.path.join(ROOT_PATH, 'resource', 'hook', '*.py'))
        )
    ]
)
