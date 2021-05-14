# :coding: utf-8
# :copyright: Copyright (c) 2021 ftrack

import functools
import sys
import os

import ftrack_api


def on_discover_rv_integration(session, event):
    cwd = os.path.dirname(__file__)
    sources = os.path.abspath(os.path.join(cwd, '..', 'dependencies'))
    sys.path.append(sources)

    from ftrack_connect_rv import __version__ as integration_version

    data = {
        'integration': {
            'name': 'ftrack-connect-rv',
            'version': integration_version,
            'env': {
                'PYTHONPATH.prepend': sources,
                'RV_PYTHON3.prepend': "1"
            }
        }
    }
    return data


def register(session):
    '''Subscribe to application launch events on *registry*.'''
    if not isinstance(session, ftrack_api.session.Session):
        return

    handle_event = functools.partial(
        on_discover_rv_integration,
        session
    )
    session.event_hub.subscribe(
        'topic=ftrack.connect.application.launch'
        ' and data.application.identifier=rv*'
        ' and data.application.version >= 2021',
        handle_event,
        priority=20
    )

    session.event_hub.subscribe(
        'topic=ftrack.connect.application.discover'
        ' and data.application.identifier=rv*'
        ' and data.application.version >= 2021',
        handle_event,
        priority=20
    )
