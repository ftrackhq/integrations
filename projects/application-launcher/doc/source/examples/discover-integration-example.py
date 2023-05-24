# :coding: utf-8
# :copyright: Copyright (c) 2016 ftrack

import os
import sys
import ftrack_api
import logging
from functools import partial


logger = logging.getLogger('example_integration.discover')


def on_application_launch(session, event):
    '''Handle application launch and add environment to *event*.'''

    # gather local paths
    plugin_base_dir = os.path.normpath(
        os.path.join(os.path.abspath(os.path.dirname(__file__)), '..')
    )

    hook_path = os.path.join(plugin_base_dir, 'resource', 'hook')

    # Add dependencies to PATH.
    python_dependencies = os.path.join(plugin_base_dir, 'dependencies')
    sys.path.append(python_dependencies)

    # Get the context is running from.
    entity = event['data']['context']['selection'][0]
    task = session.get('Context', entity['entityId'])

    data = {
        'integration': {
            "name": 'ftrack-example-integration',
            'version': '0.0.0',
            'env': {
                'FTRACK_EVENT_PLUGIN_PATH.prepend': hook_path,
                'PYTHONPATH.prepend': os.path.pathsep.join(
                    [python_dependencies]
                ),
                'FTRACK_CONTEXTID.set': task['id'],
                'FS.set': task['parent']['custom_attributes'].get(
                    'fstart', '1.0'
                ),
                'FE.set': task['parent']['custom_attributes'].get(
                    'fend', '100.0'
                ),
            },
        }
    }

    # Return the composed data for this integration.
    return data


def register(session):
    '''Subscribe to application launch events on *registry*.'''
    if not isinstance(session, ftrack_api.session.Session):
        return

    handle_event = partial(on_application_launch, session)

    # Filter the application launch and discovery, based on the application
    # identifier and the version extracted.
    session.event_hub.subscribe(
        'topic=ftrack.connect.application.launch and '
        'data.application.identifier=an_application*'
        ' and data.application.version >= 2021',
        handle_event,
        priority=40,
    )
    session.event_hub.subscribe(
        'topic=ftrack.connect.application.discover and '
        'data.application.identifier=an_application*'
        ' and data.application.version >= 2021',
        handle_event,
        priority=40,
    )
