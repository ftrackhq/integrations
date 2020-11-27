# :coding: utf-8
# :copyright: Copyright (c) 2016 ftrack

import os
import sys
import ftrack_api
import logging
from functools import partial


logger = logging.getLogger('ftrack_connect_pipeline_maya.discover')


def on_application_launch(session, event):
    '''Handle application launch and add environment to *event*.'''


    plugin_base_dir = os.path.normpath(
        os.path.join(
            os.path.abspath(
                os.path.dirname(__file__)
            ),
            '..'
        )
    )

    maya_plugins_path = os.path.join(
        plugin_base_dir, 'resource', 'plug_ins'
    )

    maya_script_path = os.path.join(
        plugin_base_dir, 'resource', 'scripts'
    )

    python_dependencies = os.path.join(
        plugin_base_dir, 'dependencies'
    )
    sys.path.append(python_dependencies)

    # logger.debug('Adding ftrackShotId')
    entity = event['data']['context']['selection'][0]
    task = session.get('Context', entity['entityId'])

    # # Discover plugins from definitions
    definitions_plugin_hook = event['data']['options']['env'].get(
        'FTRACK_DEFINITION_PLUGIN_PATH', 'NOTSET'
    )
    plugin_hook = os.path.join(definitions_plugin_hook, 'maya')

    from ftrack_connect_pipeline_maya import _version as integration_version

    data = {
        'integration': {
            "name": 'ftrack-connect-pipeline-maya',
            'version': integration_version.__version__,
            'env': {
                'PYTHONPATH.prepend': os.path.pathsep.join([python_dependencies, maya_script_path]),
                'MAYA_SCRIPT_PATH': maya_script_path,
                'MAYA_PLUG_IN_PATH.prepend': maya_plugins_path,
                'FTRACK_CONTEXTID.set': task['id'],
                'FTRACK_EVENT_PLUGIN_PATH.prependPath': plugin_hook,
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
        'data.application.identifier=maya*',
        handle_event, priority=40
    )
