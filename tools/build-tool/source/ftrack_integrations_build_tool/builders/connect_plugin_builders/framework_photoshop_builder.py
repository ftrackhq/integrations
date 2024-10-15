# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

import os


from ftrack_integrations_build_tool.managers import (
    PyProjectTomlProjectManager,
    ConnectPluginFileManager,
    PoetryDependencyManager,
    CEPManager,
)


class FrameworkPhotoshopBuilder:  # (BuilderBase): probably here inherit from BuilderBase
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
        cep_folder,
        style_images_folder,
        style_css_file,
        pre_build_dependencies_path=None,
        extensions_paths=None,
        adobe_certificate_password=None,
        ProjectManager=PyProjectTomlProjectManager,
        FileManager=ConnectPluginFileManager,
        DependencyManager=PoetryDependencyManager,
        CEPManager=CEPManager,
    ):
        '''
        :param source_module: The path to the source module.
        :param python_environment_path: The path to the python environment.
        :param pre_build_dependencies_path: The path to the pre-build dependencies.
        :param extensions_paths: The paths to the extensions.
        :param ProjectManager: The project manager class. Default is PyProjectTomlProjectManager.
        :param FileManager: The file manager class. Default is ConnectPluginFileManager.
        :param DependencyManager: The dependency manager class. Default is PoetryDependencyManager.
        '''
        # TODO: probably better to inherit from builder base and that is an ABC class

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

        self._cep_manager_instance = CEPManager(
            source_module,
            os.path.split(self.file_manager_instance.destination_path)[0],
            self.file_manager_instance.build_folder,
            self.project_manager_instance.plugin_distribution_name,
            self.project_manager_instance.plugin_version,
            cep_folder,
            style_images_folder,
            style_css_file,
            adobe_certificate_password=adobe_certificate_password,
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
        self.file_manager_instance.generate_version_file_to_destination()
        self.file_manager_instance.extensions_paths = (
            self.extensions_paths or self._get_default_extensions_paths()
        )

        self.file_manager_instance.copy_extensions_to_destination()

        self._cep_manager_instance.create_staging_folder()
        self._cep_manager_instance.copy_style_images_to_staging_folder()
        self._cep_manager_instance.copy_style_file_to_staging_folder()
        self._cep_manager_instance.copy_source_cep_content_files_to_staging_folder()
        self._cep_manager_instance.copy_index_html_to_staging_folder()
        self._cep_manager_instance.copy_bootstrap_js_to_staging_folder()
        self._cep_manager_instance.copy_cep_libraries_to_staging_folder()
        self._cep_manager_instance.copy_manifest_file_to_staging_folder()
        self._cep_manager_instance.generate_and_sign_zxp()

        # self.file_manager_instance.clean()

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
