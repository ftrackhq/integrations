import subprocess
import os
import re
import logging
import json
import plistlib

import PyInstaller.__main__


VERSION_TEMPLATE = '''
# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

__version__ = '{version}'
'''


class AppInstaller(object):
    @property
    def bundle_name(self):
        return self._bundle_name

    @property
    def version(self):
        return self._version

    @property
    def icon_path(self):
        return self._icon_path

    @property
    def root_path(self):
        return self._root_path

    @property
    def dist_path(self):
        return self._dist_path

    @property
    def build_path(self):
        return self._build_path

    @property
    def entry_file_path(self):
        return self._entry_file_path

    def __init__(
        self, bundle_name, version, icon_path, root_path, entry_file_path
    ):
        self._bundle_name = bundle_name
        self._version = version
        self._icon_path = icon_path
        self._root_path = root_path
        self._dist_path = os.path.join(self.root_path, "dist")
        self._build_path = os.path.join(self.root_path, "build")
        self._entry_file_path = entry_file_path

    def generate_executable(self):
        # TODO: we should generalize this file and remove all references to connect
        version_file_path = self._generate_version_file()

        pyinstaller_commands = [
            self.entry_file_path,
            '--windowed',
            '--name',
            self.bundle_name,
            '--collect-all',
            'ftrack_connect',
            '--icon',
            self.icon_path,
            '--distpath',
            self.dist_path,
            '--workpath',
            self.build_path,
            '--add-data',
            version_file_path + ':ftrack_connect',
            '-y',
            '--clean',
        ]
        try:
            PyInstaller.__main__.run(pyinstaller_commands)
        except Exception as e:
            f'pyinstaller failed to build {self.bundle_name}! Exitcode: {e}'

    def _generate_version_file(self):
        '''
        Store the version of the app to a __version__.py so it can be picked
        from the init file when start fronm the installer.
        '''
        version_file_path = os.path.join(self.root_path, '__version__.py')

        with open(version_file_path, 'w') as file:
            file.write(VERSION_TEMPLATE.format(version=self.version))

        return version_file_path


class WindowsAppInstaller(AppInstaller):
    os_root_folder = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "windows"
    )
    codesing_folder = os.path.join(os_root_folder, "codesign")
    INNOSETUP_PATH = "C:\\Program Files (x86)\\Inno Setup 6\\ISCC.exe"

    def codesign(self, path):
        '''Codesign artifact *path* using jsign tool in Windows'''
        bat_file = os.path.join(self.codesing_folder, "codesign.bat")
        return_code = os.system(f'{bat_file} "{path}"')
        logging.info(f'Exitcode from code signing "{path}": {return_code}')

    def generate_installer_package(self, codesign=True):
        # TODO: need to make the ftrack Connect.iss generic
        '''Create installer executable on Windows. Returns the resulting path.'''

        if not os.path.exists(self.INNOSETUP_PATH):
            raise Exception(f'Inno Setup not found at: {self.INNOSETUP_PATH}')

        # Load template and inject version
        with open(
            os.path.join(self.os_root_folder, 'ftrack Connect.iss'),
            "r",
        ) as f_template:
            template = f_template.read()
            temp_iss_path = os.path.join(
                self.build_path, "installer", 'ftrack Connect.iss'
            )
            if not os.path.exists(os.path.dirname(temp_iss_path)):
                os.makedirs(os.path.dirname(temp_iss_path))
            final_content = template.replace('${VERSION}', self.version)
            final_content = final_content.replace(
                '${DIST_PATH}', self.dist_path
            )
            final_content = final_content.replace(
                '${ROOT_PATH}', self.root_path
            )
            with open(temp_iss_path, "w") as f_out:
                f_out.write(final_content)

        # Run innosetup, check exitcode
        innosetup_commands = [self.INNOSETUP_PATH, temp_iss_path]

        return_code = subprocess.check_call(innosetup_commands)

        assert (
            return_code == 0
        ), f'Inno Setup failed to build installer! Exitcode: {return_code}'

        installer_path = os.path.join(
            self.dist_path, f"ftrack_connect-{self.version}-win64.exe"
        )
        if not os.path.exists(installer_path):
            raise Exception(
                f'Expected installer not found at: {installer_path}'
            )

        if codesign:
            self.codesign(installer_path)

        return installer_path


