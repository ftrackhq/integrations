# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

import os
import shutil
from distutils.spawn import find_executable

ZXPSIGN_CMD = 'ZXPSignCmd'

# TODO: probably raise errors when paths doesn't exists.


class CEPManager:
    @property
    def source_module(self):
        return self._source_module

    @property
    def cep_folder(self):
        return self._cep_folder

    @property
    def style_images_folder(self):
        return str(self._style_images_folder)

    @style_images_folder.setter
    def style_images_folder(self, value):
        # Check that value is a string or None
        if value is not None and not isinstance(value, str):
            raise ValueError(
                "The style images folder must be a string representing a path."
            )
        self._style_images_folder = value

    @property
    def style_css_file(self):
        return str(self._style_css_file)

    @style_css_file.setter
    def style_css_file(self, value):
        # Check that value is a string or None
        if value is not None and not isinstance(value, str):
            raise ValueError(
                "The style images folder must be a string representing a path."
            )
        self._style_css_file = value

    @property
    def manifest_path(self):
        if not self._manifest_path:
            default_manifest_path = os.path.join(
                self.source_module,
                'resource',
                'adobe-cep',
                'bundle',
                'manifest.xml',
            )
            return str(default_manifest_path)
        return str(self._manifest_path)

    @manifest_path.setter
    def manifest_path(self, value):
        # Check that value is a string or None
        if value is not None and not isinstance(value, str):
            raise ValueError(
                "The manifest path must be a string representing a path."
            )
        self._manifest_path = value

    @property
    def adobe_certificate_password(self):
        if not self._adobe_certificate_password:
            default_adobe_certificate_password = os.environ.get(
                'ADOBE_CERTIFICATE_PASSWORD'
            )
            return str(default_adobe_certificate_password)
        return str(self._adobe_certificate_password)

    @adobe_certificate_password.setter
    def adobe_certificate_password(self, value):
        # Check that value is a string or None
        if value is not None and not isinstance(value, str):
            raise ValueError(
                "The adobe_certificate_password must be a string representing a password."
            )
        self._adobe_certificate_password = value

    @property
    def adobe_certificate_p12_path(self):
        if not self._adobe_certificate_p12_path:
            default_adobe_certificate_p12_path = os.path.join(
                self.cep_folder, 'bundle', 'certificate.p12'
            )
            return str(default_adobe_certificate_p12_path)
        return str(self._adobe_certificate_p12_path)

    @adobe_certificate_p12_path.setter
    def adobe_certificate_p12_path(self, value):
        # Check that value is a string or None
        if value is not None and not isinstance(value, str):
            raise ValueError(
                "The adobe certificate p12 path must be a string representing a path."
            )
        self._adobe_certificate_p12_path = value

    @property
    def cep_libraries_folder(self):
        if not self._cep_libraries_folder:
            default_cep_libraries_folder = os.path.join(
                self.cep_folder, 'libraries'
            )
            return str(default_cep_libraries_folder)
        return str(self._cep_libraries_folder)

    @cep_libraries_folder.setter
    def cep_libraries_folder(self, value):
        # Check that value is a string or None
        if value is not None and not isinstance(value, str):
            raise ValueError(
                "The adobe certificate p12 path must be a string representing a path."
            )
        self._cep_libraries_folder = value

    @property
    def framework_js_libraries_folder(self):
        if not self._framework_js_libraries_folder:
            default_framework_js_libraries_folder = os.path.join(
                self.cep_folder, 'framework-js', 'source'
            )
            return str(default_framework_js_libraries_folder)
        return str(self._framework_js_libraries_folder)

    @framework_js_libraries_folder.setter
    def framework_js_libraries_folder(self, value):
        # Check that value is a string or None
        if value is not None and not isinstance(value, str):
            raise ValueError(
                "The adobe certificate p12 path must be a string representing a path."
            )
        self._framework_js_libraries_folder = value

    def __init__(
        self,
        source_module,
        cep_folder,
        style_images_folder,
        style_css_file,
        manifest_path=None,
        adobe_certificate_password=None,
        adobe_certificate_p12_path=None,
        cep_libraries_folder=None,
        framework_js_libraries_folder=None,
        build_folder=None,
        plugin_version=None,
        # plugin_distribution_name,
        # plugin_version,
        # destination_path=None,
        # connect_hook_folder=None,
        # connect_launch_folder=None,
        # resource_folder=None,
        # dependencies_folder=None,
        # extensions_paths=None,
    ):
        self._source_module = source_module
        self._cep_folder = cep_folder
        self.style_images_folder = style_images_folder
        self.style_css_file = style_css_file

        self.manifest_path = manifest_path
        self.adobe_certificate_password = adobe_certificate_password
        self.adobe_certificate_p12_path = adobe_certificate_p12_path
        self.cep_libraries_folder = cep_libraries_folder
        self.framework_js_libraries_folder = framework_js_libraries_folder

        self.build_folder = build_folder
        self.staging_folder = os.path.join(build_folder, 'staging')

        # destination_folder

        ZXPSIGN_CMD_PATH = find_executable(ZXPSIGN_CMD)
        if not ZXPSIGN_CMD_PATH:
            raise Exception('%s is not in your ${PATH}!' % (ZXPSIGN_CMD))

        # self._plugin_distribution_name = plugin_distribution_name
        # self._plugin_version = plugin_version
        #
        # self.destination_path = destination_path
        #
        # self.connect_hook_folder = connect_hook_folder
        # self.connect_launch_folder = connect_launch_folder
        # self.resource_folder = resource_folder
        # self.dependencies_folder = dependencies_folder
        # self.extensions_paths = extensions_paths
        #
        # # Init paths
        # self._hook_destination = None
        # self._dependencies_destination = None
        # self._extensions_destination = None
        # self._launch_destination = None
        # self._resource_destination = None
        # self._build_folder = None

    def create_staging_folder(self):
        shutil.rmtree(self.staging_folder, ignore_errors=True)
        os.makedirs(self.staging_folder)
        os.makedirs(os.path.join(self.staging_folder, 'image'))
        os.makedirs(os.path.join(self.staging_folder, 'css'))

    def copy_index_html_to_staging_folder(self):
        try:
            self._copy_and_replace_version(
                os.path.join(self.cep_folder, 'index.html'),
                os.path.join(self.staging_folder, 'index.html'),
            )
        except FileNotFoundError as e:
            raise FileNotFoundError(
                f"Index.html not found in CEP folder {self.cep_folder}."
            )

    def copy_bootstrap_js_to_staging_folder(self):
        try:
            self._copy_and_replace_version(
                os.path.join(self.cep_folder, 'bootstrap.js'),
                os.path.join(self.staging_folder, 'bootstrap.js'),
            )
        except FileNotFoundError as e:
            raise FileNotFoundError(
                f"Bootstrap.js not found in CEP folder {self.cep_folder}."
            )

    def copy_style_images_to_staging_folder(self):
        try:
            shutil.copytree(
                self.style_images_folder,
                os.path.join(self.staging_folder, 'image'),
            )
        except FileNotFoundError as e:
            raise FileNotFoundError(
                f"Style images folder {self.style_images_folder} does not exist."
            )

    def copy_style_file_to_staging_folder(self):
        try:
            shutil.copy(
                self.style_css_file,
                os.path.join(self.staging_folder, 'css', 'style.css'),
            )
        except FileNotFoundError as e:
            raise FileNotFoundError(
                f"Style css file {self.style_css_file} does not exist."
            )

    def copy_cep_libraries_to_staging_folder(self):
        try:
            shutil.copytree(
                self.cep_libraries_folder,
                os.path.join(self.staging_folder, 'lib'),
            )
        except FileNotFoundError as e:
            raise FileNotFoundError(
                f"CEP libraries folder {self.cep_libraries_folder} does not exist."
            )

    def copy_framework_js_libraries_to_staging_folder(self):
        try:
            # TODO: make sure we don't replace the lib folder if it already exists
            shutil.copytree(
                self.framework_js_libraries_folder,
                os.path.join(self.staging_folder, 'lib'),
            )
        except FileNotFoundError as e:
            raise FileNotFoundError(
                f"Framework JS libraries folder {self.framework_js_libraries_folder} does not exist."
            )

    def _copy_and_replace_version(self, source_path, target_path):
        '''Copies the single file pointed out by *source_path* to *target_path* and
        replaces version expression to supplied *version*.'''
        if not os.path.exists(source_path):
            raise FileNotFoundError(
                f"Source file {source_path} does not exist."
            )
        with open(source_path, 'r') as f_src:
            with open(target_path, 'w') as f_dst:
                f_dst.write(
                    f_src.read().replace('${VERSION}', self.plugin_version)
                )

    # def copy_hook_to_destination(self):
    #     # Check that connect_hook_folder has been set
    #     if not self.connect_hook_folder:
    #         raise ValueError("Connect hook folder has not been set.")
    #     try:
    #         self._copy_folder_to_destination(
    #             self.connect_hook_folder, self.hook_destination
    #         )
    #     except FileNotFoundError as e:
    #         raise FileNotFoundError(
    #             f"Connect hook folder {self.connect_hook_folder} does not exist."
    #         )
    #
    # def copy_dependencies_to_destination(self):
    #     if not self.dependencies_folder:
    #         raise ValueError("Dependencies folder has not been set.")
    #     try:
    #         self._copy_folder_to_destination(
    #             self.dependencies_folder, self.dependencies_destination
    #         )
    #     except FileNotFoundError as e:
    #         raise FileNotFoundError(
    #             f"Dependencies path {self.dependencies_folder} does not exist."
    #         )
    #
    # def copy_launch_to_destination(self):
    #     if not self.connect_launch_folder:
    #         raise ValueError("Launch folder has not been set.")
    #     try:
    #         self._copy_folder_to_destination(
    #             self.connect_launch_folder, self.launch_destination
    #         )
    #     except FileNotFoundError as e:
    #         raise FileNotFoundError(
    #             f"Launch folder {self.connect_launch_folder} does not exist."
    #         )
    #
    # def copy_resource_to_destination(self):
    #     if not self.resource_folder:
    #         raise ValueError("Resource folder has not been set.")
    #     try:
    #         self._copy_folder_to_destination(
    #             self.resource_folder, self.resource_destination
    #         )
    #     except FileNotFoundError as e:
    #         raise FileNotFoundError(
    #             f"Resource folder {self.resource_folder} does not exist."
    #         )
    #
    # def copy_extensions_to_destination(self):
    #     if not self.extensions_paths:
    #         raise ValueError("Extensions paths have not been set.")
    #     for label, path in self.extensions_paths.items():
    #         if not os.path.exists(path):
    #             raise FileNotFoundError(
    #                 f"Extensions path {path} does not exist."
    #             )
    #         self._copy_folder_to_destination(
    #             path, os.path.join(self.extensions_destination, label)
    #         )
    #
    # def generate_version_file_to_destination(self):
    #     # Store the version so Connect easily can identify the plugin version
    #     version_path = os.path.join(self.destination_path, '__version__.py')
    #     with open(version_path, 'w') as file:
    #         file.write(VERSION_TEMPLATE.format(version=self.plugin_version))
    #
    # def clean(self):
    #     # Remove the build folder if exists
    #     if os.path.exists(self.build_folder):
    #         shutil.rmtree(self.build_folder)
    #
    # def _copy_folder_to_destination(self, source_folder, destination_folder):
    #     if not os.path.exists(source_folder):
    #         raise FileNotFoundError(f"Folder {source_folder} does not exist.")
    #     if os.path.exists(destination_folder):
    #         shutil.rmtree(destination_folder)
    #     shutil.copytree(source_folder, destination_folder)
