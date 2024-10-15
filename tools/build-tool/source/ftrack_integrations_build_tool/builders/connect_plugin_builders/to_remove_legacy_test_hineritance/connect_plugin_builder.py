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
- Produce requirements.txt should also be a method
- Be able to zip it all
- Be able to deal with platform dependant plugins
- This one should inerit from builderBase where it only has a build method.
- Probably the wisget build and this one should be merged into one, as is just a matter of checking if the dependencies folder exists
- from the BuilderBase we should create another builder wich is style builder
'''
import os
import subprocess
import shutil
import toml


class ConnectPluginBuilder(BaseBuilder):
    @property
    def source_module(self):
        return self._source_module

    @property
    def python_environment_path(self):
        # TODO: if a folder is provided try to automatically find the python.exe file
        return self._python_environment_path

    @property
    def pyproject_toml_file(self):
        return self._pyproject_toml_file

    @property
    def plugin_name(self):
        return (
            self.pyproject_toml_file.get('tool', {})
            .get('poetry', {})
            .get('name', 'default_name')
        )

    @property
    def plugin_version(self):
        return (
            self.pyproject_toml_file.get('tool', {})
            .get('poetry', {})
            .get('version', '0.0.0')
        )

    @property
    def distribution_name(self):
        return f"{self.plugin_name}-{self.plugin_version}"

    @property
    def destination_path(self):
        return self._destination_path

    @property
    def connect_hook_folder(self):
        return self._connect_hook_folder

    @property
    def hook_destination(self):
        return self._hook_destination

    def __init__(
        self,
        source_module,
        python_environment_path=None,
        destination_path=None,
        connect_hook_folder=None,
    ):
        self._source_module = source_module
        self._python_environment_path = python_environment_path

        self._pyproject_toml_file = self._read_pyproject_toml_file()

        self._destination_path = (
            os.path.join(destination_path, 'dist', self.distribution_name)
            if destination_path
            else os.path.join(
                self.source_module, 'dist', self.distribution_name
            )
        )

        self._connect_hook_folder = connect_hook_folder or os.path.join(
            self.source_module, 'connect-plugin', 'hook'
        )

        # Destination paths structure
        self._hook_destination = os.path.join(self.destination_path, 'hook')

        self._build_folder = os.path.join(self.source_module, 'build')

    def build(self):
        self.copy_hook()
        self.generate_version_file()
        self.clean()

    def copy_hook(self):
        if not os.path.exists(self.connect_hook_folder):
            raise FileNotFoundError(
                f"Connect hook folder {self.connect_hook_folder} does not exist."
            )
        shutil.copytree(
            self.connect_hook_folder, self.hook_destination, dirs_exist_ok=True
        )

    def generate_version_file(self):
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

    def _get_python_version(self):
        command = [self.python_environment_path, '--version']
        result = subprocess.run(command, capture_output=True, text=True)
        version = result.stdout.split()[1]
        major_minor = '.'.join(version.split('.')[:2])
        return major_minor

    def _read_pyproject_toml_file(self):
        pyproject_path = os.path.join(self.source_module, 'pyproject.toml')
        if not os.path.exists(pyproject_path):
            raise FileNotFoundError(
                f"pyproject.toml file not found in {self.source_module}"
            )

        with open(pyproject_path, 'r') as file:
            pyproject = toml.load(file)

        return pyproject
