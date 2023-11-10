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


def load_icons(font_folder):
    font_folder = os.path.abspath(font_folder)
    if not _resource["loaded"]:
        logger.info(f'loading ftrack icon fonts from {font_folder}')
    if not _resource['loaded']:
        qta.load_font(
            'ftrack',
            'ftrack-icon.ttf',
            'ftrack-icon-charmap.json',
            directory=font_folder,
        )
        _resource['loaded'] = True
