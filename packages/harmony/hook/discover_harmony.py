# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack
import datetime
import os
import random
import uuid
import sys
import ftrack_api
import logging
import functools
import traceback
import shutil
import re

logger = logging.getLogger('ftrack_connect_pipeline_harmony.discover')

plugin_base_dir = os.path.normpath(
    os.path.join(os.path.abspath(os.path.dirname(__file__)), '..')
)
python_dependencies = os.path.join(plugin_base_dir, 'dependencies')
sys.path.append(python_dependencies)


def on_discover_pipeline_harmony(session, event):
    logger.info("Discovering harmony")
    try:
        from ftrack_connect_pipeline_harmony import (
            __version__ as integration_version,
        )

        data = {
            'integration': {
                "name": 'ftrack-connect-pipeline-harmony',
                'version': integration_version,
            }
        }

        return data
    except:
        print(traceback.format_exc())
        raise


def deploy_scripts(app_path):
    version_nr = None
    variant = None
    for part in app_path.split(os.sep):
        if part.lower().startswith('toon boom'):
            for s in re.findall(r'\d+', part):
                version_nr = s
                variant = part.split(' ')[-1]
                break
            if variant:
                break
    logger.info(
        "Deploying scripts, variant: "
        + str(variant)
        + "version: "
        + str(version_nr)
        + ", app_path: "
        + str(app_path)
    )

    assert (
        variant
    ), "Could not determine Harmony variant from executable path: {}".format(
        app_path
    )
    assert (
        version_nr
    ), "Could not determine Harmony version from executable path: {}".format(
        app_path
    )

    path_scripts = None
    if sys.platform == "win32":
        path_scripts = os.path.expandvars("%APPDATA%")
    elif sys.platform == "linux":
        path_scripts = os.path.expandvars("$HOME")
    elif sys.platform == "darwin":
        path_scripts = os.path.expandvars("$HOME/Library/Preferences")

    if not path_scripts:
        raise Exception('Could not determine user prefs folder!')

    path_scripts = os.path.realpath(path_scripts)

    path_scripts = os.path.join(
        path_scripts,
        'Toon Boom Animation',
        'Toon Boom Harmony {}'.format(variant),
    )

    if not path_scripts:
        raise Exception('Could not determine Harmony prefs folder!')

    path_scripts = os.path.join(
        path_scripts, '{}00-scripts'.format(version_nr), 'packages'
    )

    if not os.path.exists(path_scripts):
        logger.warning('Creating: {}'.format(path_scripts))
        os.makedirs(path_scripts)

    def recursive_copy_dir(src, dst):
        logger.info('Syncing {} > {}'.format(src, dst))

        for filename in os.listdir(src):
            path_src = os.path.join(src, filename)
            path_dst = os.path.join(dst, filename)

            if os.path.isdir(path_src):
                recursive_copy_dir(path_src, path_dst)
            else:
                # Compare files
                if os.path.islink(path_src):
                    # Ignore
                    continue
                remove = False
                copy = False
                if os.path.exists(path_dst):
                    remove = True
                    # Compare date and size
                    size_source = os.path.getsize(path_src)
                    size_destination = os.path.getsize(path_dst)
                    if size_destination != size_source:
                        logger.warning('Size differs on: {}'.format(path_dst))
                        copy = True
                    else:
                        modtime_source = os.path.getmtime(path_src)
                        modtime_destination = os.path.getmtime(path_dst)
                        if modtime_destination != modtime_source:
                            logger.warning(
                                'Modification date differs on: {}'.format(
                                    path_dst
                                )
                            )
                            copy = True
                else:
                    copy = True
                if copy:
                    if remove:
                        logger.warning('Removing: {}'.format(path_dst))
                        os.remove(path_dst)
                    elif not os.path.exists(os.path.dirname(path_dst)):
                        logger.warning(
                            'Creating: {}'.format(os.path.dirname(path_dst))
                        )
                        os.makedirs(os.path.dirname(path_dst))
                    logger.warning(
                        'Copying {} > {}'.format(path_src, path_dst)
                    )
                    shutil.copy(path_src, path_dst)
                    # Set modification time
                    os.utime(
                        path_dst,
                        (
                            os.path.getmtime(path_src),
                            os.path.getmtime(path_src),
                        ),
                    )

    path_src = os.path.join(plugin_base_dir, 'resource', 'bootstrap', 'ftrack')

    recursive_copy_dir(path_src, os.path.join(path_scripts, 'ftrack'))


def on_launch_pipeline_harmony(session, event):
    '''Handle application launch and add environment to *event*.'''
    logger.info("Launching harmony")

    try:
        pipeline_harmony_base_data = on_discover_pipeline_harmony(
            session, event
        )

        harmony_plugins_path = os.path.join(
            plugin_base_dir, 'resource', 'plugins', 'harmony'
        )

        # harmony_bootstrap_path = os.path.join(
        #    plugin_base_dir, 'resource', 'bootstrap'
        # )

        # harmony_bootstrap_plugin_path = os.path.join(harmony_bootstrap_path, 'plugins')

        harmony_definitions_path = os.path.join(
            plugin_base_dir, 'resource', 'definitions'
        )

        # Use Connect as Python interpreter
        standalone_python_interpreter_path = sys.argv[0]

        # Use a random port for the integration server
        port = random.randint(50000, 65000)

        pipeline_harmony_base_data['integration']['env'] = {
            'FTRACK_EVENT_PLUGIN_PATH.prepend': os.path.pathsep.join(
                [harmony_plugins_path, harmony_definitions_path]
            ),
            'FTRACK_DEFINITION_PATH.prepend': harmony_definitions_path,
            'PYTHONPATH.prepend': os.path.pathsep.join(
                [python_dependencies]  # , harmony_bootstrap_path]
            ),
            'FTRACK_INTEGRATION_SESSION_ID': str(uuid.uuid4()),
            'FTRACK_PYTHON_INTERPRETER.prepend': standalone_python_interpreter_path,
            'FTRACK_INTEGRATION_LISTEN_PORT.set': str(port),
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
            pipeline_harmony_base_data['integration']['env'][
                'FS.set'
            ] = parent['custom_attributes'].get('fstart', '1.0')
            pipeline_harmony_base_data['integration']['env'][
                'FE.set'
            ] = parent['custom_attributes'].get('fend', '100.0')
            pipeline_harmony_base_data['integration']['env'][
                'FPS.set'
            ] = parent['custom_attributes'].get('fps', '24.0')

        # Copy bootstrap JS scripts to Harmony scripts folder
        deploy_scripts(event['data']['application']['path'])

    except:
        logger.warning(traceback.format_exc())
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
        'data.application.identifier=toonboom*',
        handle_discovery_event,
        priority=40,
    )

    handle_launch_event = functools.partial(
        on_launch_pipeline_harmony, session
    )

    session.event_hub.subscribe(
        'topic=ftrack.connect.application.launch and '
        'data.application.identifier=toonboom*',
        handle_launch_event,
        priority=40,
    )
