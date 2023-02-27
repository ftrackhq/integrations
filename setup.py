# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack


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

RESOURCE_PATH = os.path.join(ROOT_PATH, 'resource')

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
            BUILD_PATH, 'ftrack-connect-pipeline-unreal-{}'.format(VERSION)
        )

        '''Run the build step.'''
        # Clean staging path
        shutil.rmtree(STAGING_PATH, ignore_errors=True)

        # Copy resource files
        shutil.copytree(RESOURCE_PATH, os.path.join(STAGING_PATH, 'resource'))

        # Copy plugin files
        shutil.copytree(HOOK_PATH, os.path.join(STAGING_PATH, 'hook'))

        subprocess.check_call(
            [
                sys.executable,
                '-m',
                'pip',
                'install',
                '.',
                '--target',
                os.path.join(STAGING_PATH, 'dependencies'),
            ]
        )

        result_path = shutil.make_archive(
            os.path.join(
                BUILD_PATH,
                'ftrack-connect-pipeline-unreal-{0}'.format(VERSION),
            ),
            'zip',
            STAGING_PATH,
        )

        print('Result: ' + result_path)


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
# :copyright: Copyright (c) 2014-2022 ftrack

__version__ = {version!r}
'''

# Configuration.
setup(
    name='ftrack-connect-pipeline-unreal',
    description='Unreal plugin enabling publish, open, load and asset management with ftrack eco system.',
    long_description=open(README_PATH).read(),
    keywords='ftrack',
    url='https://bitbucket.org/ftrack/ftrack-connect-pipeline-unreal',
    author='ftrack',
    author_email='support@ftrack.com',
    license='Apache License (2.0)',
    packages=find_packages(SOURCE_PATH),
    package_dir={'': 'source'},
    use_scm_version={
        'write_to': 'source/ftrack_connect_pipeline_unreal/_version.py',
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
    install_requires=['PySide2', 'Qt.py'],
    tests_require=['pytest >= 2.3.5, < 3'],
    cmdclass={'test': PyTest, 'build_plugin': BuildPlugin},
    zip_safe=False,
)
