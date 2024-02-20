# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

'''
requires :
pyside2 = 5.13.2


'''
import shutil
import sys
import os
import opcode
import logging
import plistlib
import pkg_resources
import subprocess
import time
import datetime
import zipfile

# The Connect installer version, remember to bump this and update release notes
# prior to release
__version__ = '24.2.0'

# Embedded plugins.


embedded_plugins = [
    # new/updated releases
]

bundle_name = 'ftrack Connect'
import PySide2
import shiboken2

pyside_path = os.path.join(PySide2.__path__[0])
shiboken_path = os.path.join(shiboken2.__path__[0])

# Setup code

logging.basicConfig(level=logging.INFO)

from setuptools import setup as setup

ROOT_PATH = os.path.dirname(os.path.realpath(__file__))
SOURCE_PATH = os.path.join(ROOT_PATH, 'source')
RESOURCE_PATH = os.path.join(ROOT_PATH, 'resource')
README_PATH = os.path.join(ROOT_PATH, 'README.md')
BUILD_PATH = os.path.join(ROOT_PATH, 'build')
DIST_PATH = os.path.join(ROOT_PATH, 'dist')
DOWNLOAD_PLUGIN_PATH = os.path.join(
    BUILD_PATH,
    'plugin-downloads-{0}'.format(
        datetime.datetime.now().strftime('%y-%m-%d-%H-%M-%S')
    ),
)
AWS_PLUGIN_DOWNLOAD_PATH = (
    'https://download.ftrack.com/ftrack-connect/integrations/'
)

# Write to _version.py

version_template = '''
# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

__version__ = {version!r}
'''

with open(
    os.path.join(SOURCE_PATH, 'ftrack_connect_installer', '_version.py'), 'w'
) as file:
    file.write(version_template.format(version=__version__))

print('BUILDING VERSION : {}'.format(__version__))

connect_resource_hook = os.path.join(
    pkg_resources.get_distribution("ftrack-connect").location,
    'ftrack_connect/hook',
)

external_connect_plugins = []
for plugin in embedded_plugins:
    external_connect_plugins.append((plugin, plugin.replace('.zip', '')))

# General configuration.
configuration = dict(
    name='ftrack Connect',
    description='Meta package for ftrack connect.',
    long_description=open(README_PATH).read(),
    keywords='ftrack, connect, package',
    url='https://github.com/ftrackhq/integrations/installers/connect-installer',
    author='ftrack',
    include_package_data=True,
    author_email='support@ftrack.com',
    license='Apache License (2.0)',
    package_dir={'': 'source'},
    package_data={"": ["{}/**/*.*".format(RESOURCE_PATH)]},
    version=__version__,
    setup_requires=[
        'lowdown >= 0.1.0, < 1',
        'cryptography',
        'requests >= 2, <3',
        'ftrack_action_handler >= 0.2.1',
        'cx_freeze',
        'wheel',
        'setuptools>=45.0.0',
        'setuptools_scm',
        'ftrack_utils',
    ],
    options={},
    python_requires=">=3, <4",
)

