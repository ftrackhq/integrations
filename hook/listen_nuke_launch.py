# :coding: utf-8
# :copyright: Copyright (c) 2016 ftrack

import os
import ftrack_api
import ftrack_connect.application
import logging
from functools import partial

logger = logging.getLogger('ftrack_connect_pipeline_nuke.listen_nuke_launch')

plugin_base_dir = os.path.normpath(
    os.path.join(
        os.path.abspath(
            os.path.dirname(__file__)
        ),
        '..'
    )
)

nuke_connect_plugins_path = os.path.join(
    plugin_base_dir, 'resource', 'plug_ins'
)

nuke_script_path = os.path.join(
    plugin_base_dir, 'resource', 'scripts'
)

python_dependencies = os.path.join(
    plugin_base_dir, 'dependencies'
)


def on_application_launch(session, event):
    '''Handle application launch and add environment to *event*.'''

    logger.debug('Adding nuke pipeline environments.')

    # logger.debug('Adding ftrackShotId')
    entity = event['data']['context']['selection'][0]
    task = session.get('Task', entity['entityId'])
    taskParent = task['parent']

    try:
        event['data']['options']['env']['FS'] = str(
            taskParent['custom_attributes'].get('fstart', '1')
        )
    except Exception:
        event['data']['options']['env']['FS'] = '1'

    try:
        event['data']['options']['env']['FE'] = str(
            taskParent['custom_attributes'].get('fend', '1')
        )
    except Exception:
        event['data']['options']['env']['FE'] = '1'

    event['data']['options']['env']['FTRACK_CONTEXTID'] = task['id']

    # Add dependencies in pythonpath
    ftrack_connect.application.appendPath(
        python_dependencies,
        'PYTHONPATH',
        event['data']['options']['env']
    )

    # nuke scripts
    ftrack_connect.application.appendPath(
        nuke_script_path,
        'PYTHONPATH',
        event['data']['options']['env']
    )

    ftrack_connect.application.appendPath(
        nuke_script_path,
        'NUKE_PATH',
        event['data']['options']['env']
    )

    definitions_plugin_hook = event['data']['options']['env'].get(
        'FTRACK_DEFINITION_PLUGIN_PATH'
    )
    plugin_hook = os.path.join(definitions_plugin_hook, 'nuke')
    # Add base plugins to events path.
    ftrack_connect.application.appendPath(
        plugin_hook,
        'FTRACK_EVENT_PLUGIN_PATH',
        event['data']['options']['env']
    )

    return event['data']['options']


def register(session):
    '''Subscribe to application launch events on *registry*.'''
    if not isinstance(session, ftrack_api.session.Session):
        return

    handle_event = partial(on_application_launch, session)

    session.event_hub.subscribe(
        'topic=ftrack.connect.application.launch and '
        'data.application.identifier=nuke*',
        handle_event, priority=40
    )
