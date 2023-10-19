# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

import os
import logging
import qtawesome as qta
import darkdetect

# Evaluate version
try:
    from ftrack_connect.util import get_version

    __version__ = get_version(
        os.path.basename(os.path.dirname(__file__)),
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    )
except Exception:
    __version__ = '0.0.0'


logger = logging.getLogger(__name__)

_resource = {"loaded": False}


def load_icons(font_folder):
    font_folder = os.path.abspath(font_folder)
    logger.info(
        f'loading ftrack icon fonts from {font_folder} : resource already loaded {_resource["loaded"]}'
    )
    if not _resource['loaded']:
        qta.load_font(
            'ftrack',
            'ftrack-icon.ttf',
            'ftrack-icon-charmap.json',
            directory=font_folder,
        )
        _resource['loaded'] = True