# Platform specific distributions.
if sys.platform in ('darwin', 'win32', 'linux'):
    configuration['setup_requires'].append('cx_freeze')

    from cx_Freeze import setup, Executable, build

    class BuildResources(build):
        '''Custom build to pre-build resources.'''

        def run(self):
            '''Run build ensuring build_resources called first.'''

            import requests

            print('Creating {}'.format(DOWNLOAD_PLUGIN_PATH))
            os.makedirs(DOWNLOAD_PLUGIN_PATH)

            for plugin, target in external_connect_plugins:
                url = AWS_PLUGIN_DOWNLOAD_PATH + plugin
                temp_path = os.path.join(DOWNLOAD_PLUGIN_PATH, plugin)
                logging.info(
                    'Downloading url {0} to {1}'.format(url, temp_path)
                )
                print('DOWNLOADING FROM  {}'.format(url))

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

    configuration['cmdclass'] = {'build': BuildResources}

    # Add requests certificates to resource folder.
    import requests.certs

    # opcode is not a virtualenv module, so we can use it to find the stdlib.
    # This is the same trick used by distutils itself it installs itself into
    # the virtualenv
    distutils_path = os.path.join(
        os.path.dirname(opcode.__file__), 'distutils'
    )
    encodings_path = os.path.join(
        os.path.dirname(opcode.__file__), 'encodings'
    )

    include_connect_plugins = []
    resources = [
        (connect_resource_hook, 'resource/hook'),
        (os.path.join(RESOURCE_PATH, 'hook'), 'resource/hook'),
        (requests.certs.where(), 'resource/cacert.pem'),
        (
            os.path.join(
                SOURCE_PATH, 'ftrack_connect_installer', '_version.py'
            ),
            'resource/ftrack_connect_installer_version.py',
        ),
        ('qt.conf', 'qt.conf'),
        ('logo.svg', 'logo.svg'),
        (distutils_path, 'distutils'),
        (encodings_path, 'encodings'),
    ]

    for _, plugin_directory in external_connect_plugins:
        plugin_download_path = os.path.join(
            DOWNLOAD_PLUGIN_PATH, plugin_directory
        )
        include_connect_plugins.append(
            (
                os.path.relpath(plugin_download_path, ROOT_PATH),
                'resource/connect-standard-plugins/' + plugin_directory,
            )
        )

    zip_include_packages = []
    executables = []
    bin_includes = []
    includes = []
    include_files = []

    # Different modules are used on different platforms. Make sure to include
    # all found.
    for dbmodule in ['csv', 'sqlite3', 'ftrack_connect']:
        try:
            __import__(dbmodule)
        except ImportError:
            logging.warning('"{0}" module not available.'.format(dbmodule))
        else:
            includes.append(dbmodule)

    if sys.platform == 'win32':
        # MSI shotcut table list.
        shortcut_table = [
            (
                'DesktopShortcut',
                'DesktopFolder',
                'ftrack Connect',
                'TARGETDIR',
                '[TARGETDIR]ftrack_connect.exe',
                None,
                None,
                None,
                None,
                None,
                None,
                'TARGETDIR',
            ),
            (
                'ProgramMenuShortcut',
                'ProgramMenuFolder',
                'ftrack Connect',
                'TARGETDIR',
                '[TARGETDIR]ftrack_connect.exe',
                None,
                None,
                None,
                None,
                None,
                None,
                'TARGETDIR',
            ),
        ]

        executables.append(
            Executable(
                script='source/ftrack_connect_installer/__main__.py',
                base='Win32GUI',
                target_name='ftrack_connect.exe',
                icon='./logo.ico',
            )
        )

        # Specify upgrade code to a random GUID to ensure the MSI
        # package is upgraded when installing a new version.
        configuration['options']['bdist_msi'] = {
            'upgrade_code': '{6068BD18-65D1-47FC-BE5E-06AA5189C9CB}',
            'initial_target_dir': r'[ProgramFilesFolder]\{0}'.format(
                'ftrack Connect'
            ),
            'data': {'Shortcut': shortcut_table},
            'all_users': True,
            'add_to_path': True,
        }

        # Qt plugins paths
        qt_platforms_path = os.path.join(pyside_path, "plugins", "platforms")
        qt_imageformats_path = os.path.join(
            pyside_path, "plugins", "imageformats"
        )
        qt_iconengines_path = os.path.join(
            pyside_path, "plugins", "iconengines"
        )

        include_files = [
            # Include Qt
            (qt_platforms_path, 'lib/Qt/plugins/platforms'),
            (qt_imageformats_path, 'lib/Qt/plugins/imageformats'),
            (qt_iconengines_path, 'lib/Qt/plugins/iconengines'),
        ]
        # Extend include_files with resources list
        include_files.extend(resources)
        include_files.extend(include_connect_plugins)

        # Force Qt to be included.
        bin_includes = ['PySide2', "shiboken2", "encodings"]

    elif sys.platform == 'darwin':
        # Update Info.plist file with version
        INFO_PLIST_FILE = os.path.join(RESOURCE_PATH, 'Info.plist')
        try:
            with open(INFO_PLIST_FILE, "rb") as file:
                pl = plistlib.load(file)
            if 'CFBundleGetInfoString' in pl.keys():
                pl["CFBundleShortVersionString"] = str(
                    'ftrack Connect {}, copyright: Copyright (c) 2014-2023 ftrack'.format(
                        __version__
                    )
                )
            if 'CFBundleShortVersionString' in pl.keys():
                pl["CFBundleShortVersionString"] = str(__version__)
            with open(INFO_PLIST_FILE, "wb") as file:
                plistlib.dump(pl, file)
        except Exception as e:
            logging.warning(
                'Could not change the version at Info.plist file. \n Error: {}'.format(
                    e
                )
            )

        executables.append(
            Executable(
                script='source/ftrack_connect_installer/__main__.py',
                base=None,
                target_name='ftrack_connect',
                icon='./logo.icns',
            )
        )

        # include_frameworks is an argument of bdist_mac only, all the listed
        # frameworks will be copied to the Frameworks folder.
        include_frameworks = [
            os.path.join(pyside_path, "Qt", "lib", "QtGui.framework"),
            os.path.join(pyside_path, "Qt", "lib", "QtCore.framework"),
            os.path.join(pyside_path, "Qt", "lib", "QtNetwork.framework"),
            os.path.join(pyside_path, "Qt", "lib", "QtSvg.framework"),
            os.path.join(pyside_path, "Qt", "lib", "QtXml.framework"),
            os.path.join(pyside_path, "Qt", "lib", "QtDBus.framework"),
            os.path.join(pyside_path, "Qt", "lib", "QtWidgets.framework"),
            os.path.join(pyside_path, "Qt", "lib", "QtQml.framework"),
            os.path.join(pyside_path, "Qt", "lib", "QtPrintSupport.framework"),
        ]

        # include_resources is an argument of bdist_mac only, all the listed
        # resources will be copied to the Resuorce folder.
        include_resources = resources.copy()
        # Remove qt.conf on macOS as it's not working as expected, so QT plugins
        # and dylib are added on the MacOS folder for now
        include_resources.remove(('qt.conf', 'qt.conf'))

        # Extend resources with the connect plugins.
        include_resources.extend(include_connect_plugins)

        configuration['options']['bdist_mac'] = {
            'iconfile': './logo.icns',
            'bundle_name': bundle_name,
            'custom_info_plist': os.path.join(RESOURCE_PATH, 'Info.plist'),
            'include_frameworks': include_frameworks,
            'include_resources': include_resources,
            # TODO: codesign arguments is not working with PySide2 applications because
            #  the frameworks has to be fixed and signed.
            # 'codesign_identity': os.getenv('CODESIGN_IDENTITY'),
            # 'codesign_deep': True,
            # 'codesign_entitlements': os.path.join(
            #     RESOURCE_PATH, 'entitlements.plist'
            # )
        }

        configuration['options']['bdist_dmg'] = {
            'applications_shortcut': False,
            'volume_label': 'ftrack Connect',
        }

        include_files = [
            # Include Qt
            os.path.join(pyside_path, "Qt", "plugins", "platforms"),
            os.path.join(pyside_path, "Qt", "plugins", "imageformats"),
            os.path.join(pyside_path, "Qt", "plugins", "iconengines"),
            # Include PySide and Shiboken libs
            os.path.join(pyside_path, "libpyside2.abi3.5.13.dylib"),
            os.path.join(shiboken_path, "libshiboken2.abi3.5.13.dylib"),
        ]

    elif sys.platform == 'linux':
        executables.append(
            Executable(
                script='source/ftrack_connect_installer/__main__.py',
                base=None,
                target_name='ftrack_connect',
                icon='./logo.icns',
            )
        )

        # Qt plugins paths
        qt_platforms_path = os.path.join(
            pyside_path, "Qt", "plugins", "platforms"
        )
        qt_imageformats_path = os.path.join(
            pyside_path, "Qt", "plugins", "imageformats"
        )
        qt_iconengines_path = os.path.join(
            pyside_path, "Qt", "plugins", "iconengines"
        )

        include_files = [
            # Include Qt
            (qt_platforms_path, 'lib/Qt/plugins/platforms'),
            (qt_imageformats_path, 'lib/Qt/plugins/imageformats'),
            (qt_iconengines_path, 'lib/Qt/plugins/iconengines'),
        ]

        # Extend include_files with resources list
        include_files.extend(resources)
        include_files.extend(include_connect_plugins)

        # Force Qt to be included.
        bin_includes = [
            'libQt5Core.so',
            'libQt5Gui.so',
            'libQt5Network.so',
            'libQt5Svg.so',
            'libQt5Xml.so',
            'libQt5XcbQpa.so',
            'libQt5DBus.so',
            'libshiboken2',
        ]

    configuration['executables'] = executables

    includes.extend(
        [
            'atexit',  # Required for PySide
            'ftrack_connect',
            'ftrack_api.resource_identifier_transformer.base',
            'ftrack_api.structure.id',
            'encodings',
            'PySide2',
            'shiboken2',
            'Qt',
            'PySide2.QtSvg',
            'PySide2.QtXml',
            'PySide2.QtCore',
            'PySide2.QtWidgets',
            'PySide2.QtGui',
            'ftrack_action_handler',
            'ftrack_action_handler.action',
            'ssl',
            'xml.etree',
            'xml.etree.ElementTree',
            'xml.etree.ElementPath',
            'xml.etree.ElementInclude',
            'http',
            'http.server',
            'webbrowser',
            'html',
            'html.parser',
            'cgi',
            'concurrent',
            'concurrent.futures',
            'darkdetect',
            'ftrack_utils',
        ]
    )

    configuration['options']['build_exe'] = {
        'packages': ['ftrack_connect'],
        'includes': includes,
        "zip_include_packages": [
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
            'webbrowser',
            'darkdetect',
        ],
        'excludes': [
            "dbm.gnu",
            "tkinter",
            "unittest",
            "test",
            '_yaml',
        ],
        'include_files': include_files,
        'bin_includes': bin_includes,
    }


