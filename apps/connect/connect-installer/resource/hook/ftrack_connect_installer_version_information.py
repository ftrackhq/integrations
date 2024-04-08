# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

import logging
import os
import re

import ftrack_api

# Expect the Connect installer version to be written to a file by the installer
version_path = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '_version.py'
)
with open(os.path.join(version_path)) as _version_file:
    VERSION = re.match(
        r'.*__version__ = \'(.*?)\'', _version_file.read(), re.DOTALL
    ).group(1)


def get_version_information(event):
    '''Return version information for ftrack connect installer.'''
    return [dict(name='Installer', version=VERSION, core=True)]


def register(api_object, **kw):
    '''Register version information hook.'''

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
