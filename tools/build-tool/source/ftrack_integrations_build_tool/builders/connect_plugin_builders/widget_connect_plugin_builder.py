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


class WidgetConnectPluginBuilder(ConnectPluginBuilder):
    @property
    def dependencies_path(self):
        return self._dependencies_path

    @property
    def pre_build_dependencies_path(self):
        return self._pre_build_dependencies_path

    @property
    def dependencies_destination(self):
        return self._dependencies_destination

    def __init__(
        self,
        source_module,
        python_environment_path=None,
        destination_path=None,
        connect_hook_folder=None,
        pre_build_dependencies_path=None,
    ):
        super(WidgetConnectPluginBuilder, self).__init__(
            source_module,
            python_environment_path,
            destination_path,
            connect_hook_folder,
        )

        self._pre_build_dependencies_path = pre_build_dependencies_path

        # Destination paths structure
        self._dependencies_destination = os.path.join(
            self.destination_path, 'dependencies'
        )

    def build(self):
        if not self.pre_build_dependencies_path:
            self.install_dependencies()
        self.copy_dependencies()
        self.copy_hook()
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
