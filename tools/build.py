# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

'''
ftrack Integrations build and deployment tooling.

Temporary replaces original setuptools implementation until there is an
official CI/CD build implementation in place.


Changelog:

0.4.15 [24.03.13] Fix platform dependent bug.
0.4.14 [24.02.23] Incorporate RV pkg build.
0.4.13 [24.02.12] Build qt-style when building CEP plugin.
0.4.12 [24.02.05] Build qt-style if from_source flag to build script
0.4.11 [23.12.18] Added missing ftrack-framework-qt dependency to Photoshop
0.4.10 [23.12.12] Platform dependent support in plugin manager.
0.4.9 [23.11.23] Include DCC config in build.
0.4.8 [23.11.01] Pick up Connect plugin version and hook from connect-plugin folder.
0.4.7 [23.10.30] Read package version from pyproject.toml, parse and replace version in Connect hooks.
0.4.6 [23.10.30] Allow pre releases on Connect build when enabling test PyPi.
0.4.5 [23.10.26] Support for including assets in Connect plugin build.
0.4.4 [23.10.13] Support for building multiple packages at once.
0.4.3 [23.10.11] Support for additional CEP JS include folder
0.4.2 [23.10.09] Support for additional hook include folder
0.4.1 [23.10.02] Redone Photoshop CEP build
0.4.0 [23.09.21] Build within Monorepo, refactored framework
0.3.1 [23.08.29] CEP build updates
0.3.0 [23.07.06] Support for building CEP extension
0.2.0 [23.04.17] Supply resource folder on plugin build
0.1.0 [23.03.08] Initial version

'''

import argparse
import os
import shutil
import logging
import sys
import subprocess
from distutils.spawn import find_executable
import fileinput
import tempfile

__version__ = '0.4.15'

ZXPSIGN_CMD = 'ZXPSignCmd'

logging.getLogger().setLevel(logging.INFO)

VERSION_TEMPLATE = '''
# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

__version__ = '{version}'
'''


