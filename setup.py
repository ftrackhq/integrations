# :coding: utf-8

import os
import re
import glob
import shutil
try:
    from pip._internal import main as pip_main
except ImportError:
    print 'Please update to latest pip version'

from setuptools import setup, find_packages
import setuptools

ROOT_PATH = os.path.dirname(os.path.realpath(__file__))
SOURCE_PATH = os.path.join(ROOT_PATH, 'source')
README_PATH = os.path.join(ROOT_PATH, 'README.rst')
RESOURCE_PATH = os.path.join(ROOT_PATH, 'resource')

HIERO_PLUGIN_PATH = os.path.join(RESOURCE_PATH,'plugin')
BUILD_PATH = os.path.join(ROOT_PATH, 'build')
STAGING_PATH = os.path.join(BUILD_PATH, 'plugin')
HOOK_PATH = os.path.join(RESOURCE_PATH, 'hook')

# Read version from source.
with open(os.path.join(
    SOURCE_PATH, 'ftrack_connect_nuke_studio_beta', '_version.py'
)) as _version_file:
    VERSION = re.match(
        r'.*__version__ = \'(.*?)\'', _version_file.read(), re.DOTALL
    ).group(1)


connect_dependency_link = (
    'https://bitbucket.org/ftrack/ftrack-connect/get/1.1.4.zip'
    '#egg=ftrack-connect-1.1.4'
)


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
        # Clean staging path
        shutil.rmtree(STAGING_PATH, ignore_errors=True)

        # Copy plugin files
        shutil.copytree(
            HIERO_PLUGIN_PATH,
            os.path.join(STAGING_PATH, 'resource')
        )

        # Copy plugin files
        shutil.copytree(
            HOOK_PATH,
            os.path.join(STAGING_PATH, 'hook')
        )

        pip_main(
            [
                'install',
                '.',
                '--target',
                os.path.join(STAGING_PATH, 'dependencies'),
                '--process-dependency-links'
            ]
        )

        result_path = shutil.make_archive(
            os.path.join(
                BUILD_PATH,
                'ftrack-connect-nuke-studio-beta-{0}'.format(VERSION)
            ),
            'zip',
            STAGING_PATH
        )

        print 'Result: ' + result_path



# Call main setup.
setup(
    name='ftrack-connect-nuke-studio-beta',
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
        'ftrack-python-api >= 1, < 2',
        'lucidity >= 1.5, < 2'
    ],
    dependency_links=[
        connect_dependency_link
    ],
    tests_require=[
    ],
    zip_safe=False,
    cmdclass={
        'build_plugin': BuildPlugin
    },
)
