# :coding: utf-8
# :copyright: Copyright (c) 2014 ftrack

import datetime
import sys
import os
import re
import pkg_resources
import opcode
import logging
import zipfile

# Package and dependencies versions.
ftrack_connect_version = '1.1.6'
ftrack_connect_rv_version = '3.7'
ftrack_connect_cinema_4d_version = '0.1.5'
ftrack_location_compatibility_version = '0.3.2'
ftrack_action_handler_version = '0.1.3'

# Embedded plugins.
ftrack_connect_maya_publish_version = '0.6.2'
ftrack_connect_nuke_publish_version = '0.6.2'
ftrack_connect_3dsmax_version = '0.4.0'
ftrack_connect_hieroplayer_version = '1.3.0'
ftrack_connect_nuke_version = '1.2.0'
ftrack_connect_maya_version = '1.2.0'
ftrack_connect_nuke_studio_version = '2.1.0'

# Setup code

logging.basicConfig(
    level=logging.INFO
)

from setuptools import setup, Distribution, find_packages


ROOT_PATH = os.path.dirname(os.path.realpath(__file__))
SOURCE_PATH = os.path.join(ROOT_PATH, 'source')
RESOURCE_PATH = os.path.join(ROOT_PATH, 'resource')
README_PATH = os.path.join(ROOT_PATH, 'README.rst')
BUILD_PATH = os.path.join(ROOT_PATH, 'build')
DOWNLOAD_PLUGIN_PATH = os.path.join(
    BUILD_PATH, 'plugin-downloads-{0}'.format(
        datetime.datetime.now().strftime('%y-%m-%d-%H-%M-%S')
    )
)


# Read version from source.
with open(os.path.join(
    SOURCE_PATH, 'ftrack_connect_package', '_version.py'
)) as _version_file:
    VERSION = re.match(
        r'.*__version__ = \'(.*?)\'', _version_file.read(), re.DOTALL
    ).group(1)


external_connect_plugins = []
for plugin in (
    'ftrack-connect-maya-publish-{0}.zip'.format(ftrack_connect_maya_publish_version),
    'ftrack-connect-nuke-publish-{0}.zip'.format(ftrack_connect_nuke_publish_version),
    'ftrack-connect-nuke-studio-{0}.zip'.format(ftrack_connect_nuke_studio_version),
    'ftrack-connect-maya-{0}.zip'.format(ftrack_connect_maya_version),
    'ftrack-connect-nuke-{0}.zip'.format(ftrack_connect_nuke_version),
    # 'ftrack-connect-3dsmax-{0}.zip'.format(ftrack_connect_3dsmax_version),
    'ftrack-connect-hieroplayer-{0}.zip'.format(ftrack_connect_hieroplayer_version)
):
    external_connect_plugins.append(
        (plugin, plugin.replace('.zip', ''))
    )


connect_install_require = 'ftrack-connect == {0}'.format(ftrack_connect_version)
# TODO: Update when ftrack-connect released.
connect_dependency_link = (
    'https://bitbucket.org/ftrack/ftrack-connect/get/{0}.zip'
    '#egg=ftrack-connect-{0}'
).format(ftrack_connect_version)

connect_rv_dependency_install_require = 'ftrack-connect-rv >=3.4, < 4'

connect_rv_dependency_link = (
    'https://bitbucket.org/ftrack/ftrack-connect-rv/get/{0}.zip'
    '#egg=ftrack-connect-rv-{0}'
).format(ftrack_connect_rv_version)

connect_cinema_4d_dependency_install_require = 'ftrack-connect-cinema-4d >=0.1, < 1'

connect_cinema_4d_dependency_link = (
    'https://bitbucket.org/ftrack/ftrack-connect-cinema-4d/get/{0}.zip'
    '#egg=ftrack-connect-cinema-4d-{0}'
).format(ftrack_connect_cinema_4d_version)

ftrack_python_legacy_api_install_require = 'ftrack-python-legacy-api >= 3.6.0, < 4'

connect_ftrack_location_compatibilty_install_require = 'ftrack-location-compatibility >= 0.1, < 1'

