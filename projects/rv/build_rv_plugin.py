# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack
'''
ftrack RV build tooling
'''

import argparse
import fileinput
import os
import shutil
import sys
import logging
import tempfile

__version__ = "0.1.0"


def copytree(src, dst, symlinks=False, ignore=None):
    print('Copying {0} to {1}'.format(src, dst))
    for item in os.listdir(src):
        if item == 'BUILD_PANTS':
            continue
        s = os.path.join(src, item)
        d = os.path.join(dst, item if item != "PACKAGE.yml" else "PACKAGE")
        if os.path.isdir(s):
            shutil.copytree(s, d, symlinks, ignore)
        else:
            if not os.path.exists(os.path.dirname(d)):
                os.makedirs(os.path.dirname(d))
            print(shutil.copy2(s, d))


def build_rvpkg(source_path, output_path, version):
    '''Build rv plugin package.'''

    if version is None:
        version = '0.0.0'
        # Read version number from pyproject.toml:
        with open(os.path.join('pyproject.toml')) as f:
            for line in f:
                if 'version' in line:
                    version = line.split('=')[1].strip().strip('"')
                    break

    rvpkg_staging = os.path.join(tempfile.mkdtemp(), 'rvpkg')

    # Copy plugin files
    copytree(source_path, rvpkg_staging)

    # Strip off patch version from the tool: M.m rather than M.m.p
    plugin_name = 'ftrack-{0}'.format(version)

    plugin_destination_path = output_path

    if not os.path.exists(plugin_destination_path):
        os.makedirs(plugin_destination_path)

    if not os.path.exists(os.path.join(rvpkg_staging, 'PACKAGE')):
        raise IOError('no PACKAGE.yml file in {0}'.format(rvpkg_staging))

    package_file_path = os.path.join(rvpkg_staging, 'PACKAGE')
    package_file = fileinput.input(package_file_path, inplace=True)
    for line in package_file:
        if '{VERSION}' in line:
            sys.stdout.write(line.format(VERSION=version))
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


if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    logging.info('ftrack RV package build script v{}'.format(__version__))

    # Make sure we run from the RV root folder
    if not os.path.exists('pyproject.toml'):
        raise Exception(
            'This script must be run from the root folder of the RV plugin!'
        )

    parser.add_argument('--version', help='(Optional)The version to use.')

    parser.add_argument('source_path', help=('The RV plugin source folder\n'))

    parser.add_argument(
        'destination_path', help=('The plugin destination folder\n')
    )

    args = parser.parse_args()

    if args.source_path is None:
        raise Exception('No source path given!')

    if args.destination_path is None:
        raise Exception('No destination path given!')

    build_rvpkg(args.source_path, args.destination_path, args.version)
