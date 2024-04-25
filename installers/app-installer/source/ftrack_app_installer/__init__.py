import subprocess
import os
import re
import logging

import PyInstaller.__main__


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
            '-y',
            '--clean',
        ]
        try:
            PyInstaller.__main__.run(pyinstaller_commands)
        except Exception as e:
            f'pyinstaller failed to build {self.bundle_name}! Exitcode: {e}'
        # TODO: on MACOs the resultant info.plist generated should be contain CFBundleGetInfoString with 'ftrack Connect {}, copyright: Copyright (c) 2024 ftrack'.format(VERSION)
        #  And the important one, which is: CFBundleShortVersionString with the version number


class WindowsAppInstaller(AppInstaller):
    os_root_folder = "windows"
    codesing_folder = os.path.join(os_root_folder, "codesign")

    def codesign(self, path):
        '''Codesign artifact *path* using jsign tool in Windows'''
        return_code = os.system(
            f'{self.codesing_folder}\\codesign.bat "{path}"'
        )
        logging.info(f'Exitcode from code signing "{path}": {return_code}')

    def generate_installer_package(self, codesign=True):
        # TODO: need to make the ftrack Connect.iss generic
        '''Create installer executable on Windows. Returns the resulting path.'''

        INNOSETUP_PATH = "C:\\Program Files (x86)\\Inno Setup 6\\ISCC.exe"
        if not os.path.exists(INNOSETUP_PATH):
            raise Exception(f'Inno Setup not found at: {INNOSETUP_PATH}')

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
            with open(temp_iss_path, "w") as f_out:
                f_out.write(template.replace('${VERSION}', self.version))

        # Run innosetup, check exitcode
        innosetup_commands = [INNOSETUP_PATH, temp_iss_path]

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
    os_root_folder = "macOS"
    codesing_folder = os.path.join(os_root_folder, "codesign")

    @property
    def bundle_path(self):
        return os.path.join(self.dist_path, f'{self.bundle_name}.app')

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
            "background": "dmg_image.png",
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
        dmg_command = f'appdmg {app_dmg_args} "{dmg_path}"'
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


class LinuxAppInstaller(AppInstaller):
    def codesign(self):
        pass

    def generate_installer_package(self):
        pass
