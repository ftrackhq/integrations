# :coding: utf-8

import os
import re
import glob

from setuptools import setup, find_packages

ROOT_PATH = os.path.dirname(os.path.realpath(__file__))
SOURCE_PATH = os.path.join(ROOT_PATH, 'source')
README_PATH = os.path.join(ROOT_PATH, 'README.rst')
RESOURCE_PATH = os.path.join(ROOT_PATH, 'resource')

# Read version from source.
with open(os.path.join(
    SOURCE_PATH, 'ftrack_connect_nuke_studio', '_version.py'
)) as _version_file:
    VERSION = re.match(
        r'.*__version__ = \'(.*?)\'', _version_file.read(), re.DOTALL
    ).group(1)

connect_foundry_dependency_link = (
    'file://{0}#egg=ftrack-connect-foundry-0.1.0'
    .format(os.environ['FTRACK_CONNECT_FOUNDRY'].replace('\\', '/'))
)


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
        'mock'
    ],
    install_requires=[
        'ftrack-connect >= 0.1.2, < 2',
        'ftrack-connect-foundry >= 0.1.0, < 2'
    ],
    dependency_links=[
        connect_foundry_dependency_link
    ],
    tests_require=[
    ],
    zip_safe=False,
    data_files=data_files
)