def post_setup(codesign_frameworks=True):
    '''
    Post setup function.

    For MacOS: Fix PySide2 misplaced resources and .plist file on frameworks.
    Instead of having the Resources folder on the root of the framework,
    it should be inside the version number folder, and then this has
    to create a sym link to the root framework folder.
    Check the Qt frameworks structure of the Qt installation of the homebrew.
    Related info in:
    https://stackoverflow.com/questions/19637131/sign-a-framework-for-osx-10-9

    '''
    if sys.platform == 'darwin':
        logging.info(" Fixing PySide2 frameworks.")
        bundle_dir = os.path.join(BUILD_PATH, bundle_name + ".app")
        frameworks_dir = os.path.join(bundle_dir, "Contents", "Frameworks")
        for framework in os.listdir(frameworks_dir):
            full_path = '{}/{}'.format(frameworks_dir, framework)
            framework_name = framework.split(".")[0]
            # Fix PySide2 misplaced resources and .plist file on frameworks.
            bash_move_cmd = (
                'mv "{}/Resources" "{}/Versions/5/Resources"'.format(
                    full_path, full_path
                )
            )
            os.system(bash_move_cmd)
            # The symlink has to be relative, otherwise will not codesign correctly.
            # You can test the codesign after codesign the whole application with:
            # codesign -vvv --deep --strict build/ftrack-connect.app/
            bash_ln_command = (
                'cd "{}"; ln -s "Versions/5/Resources/" "./"'.format(full_path)
            )
            os.system(bash_ln_command)
            if codesign_frameworks:
                logging.info(
                    " Codesigning framework {}".format(framework_name)
                )
                # Codesign each framework
                bashCommand = (
                    'codesign --verbose --deep --strict --force --sign "{}" '
                    '"{}/versions/5/{}"'.format(
                        os.getenv('CODESIGN_IDENTITY'),
                        full_path,
                        framework_name,
                    )
                )
                codesign_result = os.system(bashCommand)
                if codesign_result != 0:
                    raise (
                        Exception(
                            "Codesign of the frameworks not working please make sure "
                            "you have the CODESIGN_IDENTITY, APPLE_USER_NAME "
                            "environment variables and ftrack_connect_sign_pass on "
                            "the keychain."
                        )
                    )
        if not codesign_frameworks:
            logging.info(
                " You should codesign the frameworks before codesign the "
                "application, otherwise it will not be well codesigned."
            )


