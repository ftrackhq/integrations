# :coding: utf-8
# :copyright: Copyright (c) 2016 ftrack

import os
import sys
import ftrack_api
import logging
import functools

NAME = 'ftrack-connect-pipeline'
VERSION = '0.1.0'

logger = logging.getLogger('{}.hook'.format(NAME.replace('-', '_')))


plugin_base_dir = os.path.normpath(
    os.path.join(os.path.abspath(os.path.dirname(__file__)), '..')
)

python_dependencies = os.path.join(plugin_base_dir, 'dependencies')
sys.path.append(python_dependencies)


def on_discover_pipeline(session, event):

    from ftrack_connect_pipeline import __version__ as integration_version

    data = {
        'integration': {
            'name': 'ftrack-connect-pipeline',
            'version': integration_version,
        }
    }

    return data


def on_launch_pipeline(session, event):
    '''Handle application launch and add environment to *event*.'''

    pipeline_base_data = on_discover_pipeline(session, event)

    pipeline_plugins_path = os.path.join(
        plugin_base_dir, 'resource', 'plugins', 'python'
    )

    pipeline_bootstrap_path = os.path.join(
        plugin_base_dir, 'resource', 'bootstrap'
    )

    pipeline_bootstrap_plugin_path = os.path.join(
        pipeline_bootstrap_path, 'plugins'
    )

    core_definitions_path = os.path.join(
        plugin_base_dir, 'resource', 'definitions'
    )

    pipeline_base_data['integration']['env'] = {
        'PYTHONPATH.prepend': python_dependencies,
        'FTRACK_EVENT_PLUGIN_PATH.prepend': os.path.pathsep.join(
            [pipeline_plugins_path, core_definitions_path]
        ),
        'FTRACK_DEFINITION_PATH.prepend': core_definitions_path,
    }

    return pipeline_base_data


def register(session):
    '''Subscribe to application launch events on *registry*.'''
    if not isinstance(session, ftrack_api.session.Session):
        return

    handle_discovery_event = functools.partial(on_discover_pipeline, session)

    session.event_hub.subscribe(
        'topic=ftrack.connect.application.discover '
        'and data.application.identifier=*',
        handle_discovery_event,
        priority=20,
    )

    handle_launch_event = functools.partial(on_launch_pipeline, session)

    session.event_hub.subscribe(
        'topic=ftrack.connect.application.launch '
        'and data.application.identifier=*',
        handle_launch_event,
        priority=20,
    )
