# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

import os
import sys
import logging
import argparse

from ftrack_utils.version import get_version
from ftrack_app_installer import (
    WindowsAppInstaller,
    MacOSAppInstaller,
    LinuxAppInstaller,
)


def setup_installer(bundle_name, version, root_path, entry_file):
    '''Return the instance of the installer class depending on the current platform'''
    if sys.platform.startswith('win'):
        return WindowsAppInstaller(
            bundle_name,
            version,
            os.path.join(root_path, "logo.ico"),
            root_path,
            entry_file,
        )
    elif sys.platform.startswith('darwin'):
        return MacOSAppInstaller(
            bundle_name,
            version,
            os.path.join(root_path, "logo.icns"),
            root_path,
            entry_file,
        )
    elif sys.platform.startswith('linux'):
        return LinuxAppInstaller(
            bundle_name,
            version,
            os.path.join(root_path, "logo.svg"),
            root_path,
            entry_file,
        )
    else:
        logging.error("Unsupported platform")
        return None


def main():
    arguments = sys.argv[1:]

    if sys.platform == "darwin" and getattr(sys, 'frozen', False):
        # Filter out PSN (process serial number) argument passed by OSX.
        arguments = [
            argument for argument in arguments if '-psn_0_' not in argument
        ]

    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--codesign',
        help='Codesign the application (default: True).',
        default=True,
        nargs='?',
        type=lambda x: (str(x).lower() in ['true', '1', 'yes']),
    )

    args = parser.parse_args(arguments)

    bundle_name = "ftrack Connect"
    version = get_version("ftrack_connect", os.path.dirname(__file__))
    root_path = os.path.dirname(os.path.abspath(__file__))
    entry_file = os.path.join(root_path, "source/ftrack_connect/__main__.py")

    installer = setup_installer(bundle_name, version, root_path, entry_file)

    if installer:
        installer.generate_executable()
        installer.generate_installer_package(codesign=args.codesign)
    else:
        logging.error("Failed to setup installer - Exiting.")
        sys.exit(1)


if __name__ == "__main__":
    main()
