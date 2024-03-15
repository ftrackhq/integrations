# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack
import os
import logging
import re
import qtawesome as qta

logger = logging.getLogger(__name__)

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

if (
    __version__ == "0.0.0"
    and 'FTRACK_CONNECT_INSTALLER_RESOURCE_PATH' in os.environ
):
    # If the version is still 0.0.0, we are probably running as executable from within
    # the installer. In this case, we can use the version stored by the installer.
    FTRACK_CONNECT_INSTALLER_RESOURCE_PATH = os.environ.get(
        'FTRACK_CONNECT_INSTALLER_RESOURCE_PATH',
        os.path.abspath(os.path.join(os.path.dirname(__file__), '..')),
    )

    with open(
        os.path.join(
            FTRACK_CONNECT_INSTALLER_RESOURCE_PATH,
            'ftrack_connect_version.py',
        )
    ) as _version_file:
        __version__ = re.match(
            r'.*__version__ = \'(.*?)\'', _version_file.read(), re.DOTALL
        ).group(1)


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
INTEGRATIONS_REPO = 'https://api.github.com/repos/ftrackhq/integrations'


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
