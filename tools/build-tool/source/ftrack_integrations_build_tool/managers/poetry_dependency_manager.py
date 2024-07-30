# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

import os
import subprocess


class PoetryDependencyManager:
    @property
    def source_module(self):
        return self._source_module

    @property
    def python_environment_path(self):
        # TODO: if a folder is provided try to automatically find the python.exe file
        return self._python_environment_path

    @property
    def build_folder(self):
        return self._build_folder

    @property
    def dependencies_path(self):
        return self._dependencies_path

    def __init__(
        self,
        source_module,
        python_environment_path,
        build_folder,
    ):
        self._source_module = source_module
        self._python_environment_path = python_environment_path
        self._build_folder = build_folder
        self._dependencies_path = None

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

    def _get_python_version(self):
        command = [self.python_environment_path, '--version']
        result = subprocess.run(command, capture_output=True, text=True)
        version = result.stdout.split()[1]
        major_minor = '.'.join(version.split('.')[:2])
        return major_minor
