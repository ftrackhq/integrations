# :coding: utf-8
# :copyright: Copyright (c) 2016 ftrack

import os
import sys
import ftrack_api
import logging
import functools

logger = logging.getLogger('ftrack_connect_pipeline_maya.discover')

plugin_base_dir = os.path.normpath(
    os.path.join(os.path.abspath(os.path.dirname(__file__)), '..')
)
python_dependencies = os.path.join(plugin_base_dir, 'dependencies')
sys.path.append(python_dependencies)


def on_discover_pipeline_maya(session, event):
    from ftrack_connect_pipeline_maya import __version__ as integration_version

    data = {
        'integration': {
            "name": 'ftrack-connect-pipeline-maya',
            'version': integration_version,
        }
    }

    return data


def on_launch_pipeline_maya(session, event):
    '''Handle application launch and add environment to *event*.'''

    pipeline_maya_base_data = on_discover_pipeline_maya(session, event)

    maya_plugins_path = os.path.join(
        plugin_base_dir, 'resource', 'plugins', 'python'
    )

    maya_definitions_path = os.path.join(
        plugin_base_dir, 'resource', 'definitions'
    )

    maya_bootstrap_path = os.path.join(
        plugin_base_dir, 'resource', 'bootstrap'
    )

    maya_bootstrap_plugin_path = os.path.join(maya_bootstrap_path, 'plugins')

    pipeline_maya_base_data['integration']['env'] = {
        'FTRACK_EVENT_PLUGIN_PATH.prepend': os.path.pathsep.join(
            [maya_plugins_path, maya_definitions_path]
        ),
        'FTRACK_DEFINITION_PATH.prepend': maya_definitions_path,
        'PYTHONPATH.prepend': os.path.pathsep.join(
            [python_dependencies, maya_bootstrap_path]
        ),
        'MAYA_SCRIPT_PATH': maya_bootstrap_path,
        'MAYA_PLUG_IN_PATH.prepend': maya_bootstrap_plugin_path,
    }

    selection = event['data'].get('context', {}).get('selection', [])

    if selection:
        task = session.get('Context', selection[0]['entityId'])
        pipeline_maya_base_data['integration']['env'][
            'FTRACK_CONTEXTID.set'
        ] = task['id']
        parent = session.query(
            'select custom_attributes from Context where id={}'.format(
                task['parent']['id']
            )
        ).first()  # Make sure updated custom attributes are fetched
        pipeline_maya_base_data['integration']['env']['FS.set'] = parent[
            'custom_attributes'
        ].get('fstart', '1.0')
        pipeline_maya_base_data['integration']['env']['FE.set'] = parent[
            'custom_attributes'
        ].get('fend', '100.0')
        pipeline_maya_base_data['integration']['env']['FPS.set'] = parent[
            'custom_attributes'
        ].get('fps', '24.0')

    return pipeline_maya_base_data


def register(session):
    '''Subscribe to application launch events on *registry*.'''
    if not isinstance(session, ftrack_api.session.Session):
        return

    handle_discovery_event = functools.partial(
        on_discover_pipeline_maya, session
    )

    session.event_hub.subscribe(
        'topic=ftrack.connect.application.discover and '
        'data.application.identifier=maya*'
        ' and data.application.version >= 2021',
        handle_discovery_event,
        priority=40,
    )

    handle_launch_event = functools.partial(on_launch_pipeline_maya, session)

    session.event_hub.subscribe(
        'topic=ftrack.connect.application.launch and '
        'data.application.identifier=maya*'
        ' and data.application.version >= 2021',
        handle_launch_event,
        priority=40,
    )
