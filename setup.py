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
import plistlib
import pkg_resources
import subprocess
import time

# # Package and dependencies versions.

ftrack_connect_version = '2.0'
ftrack_action_handler_version = '0.2.1'
bundle_name = 'ftrack-connect'
import PySide2
import shiboken2

pyside_path = os.path.join(PySide2.__path__[0])
shiboken_path = os.path.join(shiboken2.__path__[0])

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
# setup(**configuration)

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

    # opcode is not a virtualenv module, so we can use it to find the stdlib.
    # This is the same trick used by distutils itself it installs itself into
    # the virtualenv
    distutils_path = os.path.join(os.path.dirname(opcode.__file__), 'distutils')
    encodings_path = os.path.join(os.path.dirname(opcode.__file__), 'encodings')
    #
    resources = [
        (connect_resource_hook, 'resource/hook'),
        (os.path.join(RESOURCE_PATH, 'hook'), 'resource/hook'),
        (requests.certs.where(), 'resource/cacert.pem'),
        (
            os.path.join(SOURCE_PATH, 'ftrack_connect_package', '_version.py'),
            'resource/ftrack_connect_package_version.py'
        ),
        ('qt.conf', 'qt.conf'),
        (distutils_path, 'distutils'),
        (encodings_path, 'encodings')
    ]


    zip_include_packages = []
    executables = []
    bin_includes = []
    includes = []
    include_files = []

    # Different modules are used on different platforms. Make sure to include
    # all found.
    for dbmodule in ['csv', 'sqlite3']:
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

        executables.append(
            Executable(
                script='source/ftrack_connect_package/__main__.py',
                base='Win32GUI',
                #base=None,
                target_name='ftrack_connect_package.exe',
                icon='./logo.ico',
            )
        )

        # Specify upgrade code to a random GUID to ensure the MSI
        # package is upgraded when installing a new version.
        configuration['options']['bdist_msi'] = {
            'upgrade_code': '{6068BD18-65D1-47FC-BE5E-06AA5189C9CB}',
            'initial_target_dir': r'[ProgramFilesFolder]\{0}-{1}'.format(
                'ftrack-connect-package', VERSION
            ),
            'data': {'Shortcut': shortcut_table},
            'all_users': True, # Enable these when out of beta of connect 2
            'add_to_path': True
        }

        # Qt plugins paths
        qt_platforms_path = os.path.join(pyside_path, "plugins", "platforms")
        qt_imageformats_path = os.path.join(pyside_path, "plugins", "imageformats")
        qt_iconengines_path = os.path.join(pyside_path, "plugins", "iconengines")

        include_files = [
            # Include Qt
            (qt_platforms_path, 'lib/Qt/plugins/platforms'),
            (qt_imageformats_path, 'lib/Qt/plugins/imageformats'),
            (qt_iconengines_path, 'lib/Qt/plugins/iconengines'),
        ]
        #Extend include_files with resources list
        include_files.extend(resources)

        # Force Qt to be included.
        bin_includes = [
            "PySide2",
            "shiboken2",
            "encodings"
        ]

    elif sys.platform == 'darwin':

        # Update Info.plist file with version
        INFO_PLIST_FILE = os.path.join(RESOURCE_PATH, 'Info.plist')
        try:
            with open(INFO_PLIST_FILE, "rb") as file:
                pl = plistlib.load(file)
            if 'CFBundleGetInfoString' in pl.keys():
                pl["CFBundleShortVersionString"] = str(
                    'Ftrack Connect {}, copyright: Copyright (c) 2014-2020 ftrack'.format(
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
                script='source/ftrack_connect_package/__main__.py',
                base=None,
                target_name='ftrack_connect_package',
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
            os.path.join(pyside_path, "Qt", "lib", "QtPrintSupport.framework")
        ]

        # include_resources is an argument of bdist_mac only, all the listed
        # resources will be copied to the Resuorce folder.
        include_resources = resources.copy()
        # Remove qt.conf on macOS as it's not working as expected, so QT plugins
        # and dylib are added on the MacOS folder for now
        include_resources.remove(('qt.conf', 'qt.conf'))
        include_resources.remove((requests.certs.where(), 'resource/cacert.pem'))

        configuration['options']['bdist_mac'] = {
            'iconfile': './logo.icns',
            'bundle_name': bundle_name,
            'custom_info_plist': os.path.join(
                RESOURCE_PATH, 'Info.plist'
            ),
            'include_frameworks': include_frameworks,
            'include_resources': include_resources,
            # TODO: codesign is not working with PySide2 applications because
            #  the frameworks has to be fixed and signed.
            # 'codesign_identity': os.getenv('CODESIGN_IDENTITY'),
            # 'codesign_deep': True,
            # 'codesign_entitlements': os.path.join(
            #     RESOURCE_PATH, 'entitlements.plist'
            # )
        }

        configuration['options']['bdist_dmg'] = {
            'applications_shortcut': False,
            'volume_label': 'ftrack-connect-{0}'.format(VERSION)
        }

        include_files = [
            #Include Qt
            os.path.join(pyside_path, "Qt", "plugins", "platforms"),
            os.path.join(pyside_path, "Qt", "plugins", "imageformats"),
            os.path.join(pyside_path, "Qt", "plugins", "iconengines"),
            #Include PySide and Shiboken libs
            os.path.join(pyside_path, "libpyside2.abi3.5.15.dylib"),
            os.path.join(shiboken_path, "libshiboken2.abi3.5.15.dylib"),
            (requests.certs.where(), 'resource/cacert.pem'),
        ]

    elif sys.platform == 'linux':

        executables.append(
            Executable(
                script='source/ftrack_connect_package/__main__.py',
                base=None,
                target_name='ftrack_connect_package',
                icon='./logo.icns',
            )
        )

        # Qt plugins paths
        qt_platforms_path = os.path.join(pyside_path, "Qt", "plugins", "platforms")
        qt_imageformats_path = os.path.join(pyside_path, "Qt", "plugins", "imageformats")
        qt_iconengines_path = os.path.join(pyside_path, "Qt", "plugins", "iconengines")

        include_files = [
            # Include Qt
            (qt_platforms_path, 'lib/Qt/plugins/platforms'),
            (qt_imageformats_path, 'lib/Qt/plugins/imageformats'),
            (qt_iconengines_path, 'lib/Qt/plugins/iconengines')
            ]

        # Extend include_files with resources list
        include_files.extend(resources)

        # Force Qt to be included.
        bin_includes = [
            'libQt5Core.so',
            'libQt5Gui.so',
            'libQt5Network.so',
            'libQt5Svg.so',
            'libQt5Xml.so',
            'libQt5XcbQpa.so',
            'libQt5DBus.so',
            'libshiboken2'
        ]

    configuration['executables'] = executables

    includes.extend([
        'atexit',  # Required for PySide
        'ftrack_connect',
        'ftrack_api.resource_identifier_transformer.base',
        'ftrack_api.structure.id',
        'encodings',
        'PySide2',
        'Qt',
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
        #"include_msvcr": True,
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

    configuration['setup_requires'].extend(
        configuration['install_requires']
    )

def post_setup(codesign_frameworks = True):
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
        logging.info(
            " Fixing PySide2 frameworks."
        )
        bundle_dir = os.path.join(BUILD_PATH, bundle_name + ".app")
        frameworks_dir = os.path.join(bundle_dir,  "Contents", "Frameworks")
        for framework in os.listdir(frameworks_dir):
            full_path = '{}/{}'.format(frameworks_dir, framework)
            framework_name = framework.split(".")[0]
            # Fix PySide2 misplaced resources and .plist file on frameworks.
            bash_move_cmd = 'mv "{}/Resources" "{}/Versions/5/Resources"'.format(
                full_path,
                full_path
            )
            os.system(bash_move_cmd)
            # The symlink has to be relative, otherwise will not codesign correctly.
            # You can test the codesign after codesign the whole application with:
            # codesign -vvv --deep --strict build/ftrack-connect.app/
            bash_ln_command = 'cd {}; ln -s "Versions/5/Resources/" "./"'.format(
                full_path
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
                        framework_name
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
        '--entitlements "{}" --sign $CODESIGN_IDENTITY '
        '{}'.format(entitlements_path, bundle_path)
    )
    codesign_result = os.system(codesign_command)
    if codesign_result != 0:
        raise(
            Exception(
                "Codesign not working please nake sure you have the "
                "CODESIGN_IDENTITY, APPLE_USER_NAME environment variables and "
                "ftrack_connect_sign_pass on the keychain."
            )
        )
    else:
        logging.info(' Application signed')
    if create_dmg:
        dmg_name = '{0}-{1}.dmg'.format(bundle_name, VERSION)
        dmg_path = os.path.join(BUILD_PATH, dmg_name)
        dmg_command = (
            'appdmg resource/appdmg.json {}'.format(dmg_path)
        )
        dmg_result = os.system(dmg_command)
        if dmg_result != 0:
            raise (Exception("dmg creation not working please check."))
        else:
            logging.info(' {} Created.'.format(dmg_path))
        if notarize == True:
            logging.info(' Setting up xcode, please eter your sudo password')
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
                '--file {}'.format(dmg_path)
            )
            notarize_result = subprocess.check_output(notarize_command, shell=True)
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
            while status == "in progress" and exit_loop == False:
                # Query status
                notarize_query = (
                    'xcrun altool --notarization-info {} -u $APPLE_USER_NAME '
                    '-p "@keychain:ftrack_connect_sign_pass"'.format(uuid_num)
                )
                query_result = subprocess.check_output(notarize_query, shell=True)
                query_result = query_result.decode("utf-8")
                status = query_result.split("Status: ")[-1].split("\n")[0]
                if status == 'success':
                    exit_loop = True
                    staple_app_cmd = 'xcrun stapler staple {}'.format(bundle_path)
                    staple_dmg_cmd = 'xcrun stapler staple {}'.format(dmg_path)
                    os.system(staple_app_cmd)
                    os.system(staple_dmg_cmd)

                elif status == 'invalid':
                    exit_loop = True
                    log_url = query_result.split("LogFileURL: ")[-1].split("\n")[0]
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
                            '-p "@keychain:ftrack_connect_sign_pass"'.format(uuid_num)
                        )
                        logging.info(
                            ' Please once notarization is succed use the '
                            'following command to staple the app and the dmg: \n'
                            'xcrum stapler staple {} \n'
                            'xcrun stapler staple {}'.format(bundle_path, dmg_path)
                        )
                    else:
                        try:
                            sleep_min = float(response)
                        except Exception as e:
                            exit_loop = True
                            raise (
                                "Could not read the imput minutes, please check "
                                "the notarize manually and staple the code after. \n"
                                "Error: {}".format(e)
                            )
                        exit_loop = False
                        time.sleep(sleep_min*60)


if sys.platform == 'darwin':
    import argparse

    parser = argparse.ArgumentParser(
        prog='setup.py bdist_mac',
        add_help=True,
        description=''' Override help for Connect build in MacOs. These are the 
        accepted arguments for connect build. ''',
        epilog='Make sure you have the CODESIGN_IDENTITY and APPLE_USER_NAME '
               'environment variables and the ftrack_connect_sign_pass on the '
               'keychain before codesign.'
    )
    parser.add_argument(
        '-cf', '--codesign_frameworks',
        action='store_true',
        help='Codesign the frameworks on the Frameworks folder on MacOS',
    )
    parser.add_argument(
        '-cs', '--codesign', action='store_true', help='Codesign the .app in MacOS'
    )
    parser.add_argument(
        '-dmg', '--create_dmg', action='store_true',
        help='Create the dmg file for MacOS'
    )
    parser.add_argument(
        '-not', '--notarize', action='store_true',
        help='Notarice the dmg application after codesign'
    )
    args, unknown = parser.parse_known_args()
    sys.argv = [sys.argv[0]] + unknown
    osx_args = args

# Call main setup.
setup(**configuration)
if sys.platform == 'darwin':
    if 'osx_args' in locals():
        post_setup(codesign_frameworks=osx_args.codesign_frameworks)
        if osx_args.codesign:
            codesign_osx(create_dmg=osx_args.create_dmg, notarize=osx_args.notarize)