def create_dmg():
    '''Create DMG on MacOS. Returns the resulting path.'''
    dmg_name = '{0}-{1}.dmg'.format(bundle_name, __version__)
    dmg_path = os.path.join(DIST_PATH, dmg_name)
    if not os.path.exists(DIST_PATH):
        os.makedirs(DIST_PATH)
    elif os.path.exists(dmg_path):
        logging.warning(f'Removing existing image: {dmg_path}')
        os.unlink(dmg_path)
    logging.info('Creating image...')
    dmg_command = 'appdmg resource/appdmg.json "{}"'.format(dmg_path)
    dmg_result = os.system(dmg_command)
    if dmg_result != 0:
        raise Exception("dmg creation not working please check.")
    logging.info(' {} created, creating checksum...'.format(dmg_path))

    # Create md5 sum
    checksum_path = f'{dmg_path}.md5'
    if os.path.exists(checksum_path):
        os.unlink(checksum_path)
    logging.info('Calculating MD5 sum...')
    return_code = os.system(f'md5 "{dmg_path}" > "{checksum_path}"')
    assert return_code == 0, f'MD5 failed: {return_code}'
    logging.info(f' Checksum created: {checksum_path}')
    return dmg_path


def codesign_osx(create_dmg=True, notarize=True):
    '''
    Function to codesign the MacOs Build.

    :note: Important to have an APP-specific password generated on
    https://appleid.apple.com/account/manage
    and have it linked on the keychain under ftrack_connect_sign_pass

    For more information, see https://sites.google.com/ftrack.com/handbook/solutions/integrations/deployment?authuser=0
    '''
    #
    logging.info(
        " Starting codesign process, this will take some time, "
        "please don't stop the process."
    )
    entitlements_path = os.path.join(RESOURCE_PATH, 'entitlements.plist')
    bundle_path = os.path.join(BUILD_PATH, bundle_name + ".app")
    codesign_command = (
        'codesign --verbose --force --options runtime --timestamp --deep --strict '
        '--entitlements "{}" --sign "$CODESIGN_IDENTITY" '
        '"{}"'.format(entitlements_path, bundle_path)
    )
    codesign_result = os.system(codesign_command)
    if codesign_result != 0:
        raise (
            Exception(
                "Codesign not working please make sure you have the "
                "CODESIGN_IDENTITY, APPLE_USER_NAME environment variables and "
                "ftrack_connect_sign_pass on the keychain."
            )
        )
    else:
        logging.info(' Application signed')
    if create_dmg:
        dmg_path = create_dmg()

        if notarize is True:
            logging.info(' Setting up xcode, please enter your sudo password')
            setup_xcode_cmd = 'sudo xcode-select -s /Applications/Xcode.app'
            setup_result = os.system(setup_xcode_cmd)
            if setup_result != 0:
                raise Exception("Setting up xcode not working please check.")
            else:
                logging.info(' xcode setup completed')
            logging.info(' Starting notarize process')
            notarize_command = (
                'xcrun altool --notarize-app --verbose --primary-bundle-id "com.ftrack.connect" '
                '--username $APPLE_USER_NAME --password "@keychain:ftrack_connect_sign_pass" '
                '--file "{}"'.format(dmg_path)
            )
            notarize_result = subprocess.check_output(
                notarize_command, shell=True
            )
            notarize_result = notarize_result.decode("utf-8")
            status, uuid = notarize_result.split('\n')[0:2]
            uuid_num = uuid.split(' = ')[-1]

            # Show History Notarizations.
            notarize_history = (
                'xcrun altool --notarization-history 0 -u $APPLE_USER_NAME '
                '-p "@keychain:ftrack_connect_sign_pass"'
            )
            history_result = os.system(notarize_history)

            logging.info(' Notarize upload status: {}'.format(status))
            logging.info(' Request UUID: {}'.format(uuid_num))

            status = "in progress"
            exit_loop = False
            while status == "in progress" and exit_loop is False:
                # Query status
                notarize_query = (
                    'xcrun altool --notarization-info {} -u $APPLE_USER_NAME '
                    '-p "@keychain:ftrack_connect_sign_pass"'.format(uuid_num)
                )
                query_result = subprocess.check_output(
                    notarize_query, shell=True
                )
                query_result = query_result.decode("utf-8")
                status = query_result.split("Status: ")[-1].split("\n")[0]
                if status == 'success':
                    exit_loop = True
                    staple_app_cmd = 'xcrun stapler staple "{}"'.format(
                        bundle_path
                    )
                    staple_dmg_cmd = 'xcrun stapler staple "{}"'.format(
                        dmg_path
                    )
                    os.system(staple_app_cmd)
                    os.system(staple_dmg_cmd)

                elif status == 'invalid':
                    exit_loop = True
                    log_url = query_result.split("LogFileURL: ")[-1].split(
                        "\n"
                    )[0]
                    raise (
                        Exception(
                            "Notarization failed, please copy the following url "
                            "and check the log:\n{}".format(log_url)
                        )
                    )
                else:
                    response = input(
                        "The status of the current notarization is: {}\n Please "
                        "type exit if you want to manually wait for notarization "
                        "process to finish. Or type the minutes you want to wait "
                        "for automatically check for the notarization process\n "
                        "example: (exit or 5) : ".format(status)
                    )
                    if response == 'exit' or response == 'Exit':
                        exit_loop = True
                        logging.info(
                            ' Please check the status of the notarization using '
                            'the command:\nxcrun altool --notarization-info {} '
                            '-u $APPLE_USER_NAME  '
                            '-p "@keychain:ftrack_connect_sign_pass"'.format(
                                uuid_num
                            )
                        )
                        logging.info(
                            ' Please once notarization is succeed use the '
                            'following command to staple the app and the dmg: \n'
                            'xcrum stapler staple "{}" \n'
                            'xcrun stapler staple "{}"'.format(
                                bundle_path, dmg_path
                            )
                        )
                    else:
                        try:
                            sleep_min = float(response)
                        except Exception as e:
                            exit_loop = True
                            raise Exception(
                                "Could not read the input minutes, please check "
                                "the notarize manually and staple the code after using this command:\n\n{}\n\n"
                                "Response: {}".format(notarize_query, response)
                            )
                        exit_loop = False
                        time.sleep(sleep_min * 60)


