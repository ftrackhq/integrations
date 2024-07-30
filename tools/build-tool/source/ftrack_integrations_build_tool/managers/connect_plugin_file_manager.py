# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

import os
import shutil


class ConnectPluginFileManager:
    @property
    def source_module(self):
        return self._source_module

    @property
    def plugin_distribution_name(self):
        return self._plugin_distribution_name

    @property
    def plugin_version(self):
        return self._plugin_version

    @property
    def destination_path(self):
        if not self._destination_path:
            default_destination_path = os.path.join(
                self.source_module, 'dist', self.plugin_distribution_name
            )
            return str(default_destination_path)
        return str(self._destination_path)

    @destination_path.setter
    def destination_path(self, value):
        if not isinstance(value, str):
            raise ValueError(
                "The destination path must be a string representing a path."
            )
        self._destination_path = value

    @property
    def connect_hook_folder(self):
        if not self._connect_hook_folder:
            default_folder = os.path.join(
                self.source_module, 'connect-plugin', 'hook'
            )
            return default_folder
        return self._connect_hook_folder

    @connect_hook_folder.setter
    def connect_hook_folder(self, value):
        if not isinstance(value, str):
            raise ValueError(
                "The connect hook folder must be a string representing a path."
            )
        self._connect_hook_folder = value

    @property
    def connect_launch_folder(self):
        if not self._connect_launch_folder:
            default_folder = os.path.join(self.source_module, 'launch')
            return default_folder
        return self._connect_launch_folder

    @connect_launch_folder.setter
    def connect_launch_folder(self, value):
        if not isinstance(value, str):
            raise ValueError(
                "The connect launch folder must be a string representing a path."
            )
        self._connect_launch_folder = value

    @property
    def resource_folder(self):
        if not self._resource_folder:
            default_folder = os.path.join(self.source_module, 'resource')
            return default_folder
        return self._resource_folder

    @resource_folder.setter
    def resource_folder(self, value):
        if not isinstance(value, str):
            raise ValueError(
                "The resource folder must be a string representing a path."
            )
        self._resource_folder = value

    @property
    def dependencies_folder(self):
        return self._dependencies_folder

    @dependencies_folder.setter
    def dependencies_folder(self, value):
        if not isinstance(value, str):
            raise ValueError(
                "The dependencies folder must be a string representing a path."
            )
        self._dependencies_folder = value

    @property
    def extensions_paths(self):
        return self._extensions_paths

    @extensions_paths.setter
    def extensions_paths(self, value):
        if value:
            if not isinstance(value, dict):
                raise ValueError(
                    "Extensions paths should be a dictionary with label as key and path as value. For example: {'common': 'path/to/common', 'labkey': 'path/to/labkey'}"
                )
        self._extensions_paths = value

    @property
    def hook_destination(self):
        if not self._hook_destination:
            return os.path.join(self.destination_path, 'hook')
        return self._hook_destination

    @hook_destination.setter
    def hook_destination(self, value):
        if not isinstance(value, str):
            raise ValueError(
                "The hook destination must be a string representing a path."
            )
        self._hook_destination = value

    @property
    def dependencies_destination(self):
        if not self._dependencies_destination:
            return os.path.join(self.destination_path, 'dependencies')
        return self._dependencies_destination

    @dependencies_destination.setter
    def dependencies_destination(self, value):
        if not isinstance(value, str):
            raise ValueError(
                "The dependencies destination must be a string representing a path."
            )
        self._dependencies_destination = value

    @property
    def extensions_destination(self):
        if not self._extensions_destination:
            return str(os.path.join(self.destination_path, 'extensions'))
        return str(self._extensions_destination)

    @extensions_destination.setter
    def extensions_destination(self, value):
        if not isinstance(value, str):
            raise ValueError(
                "The extensions destination must be a string representing a path."
            )
        self._extensions_destination = value

    @property
    def launch_destination(self):
        if not self._launch_destination:
            return os.path.join(self.destination_path, 'launch')
        return self._launch_destination

    @launch_destination.setter
    def launch_destination(self, value):
        if not isinstance(value, str):
            raise ValueError(
                "The launch destination must be a string representing a path."
            )
        self._launch_destination = value

    @property
    def resource_destination(self):
        if not self._resource_destination:
            return os.path.join(self.destination_path, 'resource')
        return self._resource_destination

    @resource_destination.setter
    def resource_destination(self, value):
        if not isinstance(value, str):
            raise ValueError(
                "The resource destination must be a string representing a path."
            )
        self._resource_destination = value

    @property
    def build_folder(self):
        if not self._build_folder:
            return os.path.join(self.source_module, 'build')
        return self._build_folder

    @build_folder.setter
    def build_folder(self, value):
        if not isinstance(value, str):
            raise ValueError(
                "The build folder must be a string representing a path."
            )
        self._build_folder = value

    def __init__(
        self,
        source_module,
        plugin_distribution_name,
        plugin_version,
        destination_path=None,
        connect_hook_folder=None,
        connect_launch_folder=None,
        resource_folder=None,
        dependencies_folder=None,
        extensions_paths=None,
    ):
        self._source_module = source_module
        self._plugin_distribution_name = plugin_distribution_name
        self._plugin_version = plugin_version

        self.destination_path = destination_path

        self.connect_hook_folder = connect_hook_folder
        self.connect_launch_folder = connect_launch_folder
        self.resource_folder = resource_folder
        self.dependencies_folder = dependencies_folder
        self.extensions_paths = extensions_paths

        # Init paths
        self._hook_destination = None
        self._dependencies_destination = None
        self._extensions_destination = None
        self._launch_destination = None
        self._resource_destination = None
        self._build_folder = None

    def copy_hook_to_destination(self):
        # Check that connect_hook_folder has been set
        if not self.connect_hook_folder:
            raise ValueError("Connect hook folder has not been set.")
        try:
            self._copy_folder_to_destination(
                self.connect_hook_folder, self.hook_destination
            )
        except FileNotFoundError as e:
            raise FileNotFoundError(
                f"Connect hook folder {self.connect_hook_folder} does not exist."
            )

    def copy_dependencies_to_destination(self):
        if not self.dependencies_folder:
            raise ValueError("Dependencies folder has not been set.")
        try:
            self._copy_folder_to_destination(
                self.dependencies_folder, self.dependencies_destination
            )
        except FileNotFoundError as e:
            raise FileNotFoundError(
                f"Dependencies path {self.dependencies_folder} does not exist."
            )

    def copy_launch_to_destination(self):
        if not self.connect_launch_folder:
            raise ValueError("Launch folder has not been set.")
        try:
            self._copy_folder_to_destination(
                self.connect_launch_folder, self.launch_destination
            )
        except FileNotFoundError as e:
            raise FileNotFoundError(
                f"Launch folder {self.connect_launch_folder} does not exist."
            )

    def copy_resource_to_destination(self):
        if not self.resource_folder:
            raise ValueError("Resource folder has not been set.")
        try:
            self._copy_folder_to_destination(
                self.resource_folder, self.resource_destination
            )
        except FileNotFoundError as e:
            raise FileNotFoundError(
                f"Resource folder {self.resource_folder} does not exist."
            )

    def copy_extensions_to_destination(self):
        if not self.extensions_paths:
            raise ValueError("Extensions paths have not been set.")
        for label, path in self.extensions_paths.items():
            if not os.path.exists(path):
                raise FileNotFoundError(
                    f"Extensions path {path} does not exist."
                )
            shutil.copytree(
                path,
                os.path.join(self.extensions_destination, label),
                dirs_exist_ok=True,
            )

    def generate_version_file_to_destination(self):
        VERSION_TEMPLATE = '''
        # :coding: utf-8
        # :copyright: Copyright (c) 2024 ftrack

        __version__ = '{version}'
        '''
        # Store the version so Connect easily can identify the plugin version
        version_path = os.path.join(self.destination_path, '__version__.py')
        with open(version_path, 'w') as file:
            file.write(VERSION_TEMPLATE.format(version=self.plugin_version))

    def clean(self):
        # Remove the build folder if exists
        if os.path.exists(self._build_folder):
            shutil.rmtree(self._build_folder)

    def _copy_folder_to_destination(self, source_folder, destination_folder):
        if not os.path.exists(source_folder):
            raise FileNotFoundError(f"Folder {source_folder} does not exist.")
        shutil.copytree(source_folder, destination_folder, dirs_exist_ok=True)
