# :coding: utf-8
# :copyright: Copyright (c) 2014 ftrack

import sys
import os
import re
import pkg_resources
import opcode
import logging

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

connect_install_require = 'ftrack-connect == 0.1.19'
# TODO: Update when ftrack-connect released.
connect_dependency_link = (
    'https://bitbucket.org/ftrack/ftrack-connect/get/0.1.19.zip'
    '#egg=ftrack-connect-0.1.19'
)

cinesync_install_require = 'ftrack-connect-cinesync == 0.1.2'
cinesync_dependency_link = (
    'https://bitbucket.org/ftrack/ftrack-connect-cinesync/get/0.1.2.zip'
    '#egg=ftrack-connect-cinesync-0.1.2'
)

connect_legacy_plugins_install_require = (
    'ftrack-connect-legacy-plugins'
    ' >=0.1, < 1'
)
connect_legacy_plugins_dependency_link = (
    'file://{0}#egg=ftrack-connect-legacy-plugins-0.1.6'
    .format(os.environ['FTRACK_CONNECT_LEGACY_PLUGINS_PATH'].replace('\\', '/'))
)

connect_hieroplayer_install_require = (
    'ftrack-connect-hieroplayer'
    ' >=0.1, < 1'
)
connect_hieroplayer_dependency_link = (
    'https://bitbucket.org/ftrack/ftrack-connect-hieroplayer/get/0.1.4.zip'
    '#egg=ftrack-connect-hieroplayer-0.1.4'
)

connect_nuke_dependency_link = (
    'https://bitbucket.org/ftrack/ftrack-connect-nuke/get/0.1.6.zip'
    '#egg=ftrack-connect-nuke-0.1.6'
)
connect_nuke_dependency_install_require = (
    'ftrack-connect-nuke'
    ' >=0.1, < 1'
)

connect_maya_dependency_link = (
    'https://bitbucket.org/ftrack/ftrack-connect-maya/get/0.2.0.zip'
    '#egg=ftrack-connect-maya-0.2.0'
)
connect_maya_dependency_install_require = (
    'ftrack-connect-maya'
    ' >=0.1, < 1'
)

connect_nuke_studio_dependency_link = (
    'https://bitbucket.org/ftrack/ftrack-connect-nuke-studio/get/0.2.0.zip'
    '#egg=ftrack-connect-nuke-studio-0.2.0'
)
connect_nuke_studio_dependency_install_require = (
    'ftrack-connect-nuke-studio'
    ' >=0.1, < 1'
)

connect_rv_dependency_install_require = 'ftrack-connect-rv >=0.1, < 1'

connect_rv_dependency_link = (
    'https://bitbucket.org/ftrack/ftrack-connect-rv/get/0.1.0.zip'
    '#egg=ftrack-connect-rv-0.1.0'
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
        'sphinx >= 1.2.2, < 2',
        'sphinx_rtd_theme >= 0.1.6, < 2',
        'lowdown >= 0.1.0, < 1',
        'pyopenssl',
        'requests >= 2, <3'
    ],
    install_requires=[
        'ftrack-python-legacy-api',
        connect_install_require,
        cinesync_install_require,
        connect_legacy_plugins_install_require,
        connect_hieroplayer_install_require,
        connect_nuke_dependency_install_require,
        connect_maya_dependency_install_require,
        connect_nuke_studio_dependency_install_require,
        connect_rv_dependency_install_require
    ],
    dependency_links=[
        'file://{0}#egg=ftrack-python-legacy-api'.format(
            os.environ['FTRACK_PYTHON_LEGACY_API_PATH'].replace('\\', '/')
        ),
        connect_dependency_link,
        cinesync_dependency_link,
        connect_legacy_plugins_dependency_link,
        ('https://bitbucket.org/ftrack/lowdown/get/0.1.0.zip'
         '#egg=lowdown-0.1.0'),
        connect_hieroplayer_dependency_link,
        connect_maya_dependency_link,
        connect_nuke_dependency_link,
        connect_nuke_studio_dependency_link,
        connect_rv_dependency_link
    ],
    options={}
)


