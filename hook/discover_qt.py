# :coding: utf-8
# :copyright: Copyright (c) 2016 ftrack

import os
import ftrack_api
import ftrack_connect.application

import logging

logger = logging.getLogger('ftrack_connect_pipeline_qt.discover')

plugin_base_dir = os.path.normpath(
    os.path.join(
        os.path.abspath(
            os.path.dirname(__file__)
        ),
        '..'
    )
)


python_dependencies = os.path.join(
    plugin_base_dir, 'dependencies'
)


def on_discover_pipeline(event):
    '''Handle application launch and add environment to *event*.'''

    # Add pipeline dependencies to pythonpath.
    ftrack_connect.application.prependPath(
        python_dependencies,
        'PYTHONPATH',
        event['data']['options']['env']
    )

    # Discover plugins from definitions
    definitions_plugin_hook = event['data']['options']['env'].get(
        'FTRACK_DEFINITION_PLUGIN_PATH'
    )
    plugin_hook = os.path.join(definitions_plugin_hook, 'qt')
    # Add plugins to events path.
    ftrack_connect.application.appendPath(
        plugin_hook,
        'FTRACK_EVENT_PLUGIN_PATH',
        event['data']['options']['env']
    )


def register(session):
    '''Subscribe to application launch events on *registry*.'''
    if not isinstance(session, ftrack_api.session.Session):
        return

    logger.info('discovering :{}'.format('ftrack.pipeline.discover'))
    session.event_hub.subscribe(
        'topic=ftrack.connect.application.launch',
        on_discover_pipeline, priority=30
    )
