# :coding: utf-8
# :copyright: Copyright (c) 2016 ftrack

import os
import ftrack_api
import ftrack_connect.application

import logging

logger = logging.getLogger('ftrack_connect_pipeline.discover')

plugin_base_dir = os.path.normpath(
    os.path.join(
        os.path.abspath(
            os.path.dirname(__file__)
        ),
        '..'
    )
)

application_hook = os.path.join(
    plugin_base_dir, 'resource', 'application_hook'
)

python_dependencies = os.path.join(
    plugin_base_dir, 'dependencies'
)


def on_discover_pipeline(event):
    '''Handle application launch and add environment to *event*.'''


    ftrack_connect.application.appendPath(
        python_dependencies,
        'PYTHONPATH',
        event['data']['options']['env']
    )

    ftrack_connect.application.appendPath(
        application_hook,
        'FTRACK_EVENT_PLUGIN_PATH',
        event['data']['options']['env']
    )

    event['data']['options']['env']['FTRACK_CONTEXT_ID'] = (
        event['data']['options']['env']['FTRACK_TASKID']
    )


def register(session):
    '''Subscribe to application launch events on *registry*.'''
    if not isinstance(session, ftrack_api.session.Session):
        return

    logger.info('discovering :{}'.format('ftrack.pipeline.discover'))
    session.event_hub.subscribe(
        'topic=ftrack.connect.application.launch',
        on_discover_pipeline
    )