import argparse

if sys.platform == 'darwin':
    parser = argparse.ArgumentParser(
        prog='setup.py bdist_mac',
        add_help=True,
        description=''' Override help for Connect build in MacOs. These are the 
        accepted arguments for connect build. ''',
        epilog='Make sure you have the CODESIGN_IDENTITY and APPLE_USER_NAME '
        'environment variables and the ftrack_connect_sign_pass on the '
        'keychain before codesign. Also make sure to have appdmg installed '
        'by running "npm install -g appdmg"',
    )
    parser.add_argument(
        '-cf',
        '--codesign_frameworks',
        action='store_true',
        help='Codesign the frameworks on the Frameworks folder on MacOS',
    )
    parser.add_argument(
        '-cs',
        '--codesign',
        action='store_true',
        help='Codesign the .app in MacOS',
    )
    parser.add_argument(
        '-dmg',
        '--create_dmg',
        action='store_true',
        help='Create the dmg file for MacOS',
    )
    parser.add_argument(
        '-not',
        '--notarize',
        action='store_true',
        help='Notarize the dmg application after codesign',
    )

elif sys.platform == 'win32':
    parser = argparse.ArgumentParser(
        prog='setup.py bdist_msi|build_exe',
        add_help=True,
        description=''' Override help for Connect build in Windows. These are the 
        accepted arguments for connect build. ''',
        epilog='Make sure you have installed Java & gloud CLI tools and have '
        'authenticated with Google cloud. ',
    )
    parser.add_argument(
        '-cs',
        '--codesign',
        action='store_true',
        help='Codesign Connect .exe and msi install on Windows',
    )