connect_ftrack_location_compatibilty_dependency_link = (
    'https://bitbucket.org/ftrack/ftrack-location-compatibility/get/{0}.zip'
    '#egg=ftrack-location-compatibility-{0}'
).format(ftrack_location_compatibility_version)


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
        # The latest version of the cryptography library does not have a wheel
        # and building it fails.
        'cryptography == 1.8.2',
        'pyopenssl<= 17.0.0,<17.0.1',
        'requests >= 2, <3',
        'ftrack_action_handler == {0}'.format(
            ftrack_action_handler_version
        )
    ],
    install_requires=[
        ftrack_python_legacy_api_install_require,
        connect_install_require,
        connect_rv_dependency_install_require,
        connect_cinema_4d_dependency_install_require,
        connect_ftrack_location_compatibilty_install_require,
        'boto == 2.28.0'
    ],
    dependency_links=[
        connect_dependency_link,
        ('https://bitbucket.org/ftrack/lowdown/get/0.1.0.zip'
         '#egg=lowdown-0.1.0'),
        connect_rv_dependency_link,
        connect_cinema_4d_dependency_link,
        connect_ftrack_location_compatibilty_dependency_link
    ],
    options={}
)


# Platform specific distributions.
if sys.platform in ('darwin', 'win32', 'linux2'):

    # Ensure cx_freeze available for import.

    # TODO: RESTORE TO MASTER ONCE TESTED.

    Distribution(
        dict(
            setup_requires='cx-freeze == 4.3.3.ftrack',
            dependency_links=[
                'https://bitbucket.org/ftrack/cx-freeze/get/backlog/remove-integrations.zip'
                '#egg=cx-freeze-4.3.3.ftrack'
            ]
        )
    )
    configuration['setup_requires'].append('cx_freeze')

    from cx_Freeze import setup, Executable, build

    class Build(build):
        '''Custom build to pre-build resources.'''

        def run(self):
            '''Run build ensuring build_resources called first.'''
            download_url = (
                'https://s3-eu-west-1.amazonaws.com/ftrack-deployment/'
                'ftrack-connect/plugins/'
            )
            import requests

            #: TODO: Clean up the temporary download folder.
            os.makedirs(DOWNLOAD_PLUGIN_PATH)

            for plugin, target in external_connect_plugins:
                url = download_url + plugin
                temp_path = os.path.join(DOWNLOAD_PLUGIN_PATH, plugin)
                logging.info(
                    'Downloading url {0} to {1}'.format(
                        url,
                        temp_path
                    )
                )

                response = requests.get(url)
                response.raise_for_status()

                if response.status_code != 200:
                    raise ValueError(
                        'Got status code not equal to 200: {0}'.format(
                            response.status_code
                        )
                    )

                with open(temp_path, 'wb') as package_file:
                    package_file.write(response.content)

                with zipfile.ZipFile(temp_path, 'r') as myzip:
                    myzip.extractall(
                        os.path.join(DOWNLOAD_PLUGIN_PATH, target)
                    )

            build.run(self)

    configuration['cmdclass'] = {
        'build': Build
    }

    # Ensure ftrack-connect is
    # available for import and then discover ftrack-connect and
    # resources that need to be included outside of
    # the standard zipped bundle.
    Distribution(dict(
        setup_requires=[
            connect_install_require,
            connect_rv_dependency_install_require,
            connect_cinema_4d_dependency_install_require,
            connect_ftrack_location_compatibilty_install_require
        ],
        dependency_links=[
            connect_dependency_link,
            connect_rv_dependency_link,
            connect_cinema_4d_dependency_link,
            connect_ftrack_location_compatibilty_dependency_link
        ]
    ))
    connect_resource_hook = pkg_resources.resource_filename(
        pkg_resources.Requirement.parse('ftrack-connect'),
        'ftrack_connect_resource/hook'
    )

    ftrack_connect_rv_hook = pkg_resources.resource_filename(
        pkg_resources.Requirement.parse('ftrack-connect-rv'),
        'ftrack_connect_rv_resource/hook'
    )

    ftrack_connect_cinema_4d_hook = pkg_resources.resource_filename(
        pkg_resources.Requirement.parse('ftrack-connect-cinema-4d'),
        'ftrack_connect_cinema_4d/hook'
    )

    connect_ftrack_location_compatibilty_hook = pkg_resources.resource_filename(
        pkg_resources.Requirement.parse('ftrack-location-compatibility'),
        'ftrack_location_compatibility/hook'
    )

    # Add requests certificates to resource folder.
    import requests.certs

    include_files = [
        (connect_resource_hook, 'resource/hook'),
        (ftrack_connect_rv_hook, 'resource/hook'),
        (ftrack_connect_cinema_4d_hook, 'resource/hook'),
        (os.path.join(RESOURCE_PATH, 'hook'), 'resource/hook'),
        (connect_ftrack_location_compatibilty_hook, 'resource/hook/ftrack_location_compatibility'),
        (requests.certs.where(), 'resource/cacert.pem'),
        (os.path.join(
            SOURCE_PATH, 'ftrack_connect_package', '_version.py'
        ), 'resource/ftrack_connect_package_version.py'),
        'qt.conf'
    ]

    for _, plugin_directory in external_connect_plugins:
        plugin_download_path = os.path.join(
            DOWNLOAD_PLUGIN_PATH, plugin_directory
        )
        include_files.append(
            (
                os.path.relpath(plugin_download_path, ROOT_PATH),
                'resource/connect-standard-plugins/' + plugin_directory
            )
        )

    executables = []
    bin_includes = []
    includes = []

    # Different modules are used on different platforms. Make sure to include
    # all found.
    for dbmodule in ['dbhash', 'gdbm', 'dbm', 'dumbdbm', 'csv', 'sqlite3']:
        try:
            __import__(dbmodule)
        except ImportError:
            logging.warning('"{0}" module not available.'.format(dbmodule))
        else:
            includes.append(dbmodule)

    # MSI shotcut table list.
    shortcut_table = [
        (
            'DesktopShortcut',
            'DesktopFolder',
            'ftrack-connect',
            'TARGETDIR',
            '[TARGETDIR]ftrack_connect_package.exe',
            None,
            None,
            None,
            None,
            None,
            None,
            'TARGETDIR'
         ),
        (
            'ProgramMenuShortcut',
            'ProgramMenuFolder',
            'ftrack-connect',
            'TARGETDIR',
            '[TARGETDIR]ftrack_connect_package.exe',
            None,
            None,
            None,
            None,
            None,
            None,
            'TARGETDIR'
         )
    ]

    if sys.platform == 'win32':
        executables.append(
            Executable(
                script='source/ftrack_connect_package/__main__.py',
                base='Win32GUI',
                targetName='ftrack_connect_package.exe',
                icon='./logo.ico',
            )
        )

        # Specify upgrade code to a random GUID to ensure the MSI
        # package is upgraded when installing a new version.
        configuration['options']['bdist_msi'] = {
            'upgrade_code': '{e5666af3-56a5-426a-b308-54c2d6ad8704}',
            'initial_target_dir': r'[ProgramFilesFolder]\{0}-{1}'.format(
                'ftrack-connect-package', VERSION
            )
        }


        # Specify shortucut list for MSI installer
        configuration['options']['bdist_msi'] = {
            'data': {'Shortcut': shortcut_table}
        }

        # Seperate ftrack connect versions to separate install directories
        # it should be possible to pass this as an option with 'initial_target_dir'
        # but I did not manage to get it to work.
        sys.argv += ['--initial-target-dir',  r'[ProgramFilesFolder]\{0}-{1}'.format(
                'ftrack-connect-package', VERSION)
        ]

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
        'ftrack_connect.application',
        'ftrack_api.resource_identifier_transformer.base',
        'ftrack_api.structure.id',
        'ftrack_connect_rv',
        'ftrack_connect_cinema_4d',
        'ftrack_action_handler',
        'ftrack_action_handler.action',
        'ftrack_location_compatibility',
        'boto',
        'PySide.QtSvg',
        'PySide.QtXml',
        'packaging',
        'packaging.version',
        'packaging.specifiers',
        'packaging.requirements',
        'ssl'

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
            'distutils',
            
            # https://www.reddit.com/r/learnpython/comments/4rjkgj/no_file_named_sys_for_module_collectionssys/
            'collections.abc'
        ],
        'include_files': include_files,
        'bin_includes': bin_includes,
        'namespace_packages':['backports']
    }

    configuration['setup_requires'].extend(
        configuration['install_requires']
    )


# Call main setup.
setup(**configuration)