def build_package(pkg_path, args, command=None):
    '''Build the package @ pkg_path'''
    os.chdir(pkg_path)

    if command is None:
        command = args.command
    ROOT_PATH = os.path.realpath(os.getcwd())
    MONOREPO_PATH = os.path.realpath(os.path.join(ROOT_PATH, '..', '..'))
    CONNECT_PLUGIN_PATH = os.path.join(ROOT_PATH, 'connect-plugin')
    BUILD_PATH = os.path.join(ROOT_PATH, 'dist')
    EXTENSION_PATH = os.path.join(ROOT_PATH, 'extensions')
    CEP_PATH = os.path.join(ROOT_PATH, 'resource', 'cep')
    USES_FRAMEWORK = False
    FTRACK_DEP_LIBS = []
    PLATFORM_DEPENDENT = False

    POETRY_CONFIG_PATH = os.path.join(ROOT_PATH, 'pyproject.toml')
    DCC_NAME = None
    VERSION = None

    def append_dependencies(toml_path):
        nonlocal USES_FRAMEWORK, PLATFORM_DEPENDENT, FTRACK_DEP_LIBS
        section = None
        with open(toml_path) as f:
            for line in f:
                if line.startswith("["):
                    section = line.strip().strip('[]')
                elif section == 'tool.poetry.dependencies':
                    if line.startswith('ftrack-'):
                        lib = line.split('=')[0][7:].strip()
                        lib_toml_path = os.path.join(
                            MONOREPO_PATH, 'libs', lib, 'pyproject.toml'
                        )
                        if lib not in FTRACK_DEP_LIBS and os.path.exists(
                            lib_toml_path
                        ):
                            logging.info(
                                f'Identified monorepo dependency: {lib}'
                            )
                            FTRACK_DEP_LIBS.append(lib)
                            # Recursively add monorepo dependencies
                            append_dependencies(lib_toml_path)
                        if line.startswith('ftrack-framework-core'):
                            USES_FRAMEWORK = True

    if os.path.exists(POETRY_CONFIG_PATH):
        PROJECT_NAME = None
        section = None
        with open(POETRY_CONFIG_PATH) as f:
            for line in f:
                if line.startswith("["):
                    section = line.strip().strip('[]')
                if section == 'tool.poetry':
                    if line.startswith('name = '):
                        PROJECT_NAME = line.split('=')[1].strip().strip('"')
                    elif line.startswith('version = '):
                        VERSION = line.split('=')[1].strip().strip('"')
                elif section == 'tool.poetry.dependencies':
                    if line.find('pyside') > -1:
                        PLATFORM_DEPENDENT = True
                        logging.info(
                            'Platform dependent build - OS suffix will be added to artifact.'
                        )

        append_dependencies(POETRY_CONFIG_PATH)

        if USES_FRAMEWORK:
            DCC_NAME = PROJECT_NAME.split('-')[-1]
        assert VERSION, 'No version could be extracted from "pyproject.toml"!'

        if command == 'build_cep':
            # Align version, cannot contain rc/alpha/beta
            if VERSION.find('rc') > -1:
                VERSION = VERSION.split('rc')[0]
            elif VERSION.find('a') > -1:
                VERSION = VERSION.split('a')[0]
            elif VERSION.find('b') > -1:
                VERSION = VERSION.split('b')[0]

    else:
        logging.warning(
            'Missing "pyproject.toml" file, not able to identify target DCC!'
        )

        PROJECT_NAME = f'ftrack-{os.path.basename(ROOT_PATH)}'
        VERSION = '0.0.0'

    SOURCE_PATH = os.path.join(
        ROOT_PATH, 'source', PROJECT_NAME.replace('-', '_')
    )

    DEFAULT_STYLE_PATH = os.path.join(MONOREPO_PATH, 'resource', 'style')

    def clean(args):
        '''Remove build folder'''

        if not os.path.exists(BUILD_PATH):
            logging.warning(f'No build found: "{BUILD_PATH}"!')

        logging.info('Cleaning up {}'.format(BUILD_PATH))
        shutil.rmtree(BUILD_PATH, ignore_errors=True)

    def parse_and_copy(source_path, target_path):
        '''Copies the single file pointed out by *source_path* to *target_path* and
        replaces version expression to supplied *version*.'''
        logging.info(
            'Parsing and copying {}>{}'.format(source_path, target_path)
        )
        with open(source_path, 'r') as f_src:
            with open(target_path, 'w') as f_dst:
                f_dst.write(
                    f_src.read().replace(
                        '{{FTRACK_FRAMEWORK_PHOTOSHOP_VERSION}}', VERSION
                    )
                )

    def build_connect_plugin(args):
        '''
        Build the Connect plugin archive ready to be deployed in the Plugin manager.

        Collects all the library and hook dependencies for an integration or component.
        '''

        if not os.path.exists(BUILD_PATH):
            os.makedirs(BUILD_PATH)

        logging.info('*' * 100)
        logging.info(
            'Remember to build the plugin with Poetry (poetry build) before '
            'building the Connect plugin!'
        )
        logging.info('*' * 100)

        # Find lock file
        lock_path = None
        for filename in os.listdir(ROOT_PATH):
            if not filename == 'poetry.lock':
                continue
            lock_path = os.path.join(BUILD_PATH, filename)
            break

        if not lock_path:
            raise Exception(
                'Could not locate Poetry lock file! Please run "poetry update".'
            )

        # For now, Connect plugin has the same version as the project
        CONNECT_PLUGIN_VERSION = VERSION

        logging.info(
            'Connect plugin version ({})'.format(CONNECT_PLUGIN_VERSION)
        )

        STAGING_PATH = os.path.join(
            BUILD_PATH,
            '{}-{}'.format(PROJECT_NAME, CONNECT_PLUGIN_VERSION),
        )

        # Clean staging path
        if os.path.exists(STAGING_PATH):
            logging.info('Cleaning up {}'.format(STAGING_PATH))
            shutil.rmtree(STAGING_PATH, ignore_errors=True)
        os.makedirs(os.path.join(STAGING_PATH))

        # Find wheel and read the version
        wheel_path = None
        for filename in os.listdir(BUILD_PATH):
            # Expect: ftrack_connect_pipeline_qt-1.3.0a1-py3-none-any.whl
            if not filename.endswith('.whl') or VERSION not in filename.split(
                '-'
            ):
                continue
            wheel_path = os.path.join(BUILD_PATH, filename)
            break

        if not wheel_path:
            raise Exception(
                'Could not locate a built python wheel! Please build with Poetry.'
            )

        # Store the version so Connect easily can identify the plugin version
        version_path = os.path.join(STAGING_PATH, '__version__.py')
        with open(version_path, 'w') as file:
            file.write(VERSION_TEMPLATE.format(version=CONNECT_PLUGIN_VERSION))

        # Locate and copy hook
        logging.info('Copying Connect hook')
        path_hook = os.path.join(CONNECT_PLUGIN_PATH, 'hook')
        if not os.path.isdir(path_hook):
            raise Exception(
                'Missing "hook" folder in "connect-plugin" folder!'
            )

        shutil.copytree(path_hook, os.path.join(STAGING_PATH, 'hook'))

        # Locate and copy launcher

        launcher_path = os.path.join(EXTENSION_PATH, 'launch')
        if os.path.isdir(launcher_path):
            logging.info('Copying App launcher config')
            shutil.copytree(
                launcher_path, os.path.join(STAGING_PATH, 'launch')
            )
        else:
            logging.warning(
                'App launcher config path not found: {}'.format(launcher_path)
            )

        # Resources

        if args.include_resources:
            for resource_path in args.include_resources.split(','):
                # Copy resources
                if os.path.exists(resource_path):
                    logging.info('Copying resource "{}"'.format(resource_path))
                    if not os.path.exists(
                        os.path.join(STAGING_PATH, 'resource')
                    ):
                        os.makedirs(os.path.join(STAGING_PATH, 'resource'))
                    shutil.copytree(
                        resource_path,
                        os.path.join(
                            STAGING_PATH,
                            'resource',
                            os.path.basename(resource_path),
                        ),
                    )
                else:
                    logging.warning(
                        'Resource "{}" does not exist!'.format(resource_path)
                    )

        # Collect dependencies and extensions
        dependencies_path = os.path.join(STAGING_PATH, 'dependencies')
        extensions_destination_path = os.path.join(STAGING_PATH, 'extensions')

        os.makedirs(dependencies_path)
        os.makedirs(extensions_destination_path)

        extras = None
        if not args.from_source:
            extras = ['ftrack-libs']
        if USES_FRAMEWORK:
            if not args.from_source:
                extras.append('framework-libs')

            logging.info(
                'Collecting Framework extensions and libs, building dependencies...'
            )
            framework_extensions = []

            for target_folder, extension_base_path in [
                (
                    'common',
                    os.path.join(
                        MONOREPO_PATH,
                        'projects',
                        'framework-common-extensions',
                    ),
                ),
                (DCC_NAME, EXTENSION_PATH),
            ]:
                for extension in os.listdir(extension_base_path):
                    extension_source_path = os.path.join(
                        extension_base_path, extension
                    )
                    if (
                        not os.path.isdir(extension_source_path)
                        or extension
                        == 'launch'  # Launch deployed to root of Connect plugin
                        or extension
                        == 'js'  # Skip JS extensions, built to CEP plugin
                    ):
                        continue
                    logging.info(
                        'Adding extension: {}'.format(extension_source_path)
                    )
                    framework_extensions.append(
                        (target_folder, extension_source_path)
                    )

            for target_folder, dependency_path in framework_extensions:
                requirements_path = os.path.join(
                    dependency_path, 'requirements.txt'
                )
                if os.path.exists(requirements_path):
                    logging.info(
                        'Building Python extension dependencies @ "{}"'.format(
                            requirements_path
                        )
                    )
                    os.chdir(dependency_path)

                    commands = [
                        sys.executable,
                        '-m',
                        'pip',
                        'install',
                        '-r',
                        requirements_path,
                    ]
                    if extras:
                        commands.extend(
                            [
                                '-e',
                                f'.[{",".join(extras)}]',
                            ]
                        )
                    commands.extend(
                        [
                            '--target',
                            dependencies_path,
                        ]
                    )
                    subprocess.check_call()

                # Copy the extension
                logging.info('Copying {}'.format(dependency_path))
                filename = os.path.basename(dependency_path)

                dest_path = os.path.join(
                    extensions_destination_path, target_folder, filename
                )
                if not os.path.exists(os.path.dirname(dest_path)):
                    os.makedirs(os.path.dirname(dest_path))
                elif os.path.exists(dest_path):
                    continue
                shutil.copytree(
                    dependency_path,
                    dest_path,
                )

            # Copy DCC config
            dcc_config_path = os.path.join(
                EXTENSION_PATH, '{}.yaml'.format(DCC_NAME)
            )
            if os.path.isfile(dcc_config_path):
                logging.info('Copying DCC config')
                dest_path = os.path.join(
                    STAGING_PATH,
                    'extensions',
                    DCC_NAME,
                    '{}.yaml'.format(DCC_NAME),
                )
                if not os.path.exists(os.path.dirname(dest_path)):
                    os.makedirs(os.path.dirname(dest_path))
                shutil.copy(
                    dcc_config_path,
                    dest_path,
                )
            else:
                raise Exception(
                    'Missing DCC config file: {}'.format(dcc_config_path)
                )

        if args.from_source:
            # Build library dependencies from source
            libs_path = os.path.join(MONOREPO_PATH, 'libs')
            for filename in os.listdir(libs_path):
                lib_path = os.path.join(libs_path, filename)
                if not os.path.isfile(
                    os.path.join(lib_path, 'pyproject.toml')
                ):
                    continue
                elif filename not in FTRACK_DEP_LIBS:
                    continue
                # Cleanup
                dist_path = os.path.join(lib_path, 'dist')
                if os.path.exists(dist_path):
                    logging.warning(
                        'Cleaning lib dist folder: {}'.format(dist_path)
                    )
                    shutil.rmtree(dist_path)
                if filename == 'qt-style':
                    # Need to build qt resources
                    logging.info('Building style for {}'.format(filename))
                    save_cwd = os.getcwd()
                    os.chdir(MONOREPO_PATH)
                    build_package(
                        'libs/qt-style', args, command='build_qt_resources'
                    )
                    os.chdir(save_cwd)
                # Build
                logging.info('Building wheel for {}'.format(filename))
                subprocess.check_call(['poetry', 'build'], cwd=lib_path)

                # Locate result
                for wheel_name in os.listdir(dist_path):
                    if not wheel_name.endswith('.whl'):
                        continue
                    # Install it
                    logging.info('Installing library: {}'.format(wheel_name))
                    subprocess.check_call(
                        [
                            sys.executable,
                            '-m',
                            'pip',
                            'install',
                            os.path.join(dist_path, wheel_name),
                            '--target',
                            dependencies_path,
                        ]
                    )

        logging.info(
            f'Exporting dependencies from: "{os.path.basename(lock_path)}" (extras: {extras})'
        )
        # Run Poetry export and read the output
        requirements_path = os.path.join(STAGING_PATH, 'requirements.txt')
        commands = [
            'poetry',
            'export',
            '-f',
            'requirements.txt',
            '--without-hashes',
            '-o',
            requirements_path,
        ]
        if extras:
            for extra in extras:
                commands.extend(['-E', extra])

        subprocess.check_call(commands)

        logging.info(
            f'Installing {wheel_path} with dependencies from "{os.path.basename(requirements_path)}"'
        )
        commands = [
            sys.executable,
            '-m',
            'pip',
            'install',
            wheel_path,
            '-r',
            requirements_path,
            '--target',
            dependencies_path,
        ]
        if args.testpypi:
            # Try to pick first from pypi if not exist go to test pypi
            commands.extend(
                [
                    '--pre',
                    '--index-url',
                    'https://pypi.org/simple',
                    '--extra-index-url',
                    'https://test.pypi.org/simple',
                ]
            )

        subprocess.check_call(commands)

        if args.include_assets:
            for asset_path in args.include_assets.split(','):
                asset_destination_path = os.path.basename(asset_path)
                logging.info('Copying asset "{}"'.format(asset_path))
                if os.path.isdir(asset_path):
                    shutil.copytree(
                        asset_path,
                        os.path.join(STAGING_PATH, asset_destination_path),
                    )
                else:
                    shutil.copy(
                        asset_path,
                        os.path.join(STAGING_PATH, asset_destination_path),
                    )

        logging.info('Creating archive')
        archive_path = os.path.join(BUILD_PATH, os.path.basename(STAGING_PATH))
        if PLATFORM_DEPENDENT:
            if sys.platform.startswith('win'):
                archive_path = '{}-windows'.format(archive_path)
            elif sys.platform.startswith('darwin'):
                archive_path = '{}-mac'.format(archive_path)
            else:
                archive_path = '{}-linux'.format(archive_path)

        shutil.make_archive(
            archive_path,
            'zip',
            STAGING_PATH,
        )

        logging.info(
            'Built Connect plugin archive: {}.zip'.format(archive_path)
        )

        if args.remove_intermediate_folder:
            logging.warning(f'Removing: {STAGING_PATH}')
            shutil.rmtree(STAGING_PATH, ignore_errors=True)

    def _replace_imports_(resource_target_path):
        '''Replace imports in resource files to Qt instead of QtCore.

        This allows the resource file to work with many different versions of
        Qt.

        '''
        replace = r'from Qt import QtCore'
        for line in fileinput.input(
            resource_target_path, inplace=True, mode='r'
        ):
            if r'import QtCore' in line:
                # Calling print will yield a new line in the resource file.
                sys.stdout.write(line.replace(line, replace))
            else:
                sys.stdout.write(line)

    def build_qt_resources(args):
        '''Build resources.py from style'''
        try:
            import scss
        except ImportError:
            raise RuntimeError(
                'Error compiling sass files. Could not import "scss". '
                'Check you have the pyScss Python package installed.'
            )

        style_path = args.style_path if args else None
        if style_path is None:
            style_path = DEFAULT_STYLE_PATH
        else:
            style_path = os.path.realpath(style_path)
        if not os.path.exists(style_path):
            raise Exception('Missing "{}/" folder!'.format(style_path))

        sass_path = os.path.join(style_path, 'sass')
        css_path = style_path
        resource_source_path = os.path.join(style_path, 'resource.qrc')

        resource_target_path = args.output_path if args else None
        if resource_target_path is None:
            resource_target_path = os.path.join(SOURCE_PATH, 'resource.py')

        # Any styles to compile?
        if os.path.exists(sass_path):
            compiler = scss.Scss(search_paths=[sass_path])

            themes = ['style_light', 'style_dark']
            for theme in themes:
                scss_source = os.path.join(sass_path, '{0}.scss'.format(theme))
                css_target = os.path.join(css_path, '{0}.css'.format(theme))

                logging.info("Compiling {}".format(scss_source))
                compiled = compiler.compile(scss_file=scss_source)
                with open(css_target, 'w') as file_handle:
                    file_handle.write(compiled)
                    logging.info('Compiled {0}'.format(css_target))
        else:
            logging.warning('No styles to compile.')

        try:
            pyside_rcc_command = 'pyside2-rcc'
            executable = None

            # Check if the command for pyside*-rcc is in executable paths.
            if find_executable(pyside_rcc_command):
                executable = [pyside_rcc_command]

            if not executable:
                logging.warning(
                    'No executable found for pyside2-rcc, attempting to run as '
                    'a module'
                )
                executable = [sys.executable, '-m', 'scss']

            # Use the first occurrence if more than one is found.
            cmd = executable + [
                '-o',
                resource_target_path,
                resource_source_path,
            ]
            logging.info('Running: {}'.format(cmd))
            subprocess.check_call(cmd)

        except (subprocess.CalledProcessError, OSError):
            raise RuntimeError(
                'Error compiling resource.py using pyside-rcc. Possibly '
                'pyside-rcc could not be found. You might need to manually add '
                'it to your PATH. See README for more information.'
            )

        _replace_imports_(resource_target_path)

    def build_sphinx(args):
        '''Wrapper for building docs for preview'''

        if not os.path.exists(BUILD_PATH):
            os.makedirs(BUILD_PATH)

        DOC_PATH = os.path.join(BUILD_PATH, 'doc')

        cmd = 'sphinx-build doc {}'.format(DOC_PATH)
        logging.info('Running: {}'.format(cmd))
        os.system(cmd)

    def build_cep(args):
        '''Wrapper for building Adobe CEP extension'''

        if not os.path.exists(CEP_PATH):
            raise Exception('Missing "{}/" folder!'.format(CEP_PATH))

        MANIFEST_PATH = os.path.join(CEP_PATH, 'bundle', 'manifest.xml')
        if not os.path.exists(MANIFEST_PATH):
            raise Exception('Missing manifest:{}!'.format(MANIFEST_PATH))

        if not args.nosign:
            if len(os.environ.get('ADOBE_CERTIFICATE_PASSWORD') or '') == 0:
                raise Exception(
                    'Need certificate password in ADOBE_CERTIFICATE_PASSWORD '
                    'environment variable!'
                )

        ZXPSIGN_CMD_PATH = find_executable(ZXPSIGN_CMD)
        if not ZXPSIGN_CMD_PATH:
            raise Exception('%s is not in your ${PATH}!' % (ZXPSIGN_CMD))

        CERTIFICATE_PATH = os.path.join(CEP_PATH, 'bundle', 'certificate.p12')
        if not os.path.exists(CERTIFICATE_PATH):
            raise Exception(
                'Certificate missing: {}!'.format(CERTIFICATE_PATH)
            )

        STAGING_PATH = os.path.join(BUILD_PATH, 'staging')

        # Clean previous build
        if os.path.exists(BUILD_PATH):
            for filename in os.listdir(BUILD_PATH):
                if filename.endswith('.zxp'):
                    logging.warning(
                        'Removed previous build: {}'.format(filename)
                    )
                    os.remove(os.path.join(BUILD_PATH, filename))

        # Clean staging path
        shutil.rmtree(STAGING_PATH, ignore_errors=True)
        os.makedirs(os.path.join(STAGING_PATH))
        os.makedirs(os.path.join(STAGING_PATH, 'image'))
        os.makedirs(os.path.join(STAGING_PATH, 'css'))

        # Build resources
        logging.info('Building style...')
        save_cwd = os.getcwd()
        os.chdir(MONOREPO_PATH)
        build_package('libs/qt-style', args, command='build_qt_resources')
        os.chdir(save_cwd)

        style_path = args.style_path
        if style_path is None:
            style_path = DEFAULT_STYLE_PATH
        else:
            style_path = os.path.realpath(style_path)
        if not os.path.exists(style_path):
            raise Exception('Missing "{}/" folder!'.format(style_path))

        # Copy html
        for filename in ['index.html']:
            parse_and_copy(
                os.path.join(CEP_PATH, filename),
                os.path.join(STAGING_PATH, filename),
            )

        # Copy images
        logging.info("Copying images")
        for filename in [
            'favicon.ico',
            'ftrack-logo-48.png',
            'loader.gif',
            'thumbnail.png',
            'open_in_new.png',
            'publish.png',
            'open.png',
        ]:
            logging.info("   " + filename)
            shutil.copy(
                os.path.join(style_path, 'image', 'js', filename),
                os.path.join(STAGING_PATH, 'image', filename),
            )

        filename = 'style_dark.css'
        logging.info("Copying style: {}".format(filename))
        shutil.copy(
            os.path.join(style_path, filename),
            os.path.join(STAGING_PATH, 'css', filename),
        )

        logging.info(
            'Copying {}>{}'.format(
                os.path.join(CEP_PATH, 'libraries'),
                os.path.join(STAGING_PATH, 'lib'),
            )
        )
        shutil.copytree(
            os.path.join(CEP_PATH, 'libraries'),
            os.path.join(STAGING_PATH, 'lib'),
            symlinks=True,
        )

        logging.info("Copying framework js lib files")
        for js_file in [
            os.path.join(
                MONOREPO_PATH,
                'projects',
                'framework-photoshop-js',
                'source',
                'utils.js',
            ),
            os.path.join(
                MONOREPO_PATH,
                'projects',
                'framework-photoshop-js',
                'source',
                'event-constants.js',
            ),
            os.path.join(
                MONOREPO_PATH,
                'projects',
                'framework-photoshop-js',
                'source',
                'events-core.js',
            ),
        ]:
            parse_and_copy(
                js_file,
                os.path.join(STAGING_PATH, 'lib', os.path.basename(js_file)),
            )
        for filename in ['bootstrap.js', 'ps.jsx']:
            parse_and_copy(
                os.path.join(
                    MONOREPO_PATH,
                    'projects',
                    'framework-photoshop-js',
                    'source',
                    filename,
                ),
                os.path.join(STAGING_PATH, filename),
            )

        # Transfer manifest xml, store version
        manifest_staging_path = os.path.join(
            STAGING_PATH, 'CSXS', 'manifest.xml'
        )
        if not os.path.exists(os.path.dirname(manifest_staging_path)):
            os.makedirs(os.path.dirname(manifest_staging_path))
        parse_and_copy(MANIFEST_PATH, manifest_staging_path)

        extension_output_path = os.path.join(
            BUILD_PATH,
            'ftrack-framework-adobe-{}.zxp'.format(VERSION),
        )

        if not args.nosign:
            # Create and sign extension
            if os.path.exists(extension_output_path):
                os.remove(extension_output_path)

            result = subprocess.Popen(
                [
                    ZXPSIGN_CMD_PATH,
                    '-sign',
                    STAGING_PATH,
                    extension_output_path,
                    CERTIFICATE_PATH,
                    '{}'.format(os.environ['ADOBE_CERTIFICATE_PASSWORD']),
                ]
            )
            result.communicate()
            if result.returncode != 0:
                raise Exception('Could not sign and build extension!')

            logging.info('Result: ' + extension_output_path)
        else:
            logging.warning(
                'Not signing and creating ZPX plugin, result for for '
                'manual deploy can be found here: {}'.format(STAGING_PATH)
            )

        if args.remove_intermediate_folder:
            logging.warning(f'Removing: {STAGING_PATH}')
            shutil.rmtree(STAGING_PATH, ignore_errors=True)

    def build_rvpkg(args):
        '''Wrapper for building RV plugin package'''

        def copytree(src, dst, symlinks=False, ignore=None):
            '''Copy file tree from *src* to *dst*, replacing PACKAGE.yml with PACKAGE'''
            print('Copying {0} to {1}'.format(src, dst))
            for item in os.listdir(src):
                if item == 'BUILD_PANTS':
                    continue
                s = os.path.join(src, item)
                d = os.path.join(
                    dst, item if item != "PACKAGE.yml" else "PACKAGE"
                )
                if os.path.isdir(s):
                    shutil.copytree(s, d, symlinks, ignore)
                else:
                    if not os.path.exists(os.path.dirname(d)):
                        os.makedirs(os.path.dirname(d))
                    print(shutil.copy2(s, d))

        rvpkg_staging = os.path.join(tempfile.mkdtemp(), 'rvpkg')

        source_path = os.path.join(ROOT_PATH, 'resource', 'plugin')

        # Copy plugin files
        copytree(source_path, rvpkg_staging)

        # Strip off patch version from the tool: M.m rather than M.m.p
        plugin_name = 'ftrack-{0}'.format(VERSION)

        assert args.output_path, 'RV pkg output path not given'
        plugin_destination_path = args.output_path

        if not os.path.exists(plugin_destination_path):
            os.makedirs(plugin_destination_path)

        if not os.path.exists(os.path.join(rvpkg_staging, 'PACKAGE')):
            raise IOError('no PACKAGE.yml file in {0}'.format(rvpkg_staging))

        package_file_path = os.path.join(rvpkg_staging, 'PACKAGE')
        package_file = fileinput.input(package_file_path, inplace=True)
        for line in package_file:
            if '{VERSION}' in line:
                sys.stdout.write(line.format(VERSION=VERSION))
            else:
                sys.stdout.write(line)

        zip_destination_file_path = os.path.join(
            plugin_destination_path, plugin_name
        )

        rvpkg_destination_file_path = os.path.join(
            plugin_destination_path, plugin_name + '.rvpkg'
        )

        # prepare zip with rv plugin
        print('packing rv plugin to {0}'.format(rvpkg_destination_file_path))

        zip_name = shutil.make_archive(
            base_name=zip_destination_file_path,
            format='zip',
            root_dir=rvpkg_staging,
        )

        shutil.move(zip_name, rvpkg_destination_file_path)

        if args.remove_intermediate_folder:
            logging.warning(f'Removing: {rvpkg_staging}')
            shutil.rmtree(rvpkg_staging, ignore_errors=True)

    if command == 'clean':
        clean(args)
    elif command == 'build_connect_plugin':
        build_connect_plugin(args)
    elif command == 'build_qt_resources':
        build_qt_resources(args)
    elif command == 'build_sphinx':
        build_sphinx(args)
    elif command == 'build_cep':
        build_cep(args)
    elif command == 'build_rvpkg':
        build_rvpkg(args)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    logging.info(
        'ftrack Integration deployment script v{}'.format(__version__)
    )

    # Connect plugin options
    parser.add_argument(
        '--include_assets',
        help='(Connect plugin) Comma separated list of additional asset to include.',
    )
    parser.add_argument(
        '--include_resources',
        help='(Connect plugin) Comma separated list of resources to include.',
    )

    parser.add_argument(
        '--from_source',
        help='(Connect plugin) Instead of pulling from PyPi, uses dependencies '
        'directly from sources.',
        action='store_true',
    )

    parser.add_argument(
        '--remove_intermediate_folder',
        help='(Connect plugin) Remove the intermediate staging plugin folder after '
        'archive creation.',
        action='store_true',
    )

    parser.add_argument(
        '--testpypi',
        help='Pip install from TestPyPi instead of public.',
        action='store_true',
    )

    # QT resource options
    parser.add_argument(
        '--style_path',
        help='(QT resource build) Override the default style path (resource/style).',
    )
    parser.add_argument(
        '--output_path',
        help='(QT resource build/RV pkg build) Override the QT resource output directory.',
    )

    # CEP options
    parser.add_argument(
        '--nosign',
        help='(CEP plugin build) Do not sign and create ZXP.',
        action='store_true',
    )

    parser.add_argument(
        'command',
        help=(
            'clean; Clean(remove) build folder \n'
            'build_connect_plugin; Build Connect plugin archive\n'
            'build_resources; Build QT resources\n'
        ),
        choices=[
            'clean',
            'build_connect_plugin',
            'build_qt_resources',
            'build_sphinx',
            'build_cep',
            'build_rvpkg',
        ],
    )

    parser.add_argument(
        'packages',
        help=(
            'Comma separated list of relative or absolute package paths to build\n'
        ),
    )

    args = parser.parse_args()

    if args.command is None:
        raise Exception('No command given!')

    if args.packages is None or len(args.packages) == 0:
        raise Exception('No packages given!')

    for pkg_path in args.packages.split(','):
        pkg_path = pkg_path.strip()
        if not os.path.exists(pkg_path):
            raise Exception(f'Package path "{pkg_path}" does not exist!')
        if not os.path.exists(
            os.path.join(pkg_path, 'pyproject.toml')
        ) and not os.path.exists(os.path.join(pkg_path, 'setup.py')):
            raise Exception(
                f'Package path "{pkg_path}" does not contain a Setuptools or Poetry '
                'project!'
            )
        logging.info('*' * 100)
        logging.info(f'Building package: {pkg_path}')
        build_package(pkg_path, args)
