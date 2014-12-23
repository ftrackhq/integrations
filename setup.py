# :coding: utf-8
# :copyright: Copyright (c) 2014 ftrack

import sys
import os
import re
import pkg_resources

from setuptools import setup, Distribution, find_packages


ROOT_PATH = os.path.dirname(os.path.realpath(__file__))
SOURCE_PATH = os.path.join(ROOT_PATH, 'source')
RESOURCE_PATH = os.path.join(ROOT_PATH, 'resource')
README_PATH = os.path.join(ROOT_PATH, 'README.rst')


# Read version from source.
with open(os.path.join(
    SOURCE_PATH, 'ftrack_connect_package', '_version.py'
)) as _version_file:
    VERSION = re.match(
        r'.*__version__ = \'(.*?)\'', _version_file.read(), re.DOTALL
    ).group(1)

connect_install_require = 'ftrack-connect >=0.1, < 1'
# TODO: Update when ftrack-connect released.
connect_dependency_link = (
    'https://bitbucket.org/ftrack/ftrack-connect/get/master.zip'
    '#egg=ftrack-connect-0.1.0'
)

cinesync_install_require = 'ftrack-connect-cinesync >=0.1, < 1'
cinesync_dependency_link = (
    'https://bitbucket.org/ftrack/ftrack-connect-cinesync/get/master.zip'
    '#egg=ftrack-connect-cinesync-0.1.1'
)

connect_legacy_plugins_install_require = (
    'ftrack-connect-legacy-plugins'
    ' >=0.1, < 1'
)
connect_legacy_plugins_dependency_link = 'file://{0}#egg=ftrack-connect-legacy-plugins-0.1.0'.format(
    os.environ['FTRACK_CONNECT_LEGACY_PLUGINS_PATH'].replace('\\', '/')
)

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
        'ftrack-python-legacy-api',
        connect_install_require,
        cinesync_install_require,
        connect_legacy_plugins_install_require
    ],
    dependency_links=[
        'file://{0}#egg=ftrack-python-legacy-api'.format(
            os.environ['FTRACK_PYTHON_LEGACY_API_PATH'].replace('\\', '/')
        ),
        connect_dependency_link,
        cinesync_dependency_link,
        connect_legacy_plugins_dependency_link
    ],
    options={}
)


# Platform specific distributions.
if sys.platform in ('darwin', 'win32'):

    # Ensure cx_freeze available for import.
    Distribution(
        dict(
            setup_requires='cx-freeze == 4.3.3.ftrack',
            dependency_links=[
                'https://bitbucket.org/ftrack/cx-freeze/get/ftrack.zip'
                '#egg=cx-freeze-4.3.3.ftrack'
            ]
        )
    )
    configuration['setup_requires'].append('cx_freeze')

    from cx_Freeze import setup, Executable

    # Ensure ftrack-connect and ftrack-connect-cinesync
    # available for import and then discover ftrack-connect and
    # ftrack-connect-cinesync resources that need to be included outside of
    # the standard zipped bundle.
    Distribution(dict(
        setup_requires=[
            connect_install_require,
            cinesync_install_require,
            connect_legacy_plugins_install_require
        ],
        dependency_links=[
            cinesync_dependency_link,
            connect_dependency_link,
            connect_legacy_plugins_dependency_link
        ]
    ))
    connect_resource_hook = pkg_resources.resource_filename(
        pkg_resources.Requirement.parse('ftrack-connect'),
        'ftrack_connect_resource/hook'
    )

    cinesync_resource_script = pkg_resources.resource_filename(
        pkg_resources.Requirement.parse('ftrack-connect-cinesync'),
        'ftrack_connect_cinesync_resource/script'
    )

    cinesync_resource_hook = pkg_resources.resource_filename(
        pkg_resources.Requirement.parse('ftrack-connect-cinesync'),
        'ftrack_connect_cinesync_resource/hook'
    )

    ftrack_connect_legacy_plugins_source = pkg_resources.resource_filename(
        pkg_resources.Requirement.parse('ftrack-connect-legacy-plugins'),
        'ftrack_connect_legacy_plugins/legacy_plugins'
    )

    ftrack_connect_legacy_plugins_hook = pkg_resources.resource_filename(
        pkg_resources.Requirement.parse('ftrack-connect-legacy-plugins'),
        'ftrack_connect_legacy_plugins/hook'
    )

    include_files = [
        (connect_resource_hook, 'resource/hook'),
        (cinesync_resource_hook, 'resource/hook'),
        (cinesync_resource_script, 'resource/script'),
        (ftrack_connect_legacy_plugins_source, 'resource/legacy_plugins'),
        (ftrack_connect_legacy_plugins_hook, 'resource/hook')
    ]

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
            'bundle_name': 'ftrack-connect'
        }

        configuration['options']['bdist_dmg'] = {
            'applications_shortcut': True,
            'volume_label': 'ftrack-connect-{0}'.format(VERSION)
        }

    configuration['executables'] = executables

    configuration['options']['build_exe'] = {
        'init_script': os.path.join(RESOURCE_PATH, 'frozen_bootstrap.py'),
        'includes': [
            'ftrack',
            'atexit',  # Required for PySide
            'ftrack_connect_cinesync.cinesync_launcher',
            'ftrack_connect.application'
        ],
        'excludes': [
            # The following don't actually exist, but are picked up by the
            # dependency walker somehow.
            'boto.compat.sys',
            'boto.compat._sre',
            'boto.compat.array',
            'boto.compat._struct',
            'boto.compat._json',

            # Compiled yaml uses unguarded pkg_resources.resource_filename which
            # won't work in frozen package.
            '_yaml'
        ],
        'include_files': include_files
    }

    configuration['setup_requires'].extend(
        configuration['install_requires']
    )


# Call main setup.
setup(**configuration)
