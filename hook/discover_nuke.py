# :coding: utf-8
# :copyright: Copyright (c) 2016 ftrack

import os
import sys
import ftrack_api
import logging
from functools import partial

logger = logging.getLogger('ftrack_connect_pipeline_nuke.listen_nuke_launch')


def on_application_launch(session, event):

    plugin_base_dir = os.path.normpath(
        os.path.join(
            os.path.abspath(
                os.path.dirname(__file__)
            ),
            '..'
        )
    )

    nuke_script_path = os.path.join(
        plugin_base_dir, 'resource', 'scripts'
    )

    python_dependencies = os.path.join(

        plugin_base_dir, 'dependencies'

    )

    sys.path.append(python_dependencies)

    entity = event['data']['context']['selection'][0]

    task = session.get('Context', entity['entityId'])

    # Discover plugins from definitions

    definitions_plugin_hook = os.getenv("FTRACK_DEFINITION_PLUGIN_PATH")

    plugin_hook = os.path.join(definitions_plugin_hook, 'nuke')

    # from ftrack_connect_pipeline_maya import _version as integration_version


    data = {
        'integration': {
            "name": 'ftrack-connect-pipeline-nuke',
            'version': '0.0.0',
            'env': {
                'FTRACK_EVENT_PLUGIN_PATH.prepend': plugin_hook,
                'PYTHONPATH.prepend': os.path.pathsep.join([python_dependencies, nuke_script_path]),
                'NUKE_PATH': nuke_script_path,
                'FTRACK_CONTEXTID.set': task['id'],
                'FS.set': task['parent']['custom_attributes'].get('fstart', '1.0'),
                'FE.set': task['parent']['custom_attributes'].get('fend', '100.0')
            }
        }
    }

    return data


def register(session):
    '''Subscribe to application launch events on *registry*.'''
    if not isinstance(session, ftrack_api.session.Session):
        return

    handle_event = partial(on_application_launch, session)

    session.event_hub.subscribe(
        'topic=ftrack.connect.application.launch and '
        'data.application.identifier=nuke*'
        ' and data.application.version >= 13.0',
        handle_event, priority=40

    )
    session.event_hub.subscribe(
        'topic=ftrack.connect.application.discover'
        ' and data.application.identifier=nuke*'
        ' and data.application.version >= 13.0',
        handle_event, priority=40
    )