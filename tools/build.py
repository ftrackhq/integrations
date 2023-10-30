# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

'''
ftrack Integrations build and deployment tooling.

Temporary replaces original setuptools implementation until there is an
official CI/CD build implementation in place.


Release notes:

0.4.7, Henrik Norin, 23.10.30; Read package version from pyproject.toml, parse and replace version in Connect hooks.
0.4.6, Henrik Norin, 23.10.30; Allow pre releases on Connect build when enabling test PyPi.
0.4.5, Henrik Norin, 23.10.26; Support for including assets in Connect plugin build.
0.4.4, Henrik Norin, 23.10.13; Support for building multiple packages at once.
0.4.3, Henrik Norin, 23.10.11; Support for additional CEP JS include folder
0.4.2, Henrik Norin, 23.10.09; Support for additional hook include folder
0.4.1, Henrik Norin, 23.10.02; Redone Photoshop CEP build
0.4.0, Henrik Norin, 23.09.21; Build within Monorepo, refactored framework
0.3.1, Henrik Norin, 23.08.29; CEP build updates
0.3.0, Henrik Norin, 23.07.06; Support for building CEP extension
0.2.0, Henrik Norin, 23.04.17; Supply resource folder on plugin build
0.1.0, Henrik Norin, 23.03.08; Initial version

'''

import argparse
import os
import shutil
import logging
import sys
import re
import subprocess
from distutils.spawn import find_executable
import fileinput

__version__ = '0.4.7'

ZXPSIGN_CMD = 'ZXPSignCmd'

logging.getLogger().setLevel(logging.INFO)