elif sys.platform == 'linux':
    parser = argparse.ArgumentParser(
        prog='setup.py build_exe',
        add_help=True,
        description=''' Override help for Connect build in Linux. These are the 
            accepted arguments for connect build. ''',
        epilog='Make sure you have patchelf installed in your Python environment.',
    )
    parser.add_argument(
        '-cb',
        '--create_deployment',
        action='store_true',
        help='Create compressed tar deployment with MD5 checksum',
    )
else:
    raise Exception('Unsupported build platform!')

args, unknown = parser.parse_known_args()
sys.argv = [sys.argv[0]] + unknown


def clean_download_dir():
    if os.path.exists(DOWNLOAD_PLUGIN_PATH):
        shutil.rmtree(DOWNLOAD_PLUGIN_PATH)


def codesign_windows(path):
    '''Codesign artifact *path* using jsign tool in Windows'''
    return_code = os.system(f'codesign.bat {path}')
    logging.info(f'Exitcode from code sign: {return_code}')


def add_codesign_cx_freeze_windows():
    '''Redefine cx_Freeze build_exe run function to support code sign after the
    executable has been built'''
    from cx_Freeze.dist import build_exe

    build_exe_run = build_exe.run

    def run(self):
        build_exe_run(self)
        exe_path = (
            f'{self.build_exe}\\{self.distribution.executables[0].target_name}'
        )
        codesign_windows(exe_path)

    build_exe.run = run