class MacOSAppInstaller(AppInstaller):
    os_root_folder = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "macOS"
    )
    codesing_folder = os.path.join(os_root_folder, "codesign")

    @property
    def bundle_path(self):
        return os.path.join(self.dist_path, f'{self.bundle_name}.app')

    def generate_executable(self):
        super(MacOSAppInstaller, self).generate_executable()
        self._update_info_plist()

    def codesign(self, path):
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
        entitlements_path = os.path.join(
            self.codesing_folder, 'entitlements.plist'
        )
        codesign_command = (
            'codesign --verbose --force --options runtime --timestamp --deep --strict '
            '--entitlements "{}" --sign "$MACOS_CERTIFICATE_NAME" '
            '"{}"'.format(entitlements_path, path)
        )
        codesign_result = os.system(codesign_command)
        if codesign_result != 0:
            raise (
                Exception(
                    "Codesign not working please make sure you have the "
                    "MACOS_CERTIFICATE_NAME, environment variables and "
                    "ftrack_connect_sign_pass on the keychain."
                )
            )
        else:
            logging.info(' Application signed')

    def generate_installer_package(self, codesign=True):
        '''Create DMG on MacOS with checksum. Returns the resulting path.'''
        assert os.path.isdir(self.bundle_path), 'No bundle output where found!'

        if codesign:
            self.codesign(self.bundle_path)

        dmg_name = '{0}-{1}-macOS.dmg'.format(
            self.bundle_name.replace(' ', '_').lower(), self.version
        )
        dmg_path = os.path.join(self.dist_path, dmg_name)
        if not os.path.exists(self.dist_path):
            os.makedirs(self.dist_path)
        elif os.path.exists(dmg_path):
            logging.warning(f'Removing existing image: {dmg_path}')
            os.unlink(dmg_path)
        logging.info('Creating image...')

        app_dmg_args = {
            "title": f"{self.bundle_name}",
            "background": f"{self.os_root_folder}/dmg_image.png",
            "icon-size": 70,
            "contents": [
                {"x": 390, "y": 180, "type": "link", "path": "/Applications"},
                {
                    "x": 130,
                    "y": 180,
                    "type": "file",
                    "path": f"{self.bundle_path}",
                },
            ],
        }

        # Define the path for the JSON file within the dist_folder
        json_file_path = f"{self.build_path}/app_dmg_args.json"

        # Serialize the dictionary to a JSON file
        with open(json_file_path, 'w') as json_file:
            json.dump(app_dmg_args, json_file, indent=4)

        dmg_command = f'appdmg {json_file_path} "{dmg_path}"'
        dmg_result = os.system(dmg_command)
        if dmg_result != 0:
            raise Exception("dmg creation not working please check.")
        logging.info(
            ' {} created, calculating md5 checksum...'.format(dmg_path)
        )

        # Create md5 sum
        checksum_path = f'{dmg_path}.md5'
        if os.path.exists(checksum_path):
            os.unlink(checksum_path)
        return_code = os.system(f'md5 "{dmg_path}" > "{checksum_path}"')
        assert return_code == 0, f'MD5 failed: {return_code}'
        logging.info(f'Checksum created: {checksum_path}')

        if codesign:
            # Notarize the dmg
            store_credentials_command = 'xcrun notarytool store-credentials "notarytool-profile" --apple-id "$PROD_MACOS_NOTARIZATION_APPLE_ID" --team-id "$PROD_MACOS_NOTARIZATION_TEAM_ID" --password "$PROD_MACOS_NOTARIZATION_PWD"'
            os.system(store_credentials_command)
            logging.info(' Setting up xcode, please enter your sudo password')
            setup_xcode_cmd = 'sudo xcode-select -s /Applications/Xcode.app'
            setup_result = os.system(setup_xcode_cmd)
            if setup_result != 0:
                raise Exception("Setting up xcode not working please check.")
            else:
                logging.info(' xcode setup completed')
            logging.info(' Starting notarize process')
            notarize_command = 'xcrun notarytool submit --verbose --keychain-profile "notarytool-profile" --wait {}'.format(
                dmg_path
            )

            notarize_result = subprocess.check_output(
                notarize_command, shell=True, text=True
            )

            # Log the full output
            logging.info(f"notarize_result: {notarize_result}")

            # Use regular expressions to search for the submission ID and final status
            id_match = re.search(r'id: (\S+)', notarize_result)
            status_matches = re.findall(r'status: (\S+)', notarize_result)

            submission_id = None
            final_status = None

            if id_match:
                # Extract the submission ID
                submission_id = id_match.group(1)
                logging.info(f"Submission ID: {submission_id}")
            else:
                logging.error("Submission ID not found in the output.")

            if status_matches:
                # Extract the final status
                final_status = status_matches[-1] if status_matches else None
                logging.info(f"Final Status: {final_status}")
            else:
                logging.error("Final status not found in the output.")

            if final_status == 'Accepted':
                staple_app_cmd = 'xcrun stapler staple "{}"'.format(
                    self.bundle_path
                )
                staple_dmg_cmd = 'xcrun stapler staple "{}"'.format(dmg_path)
                os.system(staple_app_cmd)
                os.system(staple_dmg_cmd)

            else:
                # Show notarize info
                notarize_info = 'xcrun notarytool info --keychain-profile "notarytool-profile" {}'.format(
                    submission_id
                )
                query_result = subprocess.check_output(
                    notarize_info, shell=True, text=True
                )
                logging.info("Notarize info: {}".format(query_result))

                # Fetch notary Log
                notarize_log = 'xcrun notarytool log --keychain-profile "notarytool-profile" {}'.format(
                    submission_id
                )
                log_result = subprocess.check_output(
                    notarize_log, shell=True, text=True
                )
                logging.info("Notarize log: {}".format(log_result))

                raise Exception(
                    "Notarization failed, please check the log: \n{}".format(
                        log_result
                    )
                )
        return dmg_path

    def _update_info_plist(self):
        plist_path = f"{self.bundle_path}/Contents/Info.plist"
        try:
            with open(plist_path, 'rb') as fp:
                plist = plistlib.load(fp)

            # Set copyright
            plist[
                "CFBundleGetInfoString"
            ] = f'{self.bundle_name} {self.version}, copyright: Copyright (c) 2024 ftrack'
            # Set the desired version
            plist['CFBundleShortVersionString'] = self.version

            with open(plist_path, 'wb') as fp:
                plistlib.dump(plist, fp)
        except Exception as e:
            logging.warning(
                'Could not change the version at Info.plist file. \n Error: {}'.format(
                    e
                )
            )


