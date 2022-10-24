# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack


import os
import re
import sys
import subprocess
import shutil

from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand
import setuptools


ROOT_PATH = os.path.dirname(os.path.realpath(__file__))
SOURCE_PATH = os.path.join(ROOT_PATH, 'source')
README_PATH = os.path.join(ROOT_PATH, 'README.md')


HOOK_PATH = os.path.join(ROOT_PATH, 'hook')

BUILD_PATH = os.path.join(ROOT_PATH, 'build')


class BuildPlugin(setuptools.Command):
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
        VERSION = '.'.join(release.split('.')[:3])
        global STAGING_PATH
        STAGING_PATH = os.path.join(
            BUILD_PATH, 'ftrack-connect-pipeline-{}'.format(VERSION)
        )

        '''Run the build step.'''
        # Clean staging path
        shutil.rmtree(STAGING_PATH, ignore_errors=True)

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

        result_path = shutil.make_archive(
            os.path.join(
                BUILD_PATH, 'ftrack-connect-pipeline-{0}'.format(VERSION)
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
    name='ftrack-connect-pipeline',
    description='Ftrack core pipeline integration framework.',
    long_description=open(README_PATH).read(),
    keywords='ftrack',
    url='https://bitbucket.org/ftrack/ftrack-connect-pipeline',
    author='ftrack',
    author_email='support@ftrack.com',
    license='Apache License (2.0)',
    packages=find_packages(SOURCE_PATH),
    package_dir={'': 'source'},
    use_scm_version={
        'write_to': 'source/ftrack_connect_pipeline/_version.py',
        'write_to_template': version_template,
        'version_scheme': 'post-release',
    },
    python_requires='<3.10',
    setup_requires=[
        'sphinx >= 1.8.5, < 4',
        'sphinx_rtd_theme >= 0.1.6, < 2',
        'lowdown >= 0.1.0, < 2',
        'setuptools>=44.0.0',
        'setuptools_scm',
    ],
    install_requires=[
        'ftrack-python-api >= 1, < 3',  # == 2.0RC1
        'future >=0.16.0, < 1',
        'six >= 1, < 2',
        'jsonschema==2.6.0',
        'appdirs',
        'python_jsonschema_objects <= 0.3.12',
        'jsonref',
        'markdown<=3.2.2',
        # Keep importlib-metadata it low, otherwise python_jsonschema_objects
        # build on python 3.7.12 will not work on maya 2022
        'importlib-metadata<5.0',
    ],
    tests_require=['mock', 'pytest >= 2.3.5, < 3'],
    cmdclass={'test': PyTest, 'build_plugin': BuildPlugin},
    zip_safe=False,
)
