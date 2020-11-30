# :coding: utf-8
# :copyright: Copyright (c) 2016 ftrack

import logging
import os
import sys

import ftrack_api
from functools import partial

logger = logging.getLogger('ftrack_connect_pipeline_3dsmax.listen_3dsmax_launch')

def on_application_launch(session, event):

    plugin_base_dir = os.path.normpath(
        os.path.join(
            os.path.abspath(
                os.path.dirname(__file__)
            ),
            '..'
        )
    )

    max_script_path = os.path.abspath(os.path.join(
        plugin_base_dir, 'resource', 'scripts'
    ))

    max_connect_plugins_path = os.path.abspath(os.path.join(
        plugin_base_dir, 'resource', 'plug_ins'
    ))

    max_startup_folder = os.path.abspath(os.path.join(max_script_path, 'startup'))
    max_startup_script = os.path.join(max_startup_folder, 'initftrack.ms')
    python_dependencies = os.path.abspath(os.path.join(
        plugin_base_dir, 'dependencies'
    ))
    sys.path.append(python_dependencies)

    # logger.debug('Adding ftrackShotId')
    entity = event['data']['context']['selection'][0]
    task = session.get('Context', entity['entityId'])

    # Discover plugins from definitions
    definitions_plugin_hook = os.getenv("FTRACK_DEFINITION_PLUGIN_PATH")
    plugin_hook = os.path.join(definitions_plugin_hook, '3dsmax')


    data = {
        'integration': {
            "name": 'ftrack-connect-pipeline-3dsmax',
            'version': '0.0.0',
            'env': {
                '3DSMAX_PLUG_IN_PATH.set': max_connect_plugins_path,
                'FTRACK_EVENT_PLUGIN_PATH.prepend': plugin_hook,
                'PYTHONPATH.prepend': python_dependencies,
                'FTRACK_CONTEXTID.set': task['id'],
                'FS.set': task['parent']['custom_attributes'].get('fstart', '1.0'),
                'FE.set': task['parent']['custom_attributes'].get('fend', '100.0')
            },
            'launch_arguments':['-U', 'MAXScript', max_startup_script]
        }
    }


    return data

def register(session):
    '''Subscribe to application launch events on *registry*.'''
    if not isinstance(session, ftrack_api.session.Session):
        return

    handle_event = partial(on_application_launch, session)

    session.event_hub.subscribe(
        'topic=ftrack.connect.application.launch'
        ' and data.application.identifier=3ds-max*',
        handle_event, priority=40
    )
