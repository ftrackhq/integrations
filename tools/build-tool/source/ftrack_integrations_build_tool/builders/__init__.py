class BuilderBase:
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
        raise NotImplementedError("You should implement the build method")
