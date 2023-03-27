# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

import os
import uuid
import sys
import ftrack_api
import logging
import functools
import traceback

logger = logging.getLogger('ftrack_connect_pipeline_harmony.discover')

plugin_base_dir = os.path.normpath(
    os.path.join(os.path.abspath(os.path.dirname(__file__)), '..')
)
python_dependencies = os.path.join(plugin_base_dir, 'dependencies')
sys.path.append(python_dependencies)

def on_discover_pipeline_harmony(session, event):
    try:
        logger.warning("ftrack_connect_pipeline_harmony")

        from ftrack_connect_pipeline_harmony import __version__ as integration_version

        data = {
            'integration': {
                "name": 'ftrack-connect-pipeline-harmony',
                'version': integration_version,
            }
        }

        return data
    except:
        logger.error(traceback.format_exc())

def on_launch_pipeline_harmony(session, event):
    '''Handle application launch and add environment to *event*.'''

    try:
        pipeline_harmony_base_data = on_discover_pipeline_harmony(session, event)

        harmony_plugins_path = os.path.join(
            plugin_base_dir, 'resource', 'plugins', 'python'
        )

        #harmony_bootstrap_path = os.path.join(
        #    plugin_base_dir, 'resource', 'bootstrap'
        #)

       #harmony_bootstrap_plugin_path = os.path.join(harmony_bootstrap_path, 'plugins')

        harmony_definitions_path = os.path.join(
            plugin_base_dir, 'resource', 'definitions'
        )

        # TODO: Use the Connect Python here, in standalone mode
        #standalone_python_interpreter_path = '/Users/henriknorin/Documents/ftrack/dev/venv/mac_osx_darwin_18_7_0_py3.7_poetry/bin/python'
        standalone_python_interpreter_path = '/Users/henriknorin/Documents/ftrack/dev/venv/mac_osx_darwin_18_7_0_py3.7.12_latest-qt/bin/ftrack-connect'


        pipeline_harmony_base_data['integration']['env'] = {
            'FTRACK_EVENT_PLUGIN_PATH.prepend': os.path.pathsep.join(
                [harmony_plugins_path, harmony_definitions_path]
            ),
            'FTRACK_DEFINITION_PATH.prepend': harmony_definitions_path,
            'PYTHONPATH.prepend': os.path.pathsep.join(
                [python_dependencies] #, harmony_bootstrap_path]
            ),
            'FTRACK_PYTHON_INTERPRETER.prepend': standalone_python_interpreter_path,
            'FTRACK_INTEGRATION_SESSION_ID': str(uuid.uuid4())
        }

        selection = event['data'].get('context', {}).get('selection', [])

        if selection:
            task = session.get('Context', selection[0]['entityId'])
            pipeline_harmony_base_data['integration']['env'][
                'FTRACK_CONTEXTID.set'
            ] = task['id']
            parent = session.query(
                'select custom_attributes from Context where id={}'.format(
                    task['parent']['id']
                )
            ).first()  # Make sure updated custom attributes are fetched
            pipeline_harmony_base_data['integration']['env']['FS.set'] = parent[
                'custom_attributes'
            ].get('fstart', '1.0')
            pipeline_harmony_base_data['integration']['env']['FE.set'] = parent[
                'custom_attributes'
            ].get('fend', '100.0')
            pipeline_harmony_base_data['integration']['env']['FPS.set'] = parent[
                'custom_attributes'
            ].get('fps', '24.0')

    except:
        logger.error(traceback.format_exc())
        raise
    return pipeline_harmony_base_data

def register(session):
    '''Subscribe to application launch events on *registry*.'''
    if not isinstance(session, ftrack_api.session.Session):
        return

    logger.warning("Registering harmony")

    handle_discovery_event = functools.partial(
        on_discover_pipeline_harmony, session
    )

    session.event_hub.subscribe(
        'topic=ftrack.connect.application.discover and '
        'data.application.identifier=toonboom-harmony-*',
        handle_discovery_event,
        priority=40,
    )

    handle_launch_event = functools.partial(on_launch_pipeline_harmony, session)

    session.event_hub.subscribe(
        'topic=ftrack.connect.application.launch and '
        'data.application.identifier=toonboom-harmony-*',
        handle_launch_event,
        priority=40,
    )
