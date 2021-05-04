# :coding: utf-8
# :copyright: Copyright (c) 2014-2021 ftrack

import functools
import sys
import os
import logging

import ftrack_api

NAME = 'ftrack-connect-pipeline-houdini'
VERSION = '0.1.0'

logger = logging.getLogger('{}.hook'.format(NAME.replace('-','_')))


def on_application_launch(session, event):
    '''Handle application launch and add environment to *event*.'''
    logger.info('launching: {}'.format(NAME))

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
    houdini_path_append = os.path.pathsep.join([houdini_path, '&']) if \
        os.environ.get('HOUDINI_PATH','').find('&') == -1 else houdini_path

    python_dependencies = os.path.join(
        plugin_base_dir, 'dependencies'
    )

    sys.path.append(python_dependencies)

    entity = event['data']['context']['selection'][0]
    task = session.get('Context', entity['entityId'])

    definitions_plugin_hook = os.getenv('FTRACK_DEFINITION_PLUGIN_PATH')
    plugin_hook = os.path.join(definitions_plugin_hook, 'houdini')

    data = {
        'integration': {
            'name': NAME,
            'version': VERSION,
            'env': {
                'FTRACK_EVENT_PLUGIN_PATH.prepend': plugin_hook,
                'PYTHONPATH.prepend': python_dependencies,
                'HOUDINI_PATH.append': houdini_path_append,
                'FTRACK_CONTEXTID.set': task['id'],
                'FS.set': task['parent']['custom_attributes'].get(
                    'fstart', '1.0'),
                'FE.set': task['parent']['custom_attributes'].get(
                    'fend', '100.0')
            }
        }
    }
    return data


def register(session):
    '''Subscribe to application launch events on *registry*.'''
    if not isinstance(session, ftrack_api.session.Session):
        return

    logger.info('registering :{}'.format(NAME))
    handle_launch_event = functools.partial(
        on_application_launch,
        session
    )
    session.event_hub.subscribe(
        'topic=ftrack.connect.application.discover'
        ' and data.application.identifier=houdini*',
        handle_launch_event, priority=40
    )

    session.event_hub.subscribe(
        'topic=ftrack.connect.application.launch'
        ' and data.application.identifier=houdini*',
        handle_launch_event, priority=40
    )
