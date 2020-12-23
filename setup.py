# :coding: utf-8
# :copyright: Copyright (c) 2014 ftrack

'''
requires :
pyside2 = 5.14.1


'''



import sys
import os
import re
import opcode
import logging
import pkg_resources

# # Package and dependencies versions.

ftrack_connect_version = '2.0'
ftrack_action_handler_version = '0.2.1'
import PySide2

pyside_path = os.path.join(PySide2.__path__[0])

# Setup code

logging.basicConfig(
    level=logging.INFO
)

from setuptools import Distribution, find_packages, setup as setup


ROOT_PATH = os.path.dirname(os.path.realpath(__file__))
SOURCE_PATH = os.path.join(ROOT_PATH, 'source')
RESOURCE_PATH = os.path.join(ROOT_PATH, 'resource')
README_PATH = os.path.join(ROOT_PATH, 'README.rst')
BUILD_PATH = os.path.join(ROOT_PATH, 'build')

# Read version from source.
with open(os.path.join(
    SOURCE_PATH, 'ftrack_connect_package', '_version.py'
)) as _version_file:
    VERSION = re.match(
        r'.*__version__ = \'(.*?)\'', _version_file.read(), re.DOTALL
    ).group(1)


connect_resource_hook = pkg_resources.resource_filename(
    pkg_resources.Requirement.parse('ftrack-connect'),
    'ftrack_connect_resource/hook'
)


connect_install_require = 'ftrack-connect'.format(ftrack_connect_version)
# TODO: Update when ftrack-connect released.
connect_dependency_link = (
    'git+https://bitbucket.org/ftrack/ftrack-connect.git@backlog/connect-2/story#egg=ftrack-connect'
).format(ftrack_connect_version)


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
        # 'sphinx >= 1.2.2, < 2',
        # 'sphinx_rtd_theme >= 0.1.6, < 2',
        'lowdown >= 0.1.0, < 1',
        'cryptography',
        'requests >= 2, <3',
        'ftrack_action_handler == {0}'.format(
            ftrack_action_handler_version
        ),
        'cx_freeze',
        'pyside2==5.14.1',
        'wheel',
        'setuptools'
    ],
    install_requires=[
        connect_install_require
    ],
    options={},
    dependency_links=[
        connect_dependency_link
    ],
    python_requires=">=3, <4"
)

# to run : python setup.py install
setup(**configuration)

# Platform specific distributions.
if sys.platform in ('darwin', 'win32', 'linux'):

    configuration['setup_requires'].append('cx_freeze')

    from cx_Freeze import setup ,Executable, build

    # Ensure ftrack-connect is
    # available for import and then discover ftrack-connect and
    # resources that need to be included outside of
    # the standard zipped bundle.
    Distribution(dict(
        setup_requires=[
            connect_install_require,
        ]
    ))

    # Add requests certificates to resource folder.
    import requests.certs

    include_files = [
        (connect_resource_hook, 'resource/hook'),
        (os.path.join(RESOURCE_PATH, 'hook'), 'resource/hook'),
        (requests.certs.where(), 'resource/cacert.pem'),
        (os.path.join(
            SOURCE_PATH, 'ftrack_connect_package', '_version.py'
        ), 'resource/ftrack_connect_package_version.py'),
        'qt.conf'
    ]

    zip_include_packages = [
        "PySide2",
        "shiboken2",
        "encodings",
    ]


    executables = []
    bin_includes = []
    includes = []

    # Different modules are used on different platforms. Make sure to include
    # all found.
    for dbmodule in ['csv', 'sqlite3']:
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
                #base=None,
                targetName='ftrack_connect_package.exe',
                icon='./logo.ico',
                # initScript=os.path.join(RESOURCE_PATH, 'frozen_bootstrap.py')
            )
        )

        # Specify upgrade code to a random GUID to ensure the MSI
        # package is upgraded when installing a new version.
        configuration['options']['bdist_msi'] = {
            'upgrade_code': '{6068BD18-65D1-47FC-BE5E-06AA5189C9CB}',
            'initial_target_dir': r'[ProgramFilesFolder]\{0}-{1}'.format(
                'ftrack-connect-package', VERSION
            ),
            'data': {'Shortcut': shortcut_table}
        }

        include_files.extend(
            [
                os.path.join(pyside_path, "plugins", "platforms"),
                os.path.join(pyside_path, "plugins", "imageformats"),
                os.path.join(pyside_path, "plugins", "iconengines"),
            ]
        )

    elif sys.platform == 'darwin':
        executables.append(
            Executable(
                script='source/ftrack_connect_package/__main__.py',
                base=None,
                targetName='ftrack_connect_package',
                icon='./logo.icns',
                # initScript=os.path.join(RESOURCE_PATH, 'frozen_bootstrap.py')

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

    elif sys.platform == 'linux':

        executables.append(
            Executable(
                script='source/ftrack_connect_package/__main__.py',
                base=None,
                targetName='ftrack_connect_package',
                icon='./logo.icns',
                # initScript=os.path.join(RESOURCE_PATH, 'frozen_bootstrap.py')
        )
        )

        include_files.extend(
            [
                os.path.join(pyside_path,"Qt", "plugins", "platforms"),
                os.path.join(pyside_path,"Qt", "plugins", "imageformats"),
                os.path.join(pyside_path,"Qt", "plugins", "iconengines"),
            ]
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

    encodings_path = os.path.join(
        os.path.dirname(opcode.__file__), 'encodings'
    )

    include_files.append((encodings_path, 'encodings'))

    includes.extend([
        'atexit',  # Required for PySide
        'ftrack_connect',
        'ftrack_api.resource_identifier_transformer.base',
        'ftrack_api.structure.id',
        'encodings',
        'PySide2',
        'Qt',
        'shiboken2',
        'PySide2.QtSvg',
        'PySide2.QtXml',
        'PySide2.QtCore',
        'PySide2.QtWidgets',
        'PySide2.QtGui',
        'ssl',
        'xml.etree',
        'xml.etree.ElementTree',
        'xml.etree.ElementPath',
        'xml.etree.ElementInclude',
        'http',
        'http.server',
        'webbrowser',
    ])

    configuration['options']['build_exe'] = {
        'includes': includes,
        "zip_include_packages": [
            'ftrack_connect',
            "PySide2",
            "shiboken2",
            "Qt",
            'PySide2.QtSvg',
            'PySide2.QtXml',
            'PySide2.QtCore',
            'PySide2.QtWidgets',
            'PySide2.QtGui',
            "encodings",
            'http',
            'urllib.parser',
            'webbrowser'
        ],
        # "include_msvcr": True,
        'excludes': [
            "tkinter",
            "unittest",
            "test",
            # "email",
            # The following don't actually exist, but are picked up by the
            # dependency walker somehow.
            # 'boto.compat.sys',
            # 'boto.compat._sre',
            # 'boto.compat.array',
            # 'boto.compat._struct',
            # 'boto.compat._json',

            # Compiled yaml uses unguarded pkg_resources.resource_filename which
            # won't work in frozen package.
            '_yaml',

            # Exclude distutils from virtualenv due to entire package with
            # sub-modules not being copied to virtualenv.
            # 'distutils',
            # 'distutils',

        ],
        'include_files': include_files,
        'bin_includes': bin_includes,
        'zip_include_packages': zip_include_packages
    }

    configuration['setup_requires'].extend(
        configuration['install_requires']
    )

# Call main setup.
setup(**configuration)
