# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

import os
import shutil
import subprocess
from distutils.spawn import find_executable

ZXPSIGN_CMD = 'ZXPSignCmd'

# TODO: probably raise errors when paths doesn't exists.


class CEPManager:
    @property
    def source_module(self):
        return self._source_module

    @property
    def destination_path(self):
        return self._destination_path

    @property
    def cep_folder(self):
        return self._cep_folder

    @property
    def build_folder(self):
        return self._build_folder

    @property
    def plugin_version(self):
        return self._plugin_version

    @property
    def plugin_distribution_name(self):
        return self._plugin_distribution_name

    @property
    def zxp_file_path(self):
        return os.path.join(
            self.destination_path, f'{self.plugin_distribution_name}.zxp'
        )

    @property
    def staging_folder(self):
        return os.path.join(self.build_folder, 'staging')

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
    def source_cep_folder(self):
        return os.path.join(self.source_module, 'resource', 'adobe-cep')

    @property
    def manifest_path(self):
        if not self._manifest_path:
            default_manifest_path = os.path.join(
                self.source_module,
                'resource',
                'adobe-cep',
                'CSXS',
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
                self.cep_folder, 'certificate', 'certificate.p12'
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
            default_cep_libraries_folder = os.path.join(self.cep_folder, 'lib')
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

    def __init__(
        self,
        source_module,
        destination_path,
        build_folder,
        plugin_distribution_name,
        plugin_version,
        cep_folder,
        style_images_folder,
        style_css_file,
        manifest_path=None,
        adobe_certificate_password=None,
        adobe_certificate_p12_path=None,
        cep_libraries_folder=None,
    ):
        self._source_module = source_module
        self._destination_path = destination_path
        self._build_folder = build_folder
        self._plugin_version = plugin_version
        self._plugin_distribution_name = plugin_distribution_name
        self._cep_folder = cep_folder
        self.style_images_folder = style_images_folder
        self.style_css_file = style_css_file

        self.manifest_path = manifest_path
        self.adobe_certificate_password = adobe_certificate_password
        self.adobe_certificate_p12_path = adobe_certificate_p12_path
        self.cep_libraries_folder = cep_libraries_folder

        ZXPSIGN_CMD_PATH = find_executable(ZXPSIGN_CMD)
        if not ZXPSIGN_CMD_PATH:
            raise Exception('%s is not in your ${PATH}!' % (ZXPSIGN_CMD))

    def create_staging_folder(self):
        shutil.rmtree(self.staging_folder, ignore_errors=True)
        os.makedirs(self.staging_folder)

        # Remove this
        # os.makedirs(os.path.join(self.staging_folder, 'CSXS'))

    def copy_style_images_to_staging_folder(self):
        # if os.path.exists(os.path.join(self.staging_folder, 'image')):
        #     shutil.rmtree(os.path.join(self.staging_folder, 'image'))
        # os.makedirs(os.path.join(self.staging_folder, 'image'))
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
        if os.path.exists(os.path.join(self.staging_folder, 'css')):
            shutil.rmtree(os.path.join(self.staging_folder, 'css'))
        os.makedirs(os.path.join(self.staging_folder, 'css'))
        try:
            shutil.copy(
                self.style_css_file,
                os.path.join(self.staging_folder, 'css'),
            )
        except FileNotFoundError as e:
            raise FileNotFoundError(
                f"Style css file {self.style_css_file} does not exist."
            )

    def copy_source_cep_content_files_to_staging_folder(self):
        for item in os.listdir(self.source_cep_folder):
            s = os.path.join(self.source_cep_folder, item)
            d = os.path.join(self.staging_folder, item)

            if os.path.isfile(s):
                shutil.copy2(s, d)

    def copy_index_html_to_staging_folder(self):
        try:
            shutil.copy(
                os.path.join(self.cep_folder, 'index.html'),
                os.path.join(self.staging_folder, 'index.html'),
            )
        except FileNotFoundError as e:
            raise FileNotFoundError(
                f"Index.html not found in CEP folder {self.cep_folder}."
            )

    def copy_bootstrap_js_to_staging_folder(self):
        try:
            shutil.copy(
                os.path.join(self.cep_folder, 'bootstrap.js'),
                os.path.join(self.staging_folder, 'bootstrap.js'),
            )
        except FileNotFoundError as e:
            raise FileNotFoundError(
                f"Bootstrap.js not found in CEP folder {self.cep_folder}."
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

    def copy_manifest_file_to_staging_folder(self):
        if os.path.exists(os.path.join(self.staging_folder, 'CSXS')):
            shutil.rmtree(os.path.join(self.staging_folder, 'CSXS'))
        os.makedirs(os.path.join(self.staging_folder, 'CSXS'))
        try:
            self._copy_and_replace_version(
                self.manifest_path,
                os.path.join(self.staging_folder, 'CSXS', 'manifest.xml'),
            )
        except FileNotFoundError as e:
            raise FileNotFoundError(
                f"Manifest file {self.manifest_path} does not exist."
            )

    def generate_and_sign_zxp(self):
        # Generate the ZXP file and log the result
        print(f"self.staging_folder: {self.staging_folder}")
        print(f"self.zxp_file_path: {self.zxp_file_path}")
        print(
            f"self.adobe_certificate_p12_path: {self.adobe_certificate_p12_path}"
        )
        print(
            f"self.adobe_certificate_password: {self.adobe_certificate_password}"
        )
        command = [
            ZXPSIGN_CMD,
            '-sign',
            self.staging_folder,
            self.zxp_file_path,
            self.adobe_certificate_p12_path,
            self.adobe_certificate_password,
        ]
        result = subprocess.run(command, capture_output=True, text=True)
        # Check if result is an error raise exception
        if result.returncode != 0:
            raise Exception(f"Error generating ZXP file: {result.stderr}")

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
