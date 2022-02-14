# :coding: utf-8
# :copyright: Copyright (c) 2015 ftrack

import os
import sys
import re
import shutil

from setuptools import Command
import subprocess

from setuptools import find_packages, setup

PLUGIN_NAME = 'ftrack-connect-plugin-manager-{}'

ROOT_PATH = os.path.dirname(os.path.realpath(__file__))

RESOURCE_PATH = os.path.join(ROOT_PATH, 'resource')

SOURCE_PATH = os.path.join(ROOT_PATH, 'source')

README_PATH = os.path.join(ROOT_PATH, 'README.rst')

BUILD_PATH = os.path.join(ROOT_PATH, 'build')

STAGING_PATH = os.path.join(BUILD_PATH, PLUGIN_NAME)

HOOK_PATH = os.path.join(RESOURCE_PATH, 'hook')

version_template = '''
# :coding: utf-8
# :copyright: Copyright (c) 2014-2021 ftrack

__version__ = {version!r}
'''


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
                PLUGIN_NAME.format(VERSION)
            ),
            'zip',
            STAGING_PATH
        )


# Configuration.
setup(
    name='ftrack-connect-plugin-manager',
    description='Base Class for handling application startup.',
    long_description=open(README_PATH).read(),
    keywords='ftrack',
    url='https://bitbucket.org/ftrack-integrations/ftrack-connect-plugin-manager',
    author='ftrack',
    author_email='support@ftrack.com',
    license='Apache License (2.0)',
    packages=find_packages(SOURCE_PATH),
    package_dir={'': 'source'},
    setup_requires=[
        'sphinx >= 1.8.5, < 4',
        'sphinx_rtd_theme >= 0.1.6, < 2',
        'lowdown >= 0.1.0, < 2',
        'setuptools>=45.0.0',
        'setuptools_scm'
    ],
    tests_require=['pytest >= 2.3.5, < 3'],
    use_scm_version={
        'write_to': 'source/ftrack_connect_plugin_manager/_version.py',
        'write_to_template': version_template,
        'version_scheme': 'post-release'
    },
    classifiers=[
        'License :: OSI Approved :: Apache Software License',
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 3'
    ],
    cmdclass={'build_plugin': BuildPlugin},
    zip_safe=False,
    python_requires=">=3, <4"
)