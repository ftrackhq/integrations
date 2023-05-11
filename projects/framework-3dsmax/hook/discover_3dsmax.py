# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

import logging
import os
import sys
import importlib

import ftrack_api
import functools

logger = logging.getLogger('ftrack_connect_pipeline_3dsmax.discover')


plugin_base_dir = os.path.normpath(
    os.path.join(os.path.abspath(os.path.dirname(__file__)), '..')
)

python_dependencies = os.path.abspath(
    os.path.join(plugin_base_dir, 'dependencies')
)
sys.path.append(python_dependencies)


def on_discover_pipeline_3dsmax(session, event):

    from ftrack_connect_pipeline_3dsmax import (
        __version__ as integration_version,
    )

    data = {
        'integration': {
            "name": 'ftrack-connect-pipeline-3dsmax',
            'version': integration_version,
        }
    }
    return data


def on_launch_3dsmax_pipeline(session, event):
    pipeline_max_base_data = on_discover_pipeline_3dsmax(session, event)

    max_bootstrap_path = os.path.abspath(
        os.path.join(plugin_base_dir, 'resource', 'bootstrap')
    )
    max_plugins_path = os.path.abspath(
        os.path.join(plugin_base_dir, 'resource', 'plugins', 'python')
    )

    max_definitions_path = os.path.join(
        plugin_base_dir, 'resource', 'definitions'
    )

    max_bootstrap_plugin_path = os.path.join(max_bootstrap_path, 'plugins')

    max_startup_script = os.path.join(max_bootstrap_path, 'initftrack.ms')

    pipeline_max_base_data['integration']['env'] = {
        '3DSMAX_PLUG_IN_PATH.set': max_bootstrap_plugin_path,
        'FTRACK_EVENT_PLUGIN_PATH.prepend': os.path.pathsep.join(
            [max_plugins_path, max_definitions_path]
        ),
        'FTRACK_DEFINITION_PATH.prepend': max_definitions_path,
        'PYTHONPATH.prepend': os.path.pathsep.join(
            [python_dependencies, max_startup_script]
        ),
    }
    pipeline_max_base_data['integration']['launch_arguments'] = [
        '-U',
        'MAXScript',
        max_startup_script,
    ]

    selection = event['data'].get('context', {}).get('selection', [])

    if selection:
        task = session.get('Context', selection[0]['entityId'])
        pipeline_max_base_data['integration']['env'][
            'FTRACK_CONTEXTID.set'
        ] = task['id']
        parent = session.query(
            'select custom_attributes from Context where id={}'.format(
                task['parent']['id']
            )
        ).first()  # Make sure updated custom attributes are fetched
        pipeline_max_base_data['integration']['env']['FS.set'] = parent[
            'custom_attributes'
        ].get('fstart', '1.0')
        pipeline_max_base_data['integration']['env']['FE.set'] = parent[
            'custom_attributes'
        ].get('fend', '100.0')
        pipeline_max_base_data['integration']['env']['FPS.set'] = parent[
            'custom_attributes'
        ].get('fps', '24.0')

    return pipeline_max_base_data


def register(session):
    '''Subscribe to application launch events on *registry*.'''
    if not isinstance(session, ftrack_api.session.Session):
        return

    handle_discovery_event = functools.partial(
        on_discover_pipeline_3dsmax, session
    )
    session.event_hub.subscribe(
        'topic=ftrack.connect.application.discover'
        ' and data.application.identifier=3ds-max*'
        ' and data.application.version >= 2021',
        handle_discovery_event,
        priority=40,
    )

    handle_launch_event = functools.partial(on_launch_3dsmax_pipeline, session)
    session.event_hub.subscribe(
        'topic=ftrack.connect.application.launch'
        ' and data.application.identifier=3ds-max*'
        ' and data.application.version >= 2021',
        handle_launch_event,
        priority=40,
    )
