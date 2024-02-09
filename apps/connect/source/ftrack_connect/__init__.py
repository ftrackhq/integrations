# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

import os
import logging
import qtawesome as qta

# Evaluate version and log package version
try:
    from ftrack_utils.version import get_version

    __version__ = get_version(
        os.path.basename(os.path.dirname(__file__)),
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    )
except Exception:
    import traceback

    print(traceback.format_exc())
    __version__ = "0.0.0"


logger = logging.getLogger(__name__)

_resource = {"loaded": False}


# Legacy plugins that can't be bootstrapped by Connect, will not be loaded.
CONFLICTING_PLUGINS = [
    'ftrack-connect-action-launcher-widget',
    'ftrack-connect-plugin-manager',
]

# Legacy plugins that is incompatible with Connect and needs to be re-installed
# if they not are on the new plugin format, will not be loaded.
# Please maintain the version formatting ><=....
INCOMPATIBLE_PLUGINS = [
    {'name': 'ftrack-connect-publisher-widget', 'version': '<24'},
    {'name': 'ftrack-connect-timetracker-widget', 'version': '<24'},
]

# Legacy plugins that still works but are deprecated, will be loaded.
DEPRECATED_PLUGINS = [
    'ftrack-application-launcher',
    'ftrack-connect-pipeline',
    'ftrack-connect-nuke-studio',
    'ftrack-connect-rv',
    'ftrack-connect-cinema-4d',
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