def build_package(pkg_path, args):
    '''Build the package @ pkg_path'''
    os.chdir(pkg_path)

    ROOT_PATH = os.path.realpath(os.getcwd())
    BUILD_PATH = os.path.join(ROOT_PATH, 'dist')
    RESOURCE_PATH = os.path.join(ROOT_PATH, 'resource')
    CEP_PATH = os.path.join(ROOT_PATH, 'resource', 'cep')

    POETRY_CONFIG_PATH = os.path.join(ROOT_PATH, 'pyproject.toml')
    if os.path.exists(POETRY_CONFIG_PATH):
        PROJECT_NAME = None
        VERSION = None
        with open(os.path.join(ROOT_PATH, 'pyproject.toml')) as f:
            for line in f:
                if line.startswith('name = '):
                    PROJECT_NAME = line.split('=')[1].strip().strip('"')
                elif line.startswith('version = '):
                    VERSION = line.split('=')[1].strip().strip('"')
                    break

        DCC_NAME = PROJECT_NAME.split('-')[-1]
        assert VERSION, 'No version could be extracted from "pyproject.toml"!'
    else:
        logging.warning(
            'Missing "pyproject.toml" file, not able to identify target DCC!'
        )

        PROJECT_NAME = 'ftrack-{}'.format(os.path.basename(ROOT_PATH))
        DCC_NAME = None
        VERSION = '0.0.0'

    SOURCE_PATH = os.path.join(
        ROOT_PATH, 'source', PROJECT_NAME.replace('-', '_')
    )

    MONOREPO_PATH = os.path.realpath(os.path.join(ROOT_PATH, '..', '..'))

    DEFAULT_STYLE_PATH = os.path.join(MONOREPO_PATH, 'resource', 'style')

    def clean(args):
        '''Remove build folder'''

        if not os.path.exists(BUILD_PATH):
            logging.warning('Missing "dist/" folder!')

        logging.info('Cleaning up {}'.format(BUILD_PATH))
        shutil.rmtree(BUILD_PATH, ignore_errors=True)

    def find_python_source(source_path):
        '''Find a python package in *source_path*'''
        candidate = None
        for filename in os.listdir(source_path):
            pkg_path = os.path.join(source_path, filename)
            if os.path.isfile(pkg_path):
                continue
            if os.path.exists(os.path.join(pkg_path, '__init__.py')):
                return pkg_path
            elif filename.startswith('ftrack_'):
                candidate = pkg_path
        if candidate:
            return candidate
        raise Exception(
            'No Python source package found @ "{}"'.format(source_path)
        )

    def parse_and_copy(source_path, target_path):
        '''Copies the single file pointed out by *source_path* to *target_path* and
        replaces version expression to supplied *version*.'''
        logging.info(
            'Parsing and copying {}>{}'.format(source_path, target_path)
        )
        with open(source_path, 'r') as f_src:
            with open(target_path, 'w') as f_dst:
                f_dst.write(
                    f_src.read().replace('{{PACKAGE_VERSION}}', VERSION)
                )

    def build_connect_plugin(args):
        '''
        Build the Connect plugin archive ready to be deployed in the Plugin manager.

        Collects all the library and hook dependencies for an integration or component.
        '''

        if not os.path.exists(BUILD_PATH):
            raise Exception(
                'Please build the project - missing "dist/" folder!'
            )

        logging.info('*' * 100)
        logging.info(
            'Remember to build the plugin with Poetry (poetry build) before '
            'building the Connect plugin!'
        )
        logging.info('*' * 100)

        # Find wheel and read the version
        wheel_path = None
        for filename in os.listdir(BUILD_PATH):
            # Expect: ftrack_connect_pipeline_qt-1.3.0a1-py3-none-any.whl
            if not filename.endswith('.whl'):
                continue
            wheel_path = os.path.join(BUILD_PATH, filename)
            break

        if not wheel_path:
            raise Exception(
                'Could not locate a built python wheel! Please build with Poetry.'
            )

        STAGING_PATH = os.path.join(
            BUILD_PATH, '{}-{}'.format(PROJECT_NAME, VERSION)
        )

        '''Run the build step.'''
        # Clean staging path
        logging.info('Cleaning up {}'.format(STAGING_PATH))
        shutil.rmtree(STAGING_PATH, ignore_errors=True)

        # Locate and copy hook
        logging.info('Copying Connect hook')
        hook_source_path = None
        hook_search_paths = []
        if args.include_extensions:
            hook_search_paths.append(args.include_extensions)
        hook_search_paths.append(
            os.path.join(MONOREPO_PATH, 'extensions', DCC_NAME)
        )
        for hook_search_path in hook_search_paths:
            if not os.path.exists(hook_search_path):
                continue
            for filename in os.listdir(hook_search_path):
                if filename.replace('_', '-').endswith('-connect-hook'):
                    if os.path.exists(
                        os.path.join(hook_search_path, filename, 'source')
                    ):
                        # Standard hook location
                        hook_path_package = os.path.join(
                            hook_search_path,
                            filename,
                            'source',
                            'ftrack_framework_{}_connect_hook'.format(
                                DCC_NAME
                            ),
                        )
                    else:
                        # Hook is in root
                        hook_path_package = os.path.join(
                            hook_search_path, filename
                        )
                    if os.path.exists(hook_path_package):
                        for module_name in os.listdir(hook_path_package):
                            if module_name.startswith(
                                'discover_'
                            ) and module_name.endswith('.py'):
                                hook_source_path = os.path.join(
                                    hook_path_package, module_name
                                )
                                break
            if hook_source_path:
                break
        if not hook_source_path:
            # Look in resource
            path_resource_hook = os.path.join(RESOURCE_PATH, 'hook')
            if os.path.exists(path_resource_hook):
                for filename in os.listdir(path_resource_hook):
                    if filename.startswith('discover_') and filename.endswith(
                        '.py'
                    ):
                        hook_source_path = os.path.join(
                            path_resource_hook, filename
                        )
                        break
                if not hook_source_path:
                    raise Exception(
                        'Could not locate Connect hook module within resource folder!'
                    )
            else:
                raise Exception(
                    'Could not locate Connect hook module within "extensions"!'
                )
        logging.info(
            'Copying and substituting Connect hook from {}'.format(
                hook_source_path
            )
        )
        os.makedirs(os.path.join(STAGING_PATH, 'hook'))
        parse_and_copy(
            hook_source_path,
            os.path.join(
                STAGING_PATH, 'hook', os.path.basename(hook_source_path)
            ),
        )

        # # Copy resources
        # if os.path.exists(RESOURCE_PATH):
        #     logging.info('Copying resources')
        #     shutil.copytree(
        #         RESOURCE_PATH, os.path.join(STAGING_PATH, 'resource')
        #     )
        # else:
        #     logging.warning('No resources to copy.')

        # Collect dependencies
        dependencies_path = os.path.join(STAGING_PATH, 'dependencies')

        os.makedirs(dependencies_path)

        if args.with_extensions:
            logging.info(
                '(Experimental) Collecting Framework extensions and libs, building dependencies...'
            )
            framework_dependency_packages = []
            for lib in os.listdir(os.path.join(MONOREPO_PATH, 'libs')):
                lib_path = os.path.join(MONOREPO_PATH, 'libs', lib)
                if not os.path.isdir(lib_path):
                    continue
                hook_source_path = os.path.join(MONOREPO_PATH, 'libs', lib)
                framework_dependency_packages.append(hook_source_path)
                logging.info(
                    'Adding library package: {}'.format(hook_source_path)
                )

            # Pick up extensions
            if args.include_extensions:
                # First pick up includes
                include_path = os.path.join(
                    MONOREPO_PATH, args.include_extensions
                )
                if not os.path.exists(include_path):
                    # Might be an absolute path
                    include_path = args.include_extensions
                if not os.path.exists(include_path) or not os.path.isdir(
                    include_path
                ):
                    raise Exception(
                        'Include path "{}" does not exist or is not a folder!'.format(
                            include_path
                        )
                    )
                logging.info(
                    'Searching additional include path for packages: {}'.format(
                        include_path
                    )
                )
                for extension in os.listdir(include_path):
                    hook_source_path = os.path.join(include_path, extension)
                    if not os.path.isdir(hook_source_path):
                        continue
                    if not extension.endswith('-js'):
                        logging.info(
                            'Adding package include: {}'.format(
                                hook_source_path
                            )
                        )
                        framework_dependency_packages.append(hook_source_path)

            for extension_base_path in [
                os.path.join(MONOREPO_PATH, 'extensions', 'common'),
                os.path.join(MONOREPO_PATH, 'extensions', DCC_NAME),
            ]:
                for extension in os.listdir(extension_base_path):
                    hook_source_path = os.path.join(
                        extension_base_path, extension
                    )
                    if not os.path.isdir(hook_source_path):
                        continue
                    if not extension.endswith('-js'):
                        add = True
                        # Check if already in there
                        for existing in framework_dependency_packages:
                            if os.path.basename(existing) == extension:
                                add = False
                                break
                        if add:
                            logging.info(
                                'Adding package: {}'.format(hook_source_path)
                            )
                            framework_dependency_packages.append(
                                hook_source_path
                            )
                        else:
                            logging.warning()

            bootstrap_package_filename = (
                'ftrack_framework_{}_bootstrap'.format(DCC_NAME)
            )
            for dependency_path in framework_dependency_packages:
                if os.path.exists(os.path.join(dependency_path, 'setup.py')):
                    logging.info(
                        'Building Python dependencies for "{}"'.format(
                            os.path.basename(dependency_path)
                        )
                    )
                    os.chdir(dependency_path)
                    restore_build_file = False

                    PATH_BUILD = os.path.join(dependency_path, 'BUILD')
                    if os.path.exists(PATH_BUILD):
                        restore_build_file = True
                        os.rename(PATH_BUILD, PATH_BUILD + '_')

                    subprocess.check_call(
                        [
                            sys.executable,
                            '-m',
                            'pip',
                            'install',
                            '-e',
                            '.[ftrack-libs]',
                            '.',
                            '--target',
                            dependencies_path,
                        ]
                    )

                    shutil.rmtree(os.path.join(dependency_path, 'build'))

                    if restore_build_file:
                        os.rename(PATH_BUILD + '_', PATH_BUILD)

                else:
                    # Should have source folder but not having it is also allowed
                    source_path = os.path.join(dependency_path, 'source')
                    if os.path.exists(source_path):
                        source_path = find_python_source(source_path)
                    else:
                        source_path = dependency_path
                    logging.info('Copying {}'.format(source_path))
                    filename = os.path.basename(source_path)

                    if (
                        filename.endswith('_bootstrap')
                        and filename != bootstrap_package_filename
                    ):
                        # Rename bootstrap package to the correct name expected by app launcher for now
                        filename = bootstrap_package_filename
                    dest_path = os.path.join(dependencies_path, filename)
                    if os.path.exists(dest_path):
                        continue
                    shutil.copytree(
                        source_path,
                        dest_path,
                    )

        logging.info(
            'Installing package with dependencies from: "{}"'.format(
                os.path.basename(wheel_path)
            )
        )
        commands = [
            sys.executable,
            '-m',
            'pip',
            'install',
            '{}[ftrack-libs]'.format(wheel_path),
            '--target',
            dependencies_path,
        ]
        if args.testpypi:
            commands.extend(
                [
                    '--pre',
                    '--index-url',
                    'https://test.pypi.org/simple',
                    '--extra-index-url',
                    'https://pypi.org/simple',
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
        archive_path = os.path.join(
            BUILD_PATH, '{0}-{1}'.format(PROJECT_NAME, VERSION)
        )
        shutil.make_archive(
            archive_path,
            'zip',
            STAGING_PATH,
        )

        logging.info(
            'Built Connect plugin archive: {}.zip'.format(archive_path)
        )

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

        style_path = args.style_path
        if style_path is None:
            style_path = DEFAULT_STYLE_PATH
        else:
            style_path = os.path.realpath(style_path)
        if not os.path.exists(style_path):
            raise Exception('Missing "{}/" folder!'.format(style_path))

        sass_path = os.path.join(style_path, 'sass')
        css_path = style_path
        resource_source_path = os.path.join(style_path, 'resource.qrc')

        resource_target_path = args.output_path
        if resource_target_path is None:
            resource_target_path = os.path.join(SOURCE_PATH, 'resource.py')

        compiler = scss.Scss(search_paths=[sass_path])

        themes = ['style_light', 'style_dark']
        for theme in themes:
            scss_source = os.path.join(sass_path, '{0}.scss'.format(theme))
            css_target = os.path.join(css_path, '{0}.css'.format(theme))

            logging.info('Compiling {}'.format(scss_source))
            compiled = compiler.compile(scss_file=scss_source)
            with open(css_target, 'w') as file_handle:
                file_handle.write(compiled)
                logging.info('Compiled {0}'.format(css_target))

        try:
            pyside_rcc_command = 'pyside2-rcc'
            executable = None

            # Check if the command for pyside*-rcc is in executable paths.
            if find_executable(pyside_rcc_command):
                executable = pyside_rcc_command

            if not executable:
                raise IOError('Not executable found for pyside2-rcc ')

            # Use the first occurrence if more than one is found.
            cmd = [
                executable,
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

        # Clean staging path
        shutil.rmtree(STAGING_PATH, ignore_errors=True)
        os.makedirs(os.path.join(STAGING_PATH))
        os.makedirs(os.path.join(STAGING_PATH, 'image'))
        os.makedirs(os.path.join(STAGING_PATH, 'css'))

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
                VERSION,
            )
        # Copy images
        for filename in [
            'favicon.ico',
            'ftrack-logo-48.png',
            'loader.gif',
            'publish.png',
        ]:
            shutil.copy(
                os.path.join(style_path, 'image', 'js', filename),
                os.path.join(STAGING_PATH, 'image', filename),
            )

        # Copy style
        shutil.copy(
            os.path.join(style_path, 'style_dark.css'),
            os.path.join(STAGING_PATH, 'css', 'style_dark.css'),
        )

        # Copy static libraries
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

        # Copy framework js lib files
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
                VERSION,
            )
        parse_and_copy(
            os.path.join(
                MONOREPO_PATH,
                'projects',
                'framework-photoshop-js',
                'source',
                'bootstrap.js',
            ),
            os.path.join(STAGING_PATH, 'bootstrap.js'),
            VERSION,
        )
        parse_and_copy(
            os.path.join(
                MONOREPO_PATH,
                'projects',
                'framework-photoshop-js',
                'source',
                'ps.jsx',
            ),
            os.path.join(STAGING_PATH, 'ps.jsx'),
            VERSION,
        )
        if args.include_extensions:
            include_path = os.path.join(MONOREPO_PATH, args.include_extensions)
            if not os.path.exists(include_path):
                # Might be an absolute path
                include_path = args.include_extensions
            if not os.path.isdir(include_path):
                raise Exception(
                    'Include path "{}" is not a folder!'.format(include_path)
                )
            logging.info(
                'Searching additional include path for dependencies: {}'.format(
                    include_path
                )
            )
            for filename in os.listdir(include_path):
                parse_and_copy(
                    os.path.join(include_path, filename),
                    os.path.join(STAGING_PATH, filename),
                    VERSION,
                )

        # Transfer manifest xml, store version
        manifest_staging_path = os.path.join(
            STAGING_PATH, 'CSXS', 'manifest.xml'
        )
        if not os.path.exists(os.path.dirname(manifest_staging_path)):
            os.makedirs(os.path.dirname(manifest_staging_path))
        parse_and_copy(MANIFEST_PATH, manifest_staging_path, VERSION)

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

    if args.command == 'clean':
        clean(args)
    elif args.command == 'build_connect_plugin':
        build_connect_plugin(args)
    elif args.command == 'build_qt_resources':
        build_qt_resources(args)
    elif args.command == 'build_sphinx':
        build_sphinx(args)
    elif args.command == 'build_cep':
        build_cep(args)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    logging.info(
        'ftrack Integration deployment script v{}'.format(__version__)
    )

    # Connect plugin options
    parser.add_argument(
        '--with_extensions',
        help='(Connect plugin) Manually '
        'collect and include extensions (experimental).',
    )
    parser.add_argument(
        '--include_extensions', help='Additional extension folder to include.'
    )
    parser.add_argument(
        '--include_assets',
        help='(Connect plugin) Additional asset to include.',
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
        help='(QT resource build) Override the QT resource output directory.',
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
            raise Exception(
                'Package path "{}" does not exist!'.format(pkg_path)
            )
        if not os.path.exists(
            os.path.join(pkg_path, 'pyproject.toml')
        ) and not os.path.exists(os.path.join(pkg_path, 'setup.py')):
            raise Exception(
                'Package path "{}" does not contain a Setuptools or Poetry '
                'project!'.format(pkg_path)
            )
        logging.info('*' * 100)
        logging.info('Building package: {}'.format(pkg_path))
        build_package(pkg_path, args)