if sys.platform == 'win32':
    if args.codesign:
        add_codesign_cx_freeze_windows()

# Call main setup.
setup(**configuration)

clean_download_dir()

if sys.platform == 'darwin':
    post_setup(codesign_frameworks=args.codesign_frameworks)
    if args.codesign:
        codesign_osx(create_dmg=args.create_dmg, notarize=args.notarize)
    elif args.create_dmg:
        create_dmg()
elif sys.platform == 'win32':
    if args.codesign and 'bdist_msi' in sys.argv:
        msi_name = '{0}-{1}-win64.msi'.format(bundle_name, __version__)
        codesign_windows(f'dist\\{msi_name}')
elif sys.platform == 'linux':
    if args.create_deployment:
        try:
            os.chdir(os.path.join(ROOT_PATH, 'build'))
            exe_path = os.listdir(os.getcwd())[0]
            # Detect platform
            path_os_desc = '/etc/os-release'
            assert os.path.exists(path_os_desc), 'Not a supported Linux OS!'
            with open(path_os_desc, 'r') as f:
                os_desc = f.read()
            linux_distro = ''
            if os_desc.lower().find('centos-7') > -1:
                linux_distro = 'C7'
            elif os_desc.lower().find('centos-8') > -1:
                linux_distro = 'C8'
            elif os_desc.lower().find('rocky-linux-9') > -1:
                linux_distro = 'R9'
            else:
                raise Exception('Not a supported Linux distro!')
            target_path = os.path.join(
                DIST_PATH,
                f'ftrack-connect-installer-{__version__}-{linux_distro}.tar.gz',
            )
            if not os.path.exists(os.path.dirname(target_path)):
                os.makedirs(os.path.dirname(target_path))
            elif os.path.exists(target_path):
                os.unlink(target_path)
            logging.info('Compressing...')
            return_code = os.system(
                f"tar -zcvf {target_path} {os.path.basename(exe_path)} --transform 's/{os.path.basename(exe_path)}/ftrack-connect-installer/'"
            )
            assert return_code == 0, f'TAR compress failed: {return_code}'
            # Create md5 sum
            checksum_path = f'{target_path}.md5'
            if os.path.exists(checksum_path):
                os.unlink(checksum_path)
            logging.info('Calculating MD5 sum...')
            return_code = os.system(f'md5sum {target_path} > {checksum_path}')
            assert return_code == 0, f'MD5 failed: {return_code}'
            logging.info(f' {target_path} created with checksum.')
        except:
            import traceback

            logging.warning(traceback.format_exc())
        finally:
            os.chdir(ROOT_PATH)