class LinuxAppInstaller(AppInstaller):
    def codesign(self):
        pass

    def generate_installer_package(self, codesign=False):
        try:
            os.chdir(self.dist_path)
            # Detect platform
            path_os_desc = '/etc/os-release'
            assert os.path.exists(path_os_desc), 'Not a supported Linux OS!'
            with open(path_os_desc, 'r') as f:
                os_desc = f.read()
            if os_desc.lower().find('centos-7') > -1:
                linux_distro = 'C7'
            elif os_desc.lower().find('centos-8') > -1:
                linux_distro = 'C8'
            elif os_desc.lower().find('rocky-linux-8') > -1:
                linux_distro = 'R8'
            elif os_desc.lower().find('rocky-linux-9') > -1:
                linux_distro = 'R9'
            else:
                raise Exception('Not a supported Linux distro!')
            target_path = os.path.join(
                self.dist_path,
                f'ftrack_connect-{self.version}-{linux_distro}.tar.gz',
            )
            if not os.path.exists(os.path.dirname(target_path)):
                os.makedirs(os.path.dirname(target_path))
            elif os.path.exists(target_path):
                os.unlink(target_path)
            logging.info('Compressing...')
            archive_commands = [
                "tar",
                "-zcvf",
                target_path,
                self.bundle_name,
                "--transform",
                f"s/{self.bundle_name}/ftrack-connect/",
            ]
            return_code = subprocess.check_call(archive_commands)
            assert return_code == 0, f'TAR compress failed: {return_code}'
            # Create md5 sum
            checksum_path = f'{target_path}.md5'
            if os.path.exists(checksum_path):
                os.unlink(checksum_path)
            logging.info(
                f'Created: {target_path}, calculating md5 checksum...'
            )
            return_code = os.system(f'md5sum {target_path} > {checksum_path}')
            assert return_code == 0, f'md5 failed: {return_code}'
            logging.info(f'Checksum created: {checksum_path}')
        finally:
            # Go back to root path
            os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__))))
