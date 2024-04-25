import subprocess


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
    def dist_path(self):
        return self._dist_path

    @property
    def source_file(self):
        return self._source_file

    def __init__(
        self, bundle_name, version, icon_path, dist_path, source_file
    ):
        self._bundle_name = bundle_name
        self._version = version
        self._icon_path = icon_path
        self._dist_path = dist_path
        self._source_file = source_file

    def generate_executable(self):
        pyinstaller_commands = [
            'pyinstaller',
            '--windowed',
            '--name',
            self.bundle_name,
            '--collect-all',
            'ftrack_connect',
            '--icon',
            self.icon_path,
            self.source_file,
        ]
        '''
        '--add-data',
            temp_version_path + ':ftrack_connect', # temp_version_path = tempfile.gettempdir() + '/_version.py' // we will have the _version that defines  the installer version and the connect_version
            '--add-data',
            os.path.join(
                CONNECT_INSTALLER_PATH, # PAth to the installer
                'resource',
                'hook',
                'ftrack_connect_installer_version_information.py',
            )
            + ':ftrack_connect/hook/ftrack_connect_installer_version_information.py',
        '''
        exitcode = subprocess.check_call(pyinstaller_commands)
        assert (
            exitcode == 0
        ), f'pyinstaller failed to build Connect! Exitcode: {exitcode}'


class WindowsAppInstaller(AppInstaller):
    def codesign(self):
        pass

    def generate_installer_package(self):
        pass


class MacOSAppInstaller(AppInstaller):
    def codesign(self):
        pass

    def generate_installer_package(self):
        pass


class LinuxAppInstaller(AppInstaller):
    def codesign(self):
        pass

    def generate_installer_package(self):
        pass