# Platform specific distributions.
if sys.platform in ('darwin', 'win32', 'linux2'):

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
            connect_legacy_plugins_install_require,
            connect_hieroplayer_install_require,
            connect_maya_dependency_install_require,
            connect_nuke_dependency_install_require,
            connect_nuke_studio_dependency_install_require,
            connect_rv_dependency_install_require
        ],
        dependency_links=[
            cinesync_dependency_link,
            connect_dependency_link,
            connect_legacy_plugins_dependency_link,
            connect_hieroplayer_dependency_link,
            connect_maya_dependency_link,
            connect_nuke_dependency_link,
            connect_nuke_studio_dependency_link,
            connect_rv_dependency_link
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

    ftrack_connect_hieroplayer_source = pkg_resources.resource_filename(
        pkg_resources.Requirement.parse('ftrack-connect-hieroplayer'),
        'ftrack_connect_hieroplayer_source'
    )

    ftrack_connect_hieroplayer_hook = pkg_resources.resource_filename(
        pkg_resources.Requirement.parse('ftrack-connect-hieroplayer'),
        'ftrack_connect_hieroplayer_resource/hook'
    )

    ftrack_connect_nuke_source = pkg_resources.resource_filename(
        pkg_resources.Requirement.parse('ftrack-connect-nuke'),
        'ftrack_connect_nuke/ftrack_connect_nuke'
    )

    ftrack_connect_nuke_hook = pkg_resources.resource_filename(
        pkg_resources.Requirement.parse('ftrack-connect-nuke'),
        'ftrack_connect_nuke/hook'
    )

    ftrack_connect_maya_source = pkg_resources.resource_filename(
        pkg_resources.Requirement.parse('ftrack-connect-maya'),
        'ftrack_connect_maya/ftrack_connect_maya'
    )

    ftrack_connect_maya_hook = pkg_resources.resource_filename(
        pkg_resources.Requirement.parse('ftrack-connect-maya'),
        'ftrack_connect_maya/hook'
    )

    ftrack_connect_nuke_studio_source = pkg_resources.resource_filename(
        pkg_resources.Requirement.parse('ftrack-connect-nuke-studio'),
        'ftrack_connect_nuke_studio/resource'
    )

    ftrack_connect_nuke_studio_hook = pkg_resources.resource_filename(
        pkg_resources.Requirement.parse('ftrack-connect-nuke-studio'),
        'ftrack_connect_nuke_studio/hook'
    )

    ftrack_connect_rv_hook = pkg_resources.resource_filename(
        pkg_resources.Requirement.parse('ftrack-connect-rv'),
        'ftrack_connect_rv_resource/hook'
    )

    # Add requests certificates to resource folder.
    import requests.certs

    include_files = [
        (connect_resource_hook, 'resource/hook'),
        (cinesync_resource_hook, 'resource/hook'),
        (cinesync_resource_script, 'resource/script'),
        (ftrack_connect_legacy_plugins_source, 'resource/legacy_plugins'),
        (ftrack_connect_legacy_plugins_hook, 'resource/hook'),
        (ftrack_connect_hieroplayer_hook, 'resource/hook'),
        (ftrack_connect_hieroplayer_source, 'resource/hieroplayer'),
        (ftrack_connect_rv_hook, 'resource/hook'),
        (os.path.join(RESOURCE_PATH, 'hook'), 'resource/hook'),
        (ftrack_connect_maya_hook, 'resource/hook'),
        (ftrack_connect_maya_source, 'resource/ftrack_connect_maya'),
        (ftrack_connect_nuke_hook, 'resource/hook'),
        (ftrack_connect_nuke_source, 'resource/ftrack_connect_nuke'),
        (requests.certs.where(), 'resource/cacert.pem'),
        (
            ftrack_connect_nuke_studio_source,
            'resource/ftrack_connect_nuke_studio'
        ),
        (ftrack_connect_nuke_studio_hook, 'resource/hook'),
        (os.path.join(
            SOURCE_PATH, 'ftrack_connect_package', '_version.py'
        ), 'resource/ftrack_connect_package_version.py')
    ]

    executables = []
    bin_includes = []
    includes = []

    # Different modules are used on different platforms. Make sure to include
    # all found.
    for dbmodule in ['dbhash', 'gdbm', 'dbm', 'dumbdbm']:
        try:
            __import__(dbmodule)
        except ImportError:
            logging.warning('"{0}" module not available.'.format(dbmodule))
        else:
            includes.append(dbmodule)

    if sys.platform == 'win32':
        executables.append(
            Executable(
                script='source/ftrack_connect_package/__main__.py',
                base='Win32GUI',
                targetName='ftrack_connect_package.exe',
                icon='./logo.ico'
            )
        )

        # Specify upgrade code to a random GUID to ensure the MSI
        # package is upgraded when installing a new version.
        configuration['options']['bdist_msi'] = {
            'upgrade_code': '{e5666af3-56a5-426a-b308-54c2d6ad8704}'
        }

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
            'bundle_name': 'ftrack-connect',
            'custom_info_plist': os.path.join(
                RESOURCE_PATH, 'Info.plist'
            )
        }

        configuration['options']['bdist_dmg'] = {
            'applications_shortcut': True,
            'volume_label': 'ftrack-connect-{0}'.format(VERSION)
        }

    elif sys.platform == 'linux2':
        executables.append(
            Executable(
                script='source/ftrack_connect_package/__main__.py',
                base=None,
                targetName='ftrack_connect_package',
                icon='./logo.icns'
            )
        )

        # Force Qt to be included.
        bin_includes = [
            'libQtCore.so',
            'libQtGui.so',
            'libQtNetwork.so',
            'libQtSvg.so',
            'libQtXml.so'
        ]

    configuration['executables'] = executables

    # opcode is not a virtualenv module, so we can use it to find the stdlib.
    # This is the same trick used by distutils itself it installs itself into
    # the virtualenv
    distutils_path = os.path.join(
        os.path.dirname(opcode.__file__), 'distutils'
    )

    include_files.append((distutils_path, 'distutils'))

    includes.extend([
        'ftrack',
        'atexit',  # Required for PySide
        'ftrack_connect_cinesync.cinesync_launcher',
        'ftrack_connect.application',
        'assetmgr_hiero',
        'assetmgr_nuke',
        'FnAssetAPI',
        'ftrack_connect_nuke',
        'ftrack_connect_nuke.plugin',
        'ftrack_connect_nuke.logging',
        'ftrack_connect_legacy_plugins',
        'ftrack_connect_hieroplayer',
        'ftrack_connect_rv',
        'lucidity',
        'ftrack_connect_maya'
    ])

    configuration['options']['build_exe'] = {
        'init_script': os.path.join(RESOURCE_PATH, 'frozen_bootstrap.py'),
        'includes': includes,
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
            '_yaml',

            # Exclude distutils from virtualenv due to entire package with
            # sub-modules not being copied to virtualenv.
            'distutils'
        ],
        'include_files': include_files,
        'bin_includes': bin_includes
    }

    configuration['setup_requires'].extend(
        configuration['install_requires']
    )


# Call main setup.
setup(**configuration)
