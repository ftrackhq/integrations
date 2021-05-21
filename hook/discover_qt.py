# :coding: utf-8
# :copyright: Copyright (c) 2016 ftrack

import os
import sys
import ftrack_api

import logging

NAME = 'ftrack-connect-pipeline-qt'
VERSION = '0.1.0'

logger = logging.getLogger('{}.hook'.format(NAME.replace('-','_')))


def on_application_launch(event):
    '''Handle application launch and add environment to *event*.'''
    logger.debug('launching: {}'.format(NAME))

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
    sys.path.append(python_dependencies)


    # discover version
    # from ftrack_connect_pipeline_qt import _version as integration_version

    definitions_plugin_hook = os.getenv("FTRACK_DEFINITION_PLUGIN_PATH")

    plugin_hook = os.path.join(definitions_plugin_hook, 'qt')

    data = {
        'integration': {
            'name':'ftrack-connect-pipeline-qt',
            'version': '0.0.0',
            'env':{
                'PYTHONPATH.prepend': python_dependencies,
                'FTRACK_EVENT_PLUGIN_PATH.prepend': plugin_hook
            }
        }
    }
    return data


def register(session):
    '''Subscribe to application launch events on *registry*.'''
    if not isinstance(session, ftrack_api.session.Session):
        return

    logger.debug('registering: {}'.format(NAME))
    session.event_hub.subscribe(
        'topic=ftrack.connect.application.discover '
        'and data.application.identifier=*',
        on_application_launch, priority=30
    )
    session.event_hub.subscribe(
        'topic=ftrack.connect.application.launch '
        'and data.application.identifier=*',
        on_application_launch, priority=30
    )
