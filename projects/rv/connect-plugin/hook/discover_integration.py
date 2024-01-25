# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

import functools
import os
import logging

import ftrack_api
from ftrack_connect.util import get_connect_plugin_version

logger = logging.getLogger(__name__)

cwd = os.path.dirname(__file__)
connect_plugin_path = os.path.abspath(os.path.join(cwd, '..'))

# Read version number from __version__.py
__version__ = get_connect_plugin_version(connect_plugin_path)

sources = os.path.abspath(os.path.join(connect_plugin_path, 'dependencies'))


def on_discover_rv_integration(session, event):
    data = {'integration': {'name': 'ftrack-rv', 'version': __version__}}
    return data


def on_launch_rv_integration(session, event):
    rv_data = on_discover_rv_integration(session, event)
    rv_data['integration']['env'] = {
        'PYTHONPATH.prepend': sources,
        'RV_PYTHON3.prepend': "1",
    }

    return rv_data


def get_version_information(event):
    '''Return version information for ftrack connect installer.'''
    return [dict(name='ftrack-rv', version=__version__)]


def register(session):
    '''Subscribe to application launch events on *registry*.'''
    if not isinstance(session, ftrack_api.session.Session):
        return

    handle_discovery_event = functools.partial(
        on_discover_rv_integration, session
    )

    session.event_hub.subscribe(
        'topic=ftrack.connect.application.discover'
        ' and data.application.identifier=rv*'
        ' and data.application.version >= 2021',
        handle_discovery_event,
        priority=20,
    )

    handle_launch_event = functools.partial(on_launch_rv_integration, session)

    session.event_hub.subscribe(
        'topic=ftrack.connect.application.launch'
        ' and data.application.identifier=rv*'
        ' and data.application.version >= 2021',
        handle_launch_event,
        priority=20,
    )

    # Enable RV info in Connect about dialog
    session.event_hub.subscribe(
        'topic=ftrack.connect.plugin.debug-information',
        get_version_information,
        priority=20,
    )
