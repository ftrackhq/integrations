# :coding: utf-8

import os
import re
import glob
import shutil
from pip._internal import main as pip_main

from setuptools import setup, find_packages
import setuptools

ROOT_PATH = os.path.dirname(os.path.realpath(__file__))
SOURCE_PATH = os.path.join(ROOT_PATH, 'source')
README_PATH = os.path.join(ROOT_PATH, 'README.rst')
RESOURCE_PATH = os.path.join(ROOT_PATH, 'resource')

BUILD_PATH = os.path.join(ROOT_PATH, 'build')
STAGING_PATH = os.path.join(BUILD_PATH, 'plugin')
HOOK_PATH = os.path.join(RESOURCE_PATH, 'hook')

# Read version from source.
with open(os.path.join(
    SOURCE_PATH, 'ftrack_connect_nuke_studio', '_version.py'
)) as _version_file:
    VERSION = re.match(
        r'.*__version__ = \'(.*?)\'', _version_file.read(), re.DOTALL
    ).group(1)


def get_files_from_folder(folder):
    '''Get all files in a folder in resource folder.'''
    plugin_directory = os.path.join(RESOURCE_PATH, folder)
    plugin_data_files = []

    for root, directories, files in os.walk(plugin_directory):
        files_list = []
        if files:
            for filename in files:
                files_list.append(
                    os.path.join(root, filename)
                )

        if files_list:
            destination_folder = root.replace(
                RESOURCE_PATH, 'ftrack_connect_nuke_studio/resource'
            )
            plugin_data_files.append(
                (destination_folder, files_list)
            )

    return plugin_data_files

data_files = []

for child in os.listdir(
    RESOURCE_PATH
):
    if os.path.isdir(os.path.join(RESOURCE_PATH, child)) and child != 'hook':
        data_files += get_files_from_folder(child)

data_files += get_files_from_folder(RESOURCE_PATH)

data_files.append(
    (
        'ftrack_connect_nuke_studio/hook',
        glob.glob(os.path.join(RESOURCE_PATH, 'hook', '*.py'))
    )
)

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
            RESOURCE_PATH,
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
        'ftrack-python-api >= 1, < 2',
        'lucidity >= 1.5, < 2'
    ],
    dependency_links=[
        connect_dependency_link
    ],
    tests_require=[
    ],
    zip_safe=False,
    data_files=data_files,
    cmdclass={
        'build_plugin': BuildPlugin
    },
)
