# :coding: utf-8
# :copyright: Copyright (c) 2022 ftrack

import os
import re
import shutil
import sys

from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand

from setuptools import Command
import subprocess

ROOT_PATH = os.path.dirname(os.path.realpath(__file__))
SOURCE_PATH = os.path.join(ROOT_PATH, 'source')
README_PATH = os.path.join(ROOT_PATH, 'README.md')
BUILD_PATH = os.path.join(ROOT_PATH, 'dist')
STAGING_PATH = os.path.join(BUILD_PATH, 'ftrack-connect-timetracker-widget-{}')
RESOURCE_PATH = os.path.join(ROOT_PATH, 'resource')
HOOK_PATH = os.path.join(RESOURCE_PATH, 'hook')


version_template = '''
# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

__version__ = {version!r}
'''


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
        import setuptools_scm
        release = setuptools_scm.get_version(version_scheme='post-release')
        print(release)
        VERSION = '.'.join(release.split('.')[:3])
        global STAGING_PATH
        STAGING_PATH = STAGING_PATH.format(VERSION)

        '''Run the build step.'''
        # Clean staging path
        shutil.rmtree(STAGING_PATH, ignore_errors=True)

        # Copy hook files
        shutil.copytree(
            HOOK_PATH,
            os.path.join(STAGING_PATH, 'hook')
        )

        # Install local dependencies
        subprocess.check_call(
            [
                sys.executable, '-m', 'pip', 'install', '.', '--target',
                os.path.join(STAGING_PATH, 'dependencies')
            ]
        )
        print(VERSION)

        # Generate plugin zip
        shutil.make_archive(
            os.path.join(
                BUILD_PATH,
                'ftrack-connect-timetracker-widget-{}'.format(VERSION)
            ),
            'zip',
            STAGING_PATH
        )


def get_version():
    '''Read version from _version.py'''
    version_path = os.path.join(SOURCE_PATH, 'ftrack_connect_timetracker_widget', '_version.py')
    with open(version_path, 'r') as file_handle:
        for line in file_handle.readlines():
            if line.find('__version__') > -1:
                return re.findall(r'\'(.*)\'', line)[0].strip()
    raise ValueError('Could not find version in {0}'.format(version_path))

# Configuration.
setup(
    name='ftrack-connect-timetracker-widget',
    description='ftrack connect time tracker widget',
    long_description=open(README_PATH).read(),
    keywords='ftrack',
    url='https://github.com/ftrackhq/integrations/projects/connect-timetracker-widget',
    author='ftrack',
    author_email='support@ftrack.com',
    license='Apache License (2.0)',
    packages=find_packages(SOURCE_PATH),
    package_dir={'': 'source'},
    package_data={"": ["{}/**/*.*".format(RESOURCE_PATH)]},
    version="0.5.1",
    setup_requires=[
        'sphinx >= 1.8.5, < 4',
        'sphinx_rtd_theme >= 0.1.6, < 2',
        'lowdown >= 0.1.0, < 2',
        'setuptools>=45.0.0',
        'setuptools_scm'
    ],
    install_requires=[
    ],
    tests_require=[
        'pytest >= 2.3.5, < 3'
    ],
    classifiers=[
        'License :: OSI Approved :: Apache Software License',
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 3'
    ],
    cmdclass={
        'build_plugin': BuildPlugin,
        'test': PyTest
    },
    zip_safe=False,
    python_requires=">=3, <4"
)