# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

# python tools/build.py --include_resources resource/bootstrap build_connect_plugin projects/framework-maya

# Build connect plugin command that accepts a connectpluginbuilder (in pypi)
# Photoshop example:
# We have the PSConnectPluginBuilder (in pypi?)
# In the terminal we should be able to execute something like buildConnectPlugin --builder PSConnectPluginBuilder

# We use poetry install --extras "ftrack-libs framework-libs" to install a new environment into the project root.
# If user wants, can provide a separated requirements.txt file
# There should also be a functionality to extract the dependencies from the poetry into the requirements.txt file. in fact, should extract 3 different requirement.txt, one with deps from pypi, one with deps from test pypi and one from source

# we should start just using the poetry one.
'''
# Tasks:
- Install dependnecies on a separated folder. without root
- Clean up and remove the environment stuff (files with virtualenv)
- Copy the dependencies to the destination folder
- Copy source folder to the destination folder
- Copy extensions folder to the destination folder
- Somohow should the user be able to choose the python interpreter? by default we asume that they already set that up.
'''
import os
import subprocess
import shutil

from ftrack_integrations_build_tool.builders.connect_plugin_builder import (
    ConnectPluginBuilder,
)


class FrameworkConnectPluginBuilder(ConnectPluginBuilder):
    @property
    def extensions_paths(self):
        return self._extensions_paths

    @property
    def connect_launch_folder(self):
        return self._connect_launch_folder

    @property
    def connect_resource_folder(self):
        return self._connect_resource_folder

    @property
    def dependencies_path(self):
        return self._dependencies_path

    @property
    def pre_build_dependencies_path(self):
        return self._pre_build_dependencies_path

    @property
    def dependencies_destination(self):
        return self._dependencies_destination

    @property
    def extensions_destination(self):
        return self._extensions_destination

    @property
    def launch_destination(self):
        return self._launch_destination

    @property
    def resource_destination(self):
        return self._resource_destination

    def __init__(
        self,
        source_module,
        python_environment_path=None,
        destination_path=None,
        connect_hook_folder=None,
        connect_launch_folder=None,
        connect_resource_folder=None,
        extensions_paths=None,
        pre_build_dependencies_path=None,
    ):
        super(FrameworkConnectPluginBuilder, self).__init__(
            source_module,
            python_environment_path,
            destination_path,
            connect_hook_folder,
        )

        # Check that extensions path is a dictionary with label as key and path as value. {'common': 'path/to/common', 'labkey': 'path/to/labkey'}
        if extensions_paths:
            if not isinstance(extensions_paths, dict):
                raise ValueError(
                    "Extensions paths should be a dictionary with label as key and path as value. For example: {'common': 'path/to/common', 'labkey': 'path/to/labkey'}"
                )
            self._extensions_paths = extensions_paths
        else:
            self._extensions_paths = self._get_default_extensions_paths()

        self._connect_launch_folder = connect_launch_folder or os.path.join(
            self.source_module, 'launch'
        )
        self._connect_resource_folder = (
            connect_resource_folder
            or os.path.join(self.source_module, 'resource')
        )

        self._pre_build_dependencies_path = pre_build_dependencies_path

        # Destination paths structure
        self._dependencies_destination = os.path.join(
            self.destination_path, 'dependencies'
        )
        self._extensions_destination = os.path.join(
            self.destination_path, 'extensions'
        )
        self._launch_destination = os.path.join(
            self.destination_path, 'launch'
        )
        self._resource_destination = os.path.join(
            self.destination_path, 'resource'
        )

    def build(self):
        if not self.pre_build_dependencies_path:
            self.install_dependencies()
        self.copy_dependencies()
        self.copy_extensions()
        self.copy_hook()
        self.copy_launch()
        self.copy_resource()
        self.generate_version_file()
        self.clean()

    def install_dependencies(self):
        # Be aware that we can't use poetry install as it will install the root dependency as editable.

        command = [
            'poetry',
            'bundle',
            'venv',
            self._build_folder,
            '--python',
            self.python_environment_path,
        ]
        subprocess.run(command, cwd=self.source_module, check=True)

        # Set the path to the site-packages directory
        site_packages_path = os.path.join(
            self._build_folder,
            'lib',
            f'python{self._get_python_version()}',
            'site-packages',
        )

        # Clean up _virtualenv.py file and _virtualenv.pth file
        for file in os.listdir(site_packages_path):
            if file.startswith('_virtualenv'):
                os.remove(os.path.join(site_packages_path, file))

        self._dependencies_path = site_packages_path

        return self.dependencies_path

    def copy_dependencies(self):
        if not os.path.exists(self.dependencies_path):
            raise FileNotFoundError(
                f"Dependencies path {self.dependencies_path} does not exist."
            )

        shutil.copytree(
            self.dependencies_path,
            self.dependencies_destination,
            dirs_exist_ok=True,
        )

    def copy_extensions(self):
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

    def copy_launch(self):
        if not os.path.exists(self.connect_launch_folder):
            raise FileNotFoundError(
                f"Connect launch folder {self.connect_launch_folder} does not exist."
            )
        shutil.copytree(
            self.connect_launch_folder,
            self.launch_destination,
            dirs_exist_ok=True,
        )

    def copy_resource(self):
        if not os.path.exists(self.connect_resource_folder):
            raise FileNotFoundError(
                f"Connect resource folder {self.connect_resource_folder} does not exist."
            )
        shutil.copytree(
            self.connect_resource_folder,
            self.resource_destination,
            dirs_exist_ok=True,
        )

    def _get_default_extensions_paths(self):
        # TODO: we will neeed to be able to pass the common extensions.
        # split the self.source_module string by - and get the last element as name for the key
        module_specific_extensions_name = self.source_module.split('-')[-1]
        _extensions_paths = {
            #'common': os.path.join(self.source_module, 'extensions'),
            module_specific_extensions_name: os.path.join(
                self.source_module, 'extensions'
            )
        }
        return _extensions_paths
