# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

'''
requires :
pyside2 = 5.14.1


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
DOWNLOAD_PLUGIN_PATH = os.path.join(
    BUILD_PATH,
    'plugin-downloads-{0}'.format(
        datetime.datetime.now().strftime('%y-%m-%d-%H-%M-%S')
    ),
)
AWS_PLUGIN_DOWNLOAD_PATH = (
    'https://download.ftrack.com/ftrack-connect/integrations/'
)


# Fetch Connect version
try:
    from importlib.metadata import version

    VERSION = version('ftrack-connect')
except ImportError:
    from pkg_resources import get_distribution

    VERSION = get_distribution('ftrack-connect').version

# Write to _version.py

version_template = '''
# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

__version__ = {version!r}
'''

with open(
    os.path.join(SOURCE_PATH, 'ftrack_connect_installer', '_version.py'), 'w'
) as file:
    file.write(version_template.format(version=VERSION))

print('BUILDING VERSION : {}'.format(VERSION))


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
    version="2.1.2",
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
                        VERSION
                    )
                )
            if 'CFBundleShortVersionString' in pl.keys():
                pl["CFBundleShortVersionString"] = str(VERSION)
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
            os.path.join(pyside_path, "libpyside2.abi3.5.15.dylib"),
            os.path.join(shiboken_path, "libshiboken2.abi3.5.15.dylib"),
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
        dmg_name = '{0}-{1}.dmg'.format(bundle_name, VERSION)
        dmg_path = os.path.join(BUILD_PATH, dmg_name)
        dmg_command = 'appdmg resource/appdmg.json "{}"'.format(dmg_path)
        dmg_result = os.system(dmg_command)
        if dmg_result != 0:
            raise (Exception("dmg creation not working please check."))
        else:
            logging.info(' {} Created.'.format(dmg_path))
        if notarize is True:
            logging.info(' Setting up xcode, please enter your sudo password')
            setup_xcode_cmd = 'sudo xcode-select -s /Applications/Xcode.app'
            setup_result = os.system(setup_xcode_cmd)
            if setup_result != 0:
                raise (Exception("Setting up xcode not working please check."))
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


if sys.platform == 'darwin':
    import argparse

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
    args, unknown = parser.parse_known_args()
    sys.argv = [sys.argv[0]] + unknown
    osx_args = args


def clean_download_dir():
    if os.path.exists(DOWNLOAD_PLUGIN_PATH):
        shutil.rmtree(DOWNLOAD_PLUGIN_PATH)


# Call main setup.
setup(**configuration)

clean_download_dir()
if sys.platform == 'darwin':
    if 'osx_args' in locals():
        post_setup(codesign_frameworks=osx_args.codesign_frameworks)
        if osx_args.codesign:
            codesign_osx(
                create_dmg=osx_args.create_dmg, notarize=osx_args.notarize
            )
        elif osx_args.create_dmg:
            dmg_name = '{0}-{1}.dmg'.format(bundle_name, VERSION)
            dmg_path = os.path.join(BUILD_PATH, dmg_name)
            dmg_command = 'appdmg resource/appdmg.json "{}"'.format(dmg_path)
            dmg_result = os.system(dmg_command)
            if dmg_result != 0:
                raise (Exception("dmg creation not working please check."))
            else:
                logging.info(' {} Created.'.format(dmg_path))
