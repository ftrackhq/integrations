# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

import os


from ftrack_integrations_build_tool.managers import (
    PyProjectTomlProjectManager,
    ConnectPluginFileManager,
    PoetryDependencyManager,
)


class FrameworkMayaBuilder:  # (BuilderBase): probably here inherit from BuilderBase
    @property
    def source_module(self):
        return self._source_module

    @property
    def python_environment_path(self):
        return self._python_environment_path

    @property
    def pre_build_dependencies_path(self):
        return self._pre_build_dependencies_path

    @property
    def extensions_paths(self):
        return self._extensions_paths

    @property
    def file_manager_instance(self):
        return self._file_manager_instance

    @property
    def dependency_manager_instance(self):
        return self._dependency_manager_instance

    @property
    def project_manager_instance(self):
        return self._project_manager_instance

    def __init__(
        self,
        source_module,
        python_environment_path,
        pre_build_dependencies_path=None,
        extensions_paths=None,
        ProjectManager=PyProjectTomlProjectManager,
        FileManager=ConnectPluginFileManager,
        DependencyManager=PoetryDependencyManager,
    ):
        # TODO: probably better to inherit from builder base and that is an ABC class
        '''super(FrameworkMayaBuilder, self).__init__(
            source_module,
            python_environment_path,
            ProjectManager,
            FileManager,
            DependencyManager,
        )'''
        self._source_module = source_module
        self._python_environment_path = python_environment_path

        self._project_manager_instance = ProjectManager(source_module)
        self._file_manager_instance = FileManager(
            source_module,
            self.project_manager_instance.plugin_distribution_name,
            self.project_manager_instance.plugin_version,
        )
        self._dependency_manager_instance = DependencyManager(
            source_module,
            python_environment_path,
            self.file_manager_instance.build_folder,
        )

        # Builder specific variables:
        self._pre_build_dependencies_path = pre_build_dependencies_path
        self._extensions_paths = extensions_paths

    def build(self):
        self.file_manager_instance.dependencies_folder = (
            self.pre_build_dependencies_path
            or self._dependency_manager_instance.install_dependencies()
        )
        self.file_manager_instance.copy_dependencies_to_destination()
        self.file_manager_instance.copy_hook_to_destination()
        self.file_manager_instance.copy_launch_to_destination()
        self.file_manager_instance.copy_resource_to_destination()
        self.file_manager_instance.generate_version_file_to_destination()
        self.file_manager_instance.extensions_paths = (
            self.extensions_paths or self._get_default_extensions_paths()
        )

        self.file_manager_instance.copy_extensions_to_destination()
        self.file_manager_instance.clean()

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
