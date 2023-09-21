# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

'''
Poetry/Github CI/CD build and deployment tooling, replaces original setuptools implementation.

Designed to be shared across a Monorepo

Version history:

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

__version__ = '0.3.1'

ROOT_PATH = os.path.realpath(os.getcwd())
BUILD_PATH = os.path.join(ROOT_PATH, "dist")
RESOURCE_PATH = os.path.join(ROOT_PATH, "resource")
STYLE_PATH = os.path.join(RESOURCE_PATH, "style")
CEP_PATH = os.path.join(ROOT_PATH, "source", "cep")

PROJECT_NAME = None
with open(os.path.join(ROOT_PATH, 'pyproject.toml')) as f:
    for line in f:
        if line.startswith('name = '):
            PROJECT_NAME = line.split('=')[1].strip().strip('"')
            break

SOURCE_PATH = os.path.join(ROOT_PATH, "source", PROJECT_NAME.replace('-', '_'))

ZXPSIGN_CMD = 'ZXPSignCmd'

logging.getLogger().setLevel(logging.INFO)


def clean(args):
    '''Remove build folder'''

    if not os.path.exists(BUILD_PATH):
        logging.warning('Missing "dist/" folder!')

    logging.info('Cleaning up {}'.format(BUILD_PATH))
    shutil.rmtree(BUILD_PATH, ignore_errors=True)


def build_plugin(args):
    '''Build the Connect plugin archive ready to be deployed in the Plugin manager'''

    if not os.path.exists(BUILD_PATH):
        raise Exception('Please build the project - missing "dist/" folder!')

    # Find wheel and read the version
    wheel_path = None
    VERSION = None
    for filename in os.listdir(BUILD_PATH):
        # Expect: ftrack_connect_pipeline_qt-1.3.0a1-py3-none-any.whl
        if not filename.endswith('.whl'):
            continue
        wheel_path = os.path.join(BUILD_PATH, filename)
        parts = filename.split('-')
        VERSION = parts[1]
        break

    if not VERSION:
        raise Exception('Could not locate a built python wheel!')

    STAGING_PATH = os.path.join(
        BUILD_PATH, '{}-{}'.format(PROJECT_NAME, VERSION)
    )

    '''Run the build step.'''
    # Clean staging path
    logging.info('Cleaning up {}'.format(STAGING_PATH))
    shutil.rmtree(STAGING_PATH, ignore_errors=True)

    # Copy hook
    logging.info('Copying hook')
    HOOK_PATH = os.path.join(ROOT_PATH, 'hook')
    shutil.copytree(HOOK_PATH, os.path.join(STAGING_PATH, 'hook'))

    # Copy resources
    logging.info('Copying resources')
    shutil.copytree(RESOURCE_PATH, os.path.join(STAGING_PATH, 'resource'))

    # Build dependencies
    dependencies_path = os.path.join(STAGING_PATH, 'dependencies')

    os.makedirs(dependencies_path)

    logging.info('Collecting dependencies')
    subprocess.check_call(
        [
            sys.executable,
            '-m',
            'pip',
            'install',
            wheel_path,
            '--target',
            dependencies_path,
        ]
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

    logging.info('Built Connect plugin archive: {}.zip'.format(archive_path))


def _replace_imports_(resource_target_path):
    '''Replace imports in resource files to Qt instead of QtCore.

    This allows the resource file to work with many different versions of
    Qt.

    '''
    replace = r'from Qt import QtCore'
    for line in fileinput.input(resource_target_path, inplace=True, mode='r'):
        if r'import QtCore' in line:
            # Calling print will yield a new line in the resource file.
            sys.stdout.write(line.replace(line, replace))
        else:
            sys.stdout.write(line)


def build_resources(args):
    '''Build resources.py from style'''
    try:
        import scss
    except ImportError:
        raise RuntimeError(
            'Error compiling sass files. Could not import "scss". '
            'Check you have the pyScss Python package installed.'
        )

    if not os.path.exists(STYLE_PATH):
        raise Exception('Missing "{}/" folder!'.format(STYLE_PATH))

    sass_path = os.path.join(STYLE_PATH, 'sass')
    css_path = STYLE_PATH
    resource_source_path = os.path.join(STYLE_PATH, 'resource.qrc')
    resource_target_path = os.path.join(SOURCE_PATH, 'ui', 'resource.py')

    compiler = scss.Scss(search_paths=[sass_path])

    themes = ['style_light', 'style_dark']
    for theme in themes:
        scss_source = os.path.join(sass_path, '{0}.scss'.format(theme))
        css_target = os.path.join(css_path, '{0}.css'.format(theme))

        compiled = compiler.compile(scss_file=scss_source)
        with open(css_target, 'w') as file_handle:
            file_handle.write(compiled)
            print('Compiled {0}'.format(css_target))

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


def get_version():
    '''Read version from _version.py, updated by CI based on monorepo package tag'''
    if 'POETRY_DYNAMIC_VERSIONING_BYPASS' in os.environ:
        result = os.environ['POETRY_DYNAMIC_VERSIONING_BYPASS']
        if result.startswith('v'):
            return result[1:]
        else:
            return result
    version_path = os.path.join(SOURCE_PATH, '_version.py')
    with open(version_path, 'r') as file_handle:
        for line in file_handle.readlines():
            if line.find('__version__') > -1:
                return re.findall(r'\'(.*)\'', line)[0].strip()
    raise ValueError('Could not find version in {0}'.format(version_path))


def build_cep(args):
    '''Wrapper for building docs for preview'''

    if not os.path.exists(CEP_PATH):
        raise Exception('Missing "{}/" folder!'.format(CEP_PATH))

    MANIFEST_PATH = os.path.join(CEP_PATH, "bundle", "manifest.xml")
    if not os.path.exists(MANIFEST_PATH):
        raise Exception('Missing mainfest:{}!'.format(MANIFEST_PATH))

    if len(os.environ.get('FTRACK_ADOBE_CERTIFICATE_PASSWORD') or '') == 0:
        raise Exception(
            'Need certificate password in FTRACK_ADOBE_CERTIFICATE_PASSWORD environment variable!'
        )

    ZXPSIGN_CMD_PATH = find_executable(ZXPSIGN_CMD)
    if not ZXPSIGN_CMD_PATH:
        raise Exception('%s is not in your ${PATH}!' % (ZXPSIGN_CMD))

    CERTIFICATE_PATH = os.path.join(CEP_PATH, 'bundle', 'certificate.p12')
    if not os.path.exists(CERTIFICATE_PATH):
        raise Exception("Certificate missing: {}!".format(CERTIFICATE_PATH))

    STAGING_PATH = os.path.join(BUILD_PATH, "staging")

    VERSION = get_version()

    # Clean staging path
    shutil.rmtree(STAGING_PATH, ignore_errors=True)
    os.makedirs(STAGING_PATH)

    # Copy files
    for filename in ["index.html", "index.js", "ps.jsx", "favicon.ico"]:
        shutil.copy(
            os.path.join(CEP_PATH, filename),
            os.path.join(STAGING_PATH, filename),
        )
    # Copy dirs
    for filename in ["lib", "icons", "css"]:
        logging.info(
            "Copying {}>{}".format(
                os.path.join(CEP_PATH, filename),
                os.path.join(STAGING_PATH, filename),
            )
        )
        shutil.copytree(
            os.path.join(CEP_PATH, filename),
            os.path.join(STAGING_PATH, filename),
            symlinks=True,
        )

    # Transfer manifest xml, store version
    manifest_staging_path = os.path.join(STAGING_PATH, 'CSXS', 'manifest.xml')
    if not os.path.exists(os.path.dirname(manifest_staging_path)):
        os.makedirs(os.path.dirname(manifest_staging_path))
    with open(MANIFEST_PATH, 'r') as f_src:
        with open(manifest_staging_path, 'w') as f_dst:
            f_dst.write(
                f_src.read().replace(
                    '{{FTRACK_FRAMEWORK_PHOTOSHOP_VERSION}}', VERSION
                )
            )

    extension_output_path = os.path.join(
        BUILD_PATH,
        'ftrack_framework_adobe_prototype_{}.zxp'.format(VERSION),
    )

    # Generate auto update xml
    # update_staging_path = os.path.join(STAGING_PATH, 'update.xml')
    # with open(UPDATE_PATH, 'r') as f_src:
    #    with open(update_staging_path, 'w') as f_dst:
    #        f_dst.write(f_src.read().
    #                    replace('<%= bundle.version %>', VERSION).
    #                    replace('<%= download_url %>', os.path.basename(extension_output_path)).
    #                    replace('<%= bundle.description %>', 'ftrack connect extension for Adobe Creative Cloud.')
    #                    )

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
            '{}'.format(os.environ['FTRACK_ADOBE_CERTIFICATE_PASSWORD']),
        ]
    )
    result.communicate()
    if result.returncode != 0:
        raise Exception('Could not sign and build extension!')

    print('Result: ' + extension_output_path)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    # Check if running from the correct location
    project_conf_path = os.path.join(ROOT_PATH, 'pyproject.toml')
    if not os.path.exists(project_conf_path):
        raise Exception('Tool must be run within the Poetry project folder')

    logging.info(
        'ftrack Integration deployment script v{} [{}]'.format(
            __version__, PROJECT_NAME
        )
    )

    parser.add_argument(
        'command',
        help=(
            'clean; Clean(remove) build folder \n'
            'build_plugin; Build Connect plugin archive\n'
            'build_resources; Build QT resources\n'
        ),
        choices=[
            'clean',
            'build_plugin',
            'build_resources',
            'build_resources',
            'build_sphinx',
            'build_cep',
        ],
    )

    args = parser.parse_args()

    if args.command is None:
        raise Exception('No command given!')

    if args.command == 'clean':
        clean(args)
    elif args.command == 'build_plugin':
        build_plugin(args)
    elif args.command == 'build_resources':
        build_resources(args)
    elif args.command == 'build_sphinx':
        build_sphinx(args)
    elif args.command == 'build_cep':
        build_cep(args)
