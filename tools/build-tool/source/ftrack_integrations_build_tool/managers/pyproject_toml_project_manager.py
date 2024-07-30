# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

import os
import toml


class PyProjectTomlProjectManager:
    @property
    def source_module(self):
        return self._source_module

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
    def plugin_distribution_name(self):
        return f"{self.plugin_name}-{self.plugin_version}"

    def __init__(
        self,
        source_module,
    ):
        self._source_module = source_module

        self._pyproject_toml_file = self._read_pyproject_toml_file()

    def _read_pyproject_toml_file(self):
        pyproject_path = os.path.join(self.source_module, 'pyproject.toml')
        if not os.path.exists(pyproject_path):
            raise FileNotFoundError(
                f"pyproject.toml file not found in {self.source_module}"
            )

        with open(pyproject_path, 'r') as file:
            pyproject = toml.load(file)

        return pyproject
