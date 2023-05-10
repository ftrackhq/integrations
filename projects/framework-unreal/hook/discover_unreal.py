# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

import os
import sys
import ftrack_api
import logging
import functools
import shutil

logger = logging.getLogger('ftrack_connect_pipeline_unreal.discover')

plugin_base_dir = os.path.normpath(
    os.path.join(os.path.abspath(os.path.dirname(__file__)), '..')
)
python_dependencies = os.path.join(plugin_base_dir, 'dependencies')
sys.path.append(python_dependencies)


def on_discover_pipeline_unreal(session, event):
    from ftrack_connect_pipeline_unreal import (
        __version__ as integration_version,
    )

    data = {
        'integration': {
            "name": 'ftrack-connect-pipeline-unreal',
            'version': integration_version,
        }
    }

    return data


def on_launch_pipeline_unreal(session, event):
    '''Handle application launch and add environment to *event*.'''

    pipeline_unreal_base_data = on_discover_pipeline_unreal(session, event)

    unreal_plugins_path = os.path.join(
        plugin_base_dir, 'resource', 'plugins', 'python'
    )

    unreal_bootstrap_path = os.path.join(
        plugin_base_dir, 'resource', 'bootstrap'
    )

    unreal_bootstrap_plugin_path = os.path.join(
        unreal_bootstrap_path, 'plugins'
    )

    unreal_definitions_path = os.path.join(
        plugin_base_dir, 'resource', 'definitions'
    )

    pipeline_unreal_base_data['integration']['env'] = {
        'FTRACK_EVENT_PLUGIN_PATH.prepend': os.path.pathsep.join(
            [unreal_plugins_path, unreal_definitions_path]
        ),
        'FTRACK_DEFINITION_PATH.prepend': unreal_definitions_path,
        'PYTHONPATH.prepend': os.path.pathsep.join(
            [python_dependencies, unreal_bootstrap_path]
        ),
        'QT_PREFERRED_BINDING.set': 'PySide2',
    }

    # Verify that init script is installed centrally
    unreal_editor_exe = event['data']['application']['path']
    # 'C:\\Program Files\\Epic Games\\UE_5.1\\Engine\\Binaries\\Win64\\UnrealEditor.exe'
    engine_path = os.path.realpath(
        os.path.join(unreal_editor_exe, '..', '..', '..')
    )
    script_source = os.path.join(unreal_bootstrap_path, 'init_unreal.py')
    script_destination = os.path.join(
        engine_path, 'Content', 'Python', 'init_unreal.py'
    )
    in_sync = os.path.exists(script_destination)
    if in_sync:
        # Check size
        size_source = os.path.getsize(script_source)
        size_destination = os.path.getsize(script_destination)
        if size_destination != size_source:
            logger.warning(
                'Unreal init script size differs ({}<>{}), updating...'.format(
                    size_destination, size_source
                )
            )
            in_sync = False
        else:
            # Check modification time
            modtime_source = os.path.getmtime(script_source)
            modtime_destination = os.path.getmtime(script_destination)
            if modtime_destination != modtime_source:
                logger.warning(
                    'Unreal init script modification time differs ({}<>{}), updating...'.format(
                        modtime_destination, modtime_source
                    )
                )
                in_sync = False
    if not in_sync:
        logger.warning(
            'Attempting to install Unreal init script "{}" > "{}"'.format(
                script_source, script_destination
            )
        )
        try:
            os.makedirs(os.path.dirname(script_destination), exist_ok=True)
            shutil.copy(script_source, script_destination)
            logger.info('Installed init script.')
            # Also copy icon
            icon_source = os.path.join(unreal_bootstrap_path, 'UEFtrack.ico')
            icon_destination = os.path.join(
                engine_path, 'Content', 'Python', 'UEFtrack.ico'
            )
            shutil.copy(icon_source, icon_destination)
            logger.info('Installed Unreal icon.')
        except PermissionError as pe:
            logger.exception(pe)
            logger.error(
                'Could not install Unreal init script, make sure you have write permissions to "{}"!'.format(
                    script_destination
                )
            )
            raise
    else:
        logger.info('Unreal init script is in sync, no update required.')
    selection = event['data'].get('context', {}).get('selection', [])
    if selection:
        entity = session.get('Context', selection[0]['entityId'])
        if entity.entity_type == 'Task':
            pipeline_unreal_base_data['integration']['env'][
                'FTRACK_CONTEXTID.set'
            ] = str(entity['id'])
            pipeline_unreal_base_data['integration']['env']['FS.set'] = str(
                entity['parent']['custom_attributes'].get('fstart', '1.0')
            )
            pipeline_unreal_base_data['integration']['env']['FE.set'] = str(
                entity['parent']['custom_attributes'].get('fend', '100.0')
            )
            pipeline_unreal_base_data['integration']['env']['FPS.set'] = str(
                entity['parent']['custom_attributes'].get('fps', '24')
            )

    return pipeline_unreal_base_data


def register(session):
    '''Subscribe to application launch events on *registry*.'''
    if not isinstance(session, ftrack_api.session.Session):
        return

    handle_discovery_event = functools.partial(
        on_discover_pipeline_unreal, session
    )

    session.event_hub.subscribe(
        'topic=ftrack.connect.application.discover and '
        'data.application.identifier=unreal*'
        ' and data.application.version >= 5.00',
        handle_discovery_event,
        priority=40,
    )

    handle_launch_event = functools.partial(on_launch_pipeline_unreal, session)

    session.event_hub.subscribe(
        'topic=ftrack.connect.application.launch and '
        'data.application.identifier=unreal*'
        ' and data.application.version >= 5.00',
        handle_launch_event,
        priority=40,
    )
