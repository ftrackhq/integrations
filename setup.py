# :coding: utf-8
# :copyright: Copyright (c) 2014 ftrack

import sys
import os
import re
import pkg_resources

from setuptools import setup, Distribution, find_packages


ROOT_PATH = os.path.dirname(os.path.realpath(__file__))
SOURCE_PATH = os.path.join(ROOT_PATH, 'source')
README_PATH = os.path.join(ROOT_PATH, 'README.rst')


# Read version from source.
with open(os.path.join(
    SOURCE_PATH, 'ftrack_connect_package', '_version.py'
)) as _version_file:
    VERSION = re.match(
        r'.*__version__ = \'(.*?)\'', _version_file.read(), re.DOTALL
    ).group(1)


# General configuration.
configuration = dict(
    name='ftrack-connect-package',
    version=VERSION,
    description='Meta package for ftrack connect.',
    long_description=open(README_PATH).read(),
    keywords='ftrack, connect, package',
    url='https://bitbucket.org/ftrack/ftrack-connect-package',
    author='ftrack',
    author_email='support@ftrack.com',
    license='Apache License (2.0)',
    packages=find_packages(SOURCE_PATH),
    package_dir={
        '': 'source'
    },
    setup_requires=[
    ],
    install_requires=[
        'ftrack-connect >=0.1, < 1'
    ],
    dependency_links=[
        # TODO: Update when ftrack-connect released.
        ('https://bitbucket.org/ftrack/ftrack-connect/'
         'get/backlog/package-connect-for-download/package-repository.zip'
         '#egg=ftrack-connect-0.1.0')
    ],
    options={}
)


# Platform specific distributions.
if sys.platform in ('darwin', 'win32'):

    # Ensure cx_freeze available for import.
    Distribution(dict(setup_requires='cx_freeze'))
    configuration['setup_requires'].append('cx_freeze')

    from cx_Freeze import setup, Executable

    # Discover ftrack-connect resources that need to be included outside of the
    # standard zipped bundle.
    resources = pkg_resources.resource_filename(
        pkg_resources.Requirement.parse('ftrack-connect'),
        'ftrack_connect_resource/hook'
    )

    executables = []
    if sys.platform == 'win32':
        executables.append(
            Executable(
                script='source/ftrack_connect_package/__main__.py',
                base='Win32GUI',
                targetName='ftrack_connect_package.exe',
                icon='./logo.ico'
            )
        )

    elif sys.platform == 'darwin':
        executables.append(
            Executable(
                script='source/ftrack_connect_package/__main__.py',
                base=None,
                targetName='ftrack_connect_package',
                icon='./logo.icns'
            )
        )

        configuration['options']['bdist_mac'] = {
            'iconfile': './logo.icns',
            'bundle_name': 'ftrack_connect_package'
        }

    configuration['executables'] = executables

    configuration['options']['build_exe'] = {
        'includes': [
            'ftrack_connect.ui.application',
            'atexit'  # Required for PySide
        ],
        'excludes': [
            # The following don't actually exist, but are picked up by the
            # dependency walker somehow.
            'boto.compat.sys',
            'boto.compat._sre',
            'boto.compat.array',
            'boto.compat._struct',
            'boto.compat._json'
        ],
        'include_files': [
            (resources, 'resource/hook')
        ]
    }

    configuration['setup_requires'].extend(
        configuration['install_requires']
    )


# Call main setup.
setup(**configuration)
