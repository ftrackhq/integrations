# :coding: utf-8
# :copyright: Copyright (c) 2020 ftrack

import functools
import sys
import os
import logging

import ftrack_api

logger = logging.getLogger('ftrack_connect_pipeline_houdini.discover')

def on_application_launch(session, event):

    plugin_base_dir = os.path.normpath(
        os.path.join(
            os.path.abspath(
                os.path.dirname(__file__)
            ),
            '..'
        )
    )

    houdini_path = os.path.join(
        plugin_base_dir, 'resource', 'houdini_path'
    )

    python_dependencies = os.path.join(
        plugin_base_dir, 'dependencies'
    )

    sys.path.append(python_dependencies)

    from ftrack_connect_pipeline_houdini import _version as integration_version

    entity = event['data']['context']['selection'][0]
    task = session.get('Context', entity['entityId'])

    definitions_plugin_hook = os.getenv("FTRACK_DEFINITION_PLUGIN_PATH")
    plugin_hook = os.path.join(definitions_plugin_hook, 'houdini')

    data = {
        'integration': {
            "name": 'ftrack-connect-pipeline-houdini',
            'version': integration_version,
            'env': {
                'FTRACK_EVENT_PLUGIN_PATH.prepend': plugin_hook,
                'PYTHONPATH.prepend': python_dependencies,
                'HOUDINI_PATH.prepend': os.path.pathsep.join([houdini_path, '&']),
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

    logger.info('discovering :{}'.format('ftrack.pipeline-houdini.discover'))
    handle_event = functools.partial(
        on_application_launch,
        session
    )
    session.event_hub.subscribe(
        'topic=ftrack.connect.application.launch'
        ' and data.application.identifier=houdini*',
        handle_event, priority=40
    )
