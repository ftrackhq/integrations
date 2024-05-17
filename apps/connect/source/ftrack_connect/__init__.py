# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

import os
import logging
import qtawesome as qta
import re
import sys

logger = logging.getLogger(__name__)

# Create stderr, set to None on Windows. Required for BaseHTTPRequestHandler to be able to log.
if sys.stderr is None:
    sys.stderr = open(os.devnull, 'w')

# Evaluate version and log package version
try:
    from ftrack_utils.version import get_version

    __version__ = get_version(
        os.path.basename(os.path.dirname(__file__)),
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    )
except Exception:
    import traceback

    logging.warning(traceback.format_exc())
    __version__ = "0.0.0"

if __version__ == "0.0.0":
    # If the version is still 0.0.0, we are probably running as executable from within
    # the installer. In this case, we can use the version stored by the installer.

    if getattr(sys, 'frozen', False):
        # If the application is run as a bundle, the pyInstaller bootloader
        # extends the sys module by a flag frozen=True and sets the app
        # path into variable _MEIPASS.
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath(".")

    version_file_path = os.path.join(
        base_path, 'ftrack_connect', '__version__.py'
    )

    try:
        with open(version_file_path, 'r') as _version_file:
            version_content = _version_file.read()
            version_match = re.match(
                r".*__version__ = '(.*?)'", version_content, re.DOTALL
            )
            if version_match:
                __version__ = version_match.group(1)
            else:
                __version__ = "0.0.0"
                logging.warning("Version string not found in __version__.py")

    except Exception as e:
        logging.warning(f"Error reading version file: {e}")
        __version__ = "0.0.0"


_resource = {"loaded": False}

# Legacy plugins that is incompatible with Connect and needs to be re-installed
# if they not are on the new plugin format, will not be loaded.
# Please maintain the version formatting ><=....
INCOMPATIBLE_PLUGINS = [
    {'name': 'ftrack-connect-publisher-widget', 'version': '<24'},
    {'name': 'ftrack-connect-timetracker-widget', 'version': '<24'},
    {'name': 'ftrack-connect-action-launcher-widget', 'version': '>0'},
    {'name': 'ftrack-connect-plugin-manager', 'version': '>0'},
]

# Legacy plugins that still works but are deprecated, will be loaded.
DEPRECATED_PLUGINS = [
    {'name': 'ftrack-application-launcher', 'version': '>0'},
    {'name': 'ftrack-connect-pipeline', 'version': '>0'},
    {'name': 'ftrack-connect-pipeline-qt', 'version': '>0'},
    {'name': 'ftrack-connect-pipeline-maya', 'version': '>0'},
    {'name': 'ftrack-connect-pipeline-nuke', 'version': '>0'},
    {'name': 'ftrack-connect-pipeline-houdini', 'version': '>0'},
    {'name': 'ftrack-connect-pipeline-3dsmax', 'version': '>0'},
    {'name': 'ftrack-connect-pipeline-unreal', 'version': '>0'},
    {'name': 'ftrack-connect-nuke-studio', 'version': '>0'},
    {'name': 'ftrack-connect-rv', 'version': '>0'},
    {'name': 'ftrack-connect-cinema-4d', 'version': '>0'},
]

# ftrack integrations repo URL from were to discover and download plugins
DEFAULT_INTEGRATIONS_REPO_URL = (
    'https://api.github.com/repos/ftrackhq/integrations'
)


def load_icons(font_folder):
    font_folder = os.path.abspath(font_folder)
    if not _resource['loaded']:
        logger.info(f'loading ftrack icon fonts from {font_folder}')
        qta.load_font(
            'ftrack',
            'ftrack-icon.ttf',
            'ftrack-icon-charmap.json',
            directory=font_folder,
        )
        _resource['loaded'] = True


def load_fonts_resource():
    '''Load fonts from the resource folder'''
    icon_fonts_path = None
    if getattr(sys, 'frozen', False):
        # If the application is run as a bundle, the pyInstaller bootloader
        # extends the sys module by a flag frozen=True and sets the app
        # path into variable _MEIPASS.
        icon_fonts_path = os.path.join(sys._MEIPASS, "ftrack_connect", "fonts")
    else:
        # Get the directory of the current script
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # Path to the fonts folder
        icon_fonts_path = os.path.join(current_dir, 'fonts')

    load_icons(icon_fonts_path)


def set_up_certificates():
    '''When runing from the installer setup the certificates to avoid problems with SSL certificates.'''
    if getattr(sys, 'frozen', False):
        # If the application is run as a bundle, the pyInstaller bootloader
        # extends the sys module by a flag frozen=True and sets the app
        # path into variable _MEIPASS.
        connect_cert_dir = os.path.join(
            sys._MEIPASS, "ftrack_connect", "certs"
        )

        # Set the path to certificate file in resource folder. This allows requests
        # module to read it outside frozen zip file.
        os.environ.setdefault(
            'REQUESTS_CA_BUNDLE',
            os.path.abspath(os.path.join(connect_cert_dir, 'cacert.pem')),
        )

        # Websocket-client ships with its own cacert file, we however default
        # to the one shipped with the requests library.
        os.environ.setdefault(
            'WEBSOCKET_CLIENT_CA_BUNDLE', os.environ.get('REQUESTS_CA_BUNDLE')
        )

        # The httplib in python +2.7.9 requires a cacert file.
        os.environ.setdefault(
            'SSL_CERT_FILE', os.environ.get('REQUESTS_CA_BUNDLE')
        )


set_up_certificates()
