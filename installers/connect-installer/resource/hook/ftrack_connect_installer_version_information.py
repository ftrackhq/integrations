# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

import logging
import os
import re

import ftrack_api


FTRACK_CONNECT_INSTALLER_RESOURCE_PATH = os.environ.get(
    'FTRACK_CONNECT_INSTALLER_RESOURCE_PATH',
    os.path.abspath(os.path.join(os.path.dirname(__file__), '..')),
)

VERSION = 'Unknown'
with open(
    os.path.join(
        FTRACK_CONNECT_INSTALLER_RESOURCE_PATH,
        'ftrack_connect_installer_version.py',
    )
) as _version_file:
    VERSION = re.match(
        r'.*__version__ = \'(.*?)\'', _version_file.read(), re.DOTALL
    ).group(1)


def get_version_information(event):
    '''Return version information for ftrack connect installer.'''
    return [dict(name='Package', version=VERSION, core=True)]


def register(api_object, **kw):
    '''Register version information hook.'''

    logger = logging.getLogger(
        'ftrack_connect_installer_version_information:register'
    )

    # Validate that api_object is an instance of ftrack_api.Session. If not,
    # assume that register is being called from an incompatible API
    # and return without doing anything.
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return

    api_object.event_hub.subscribe(
        'topic=ftrack.connect.plugin.debug-information',
        get_version_information,
    )
