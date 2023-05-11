# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

import functools
import sys
import os
import logging

import ftrack_api

integration_name = 'ftrack-connect-pipeline-houdini'
logger = logging.getLogger(
    '{}.hook'.format(integration_name.replace('-', '_'))
)

plugin_base_dir = os.path.normpath(
    os.path.join(os.path.abspath(os.path.dirname(__file__)), '..')
)

python_dependencies = os.path.join(plugin_base_dir, 'dependencies')
sys.path.append(python_dependencies)

# Utility function per Os


def get_windows_options(event, data):
    app_path = event['data']['application']['path']
    app_dir = os.path.dirname(os.path.dirname(app_path))
    if not os.path.exists(os.path.join(app_dir, 'python37')):
        logger.debug(
            'Not discovering non-py3k Houdini build ("{0}").'.format(app_path)
        )
        data['integration']['disable'] = True


def get_darwin_options(event, data):
    # Check Python framework link points to a certain target
    app_path = event['data']['application']['path']  # Path to .app
    app_dir = os.path.dirname(app_path)
    link_path = os.path.realpath(
        os.path.join(app_dir, 'Frameworks/Python.framework/Versions/Current')
    )
    python_version = None
    if os.path.exists(link_path):
        python_version = os.path.basename(link_path)
    if python_version:
        if python_version.split('.')[0] != '3':
            logger.debug(
                'Not discovering non-py3k Houdini build ("{0}",'
                ' linked interpreter: {1}).'.format(app_path, python_version)
            )
            data['integration']['disable'] = True
    else:
        logger.warning(
            'Cannot detect Mac Python framework version for executable {}'.format(
                app_path
            )
        )


def get_linux_options(event, data):
    # Check if python 3.7 library exists
    app_path = event['data']['application']['path']
    bin_dir = os.path.dirname(app_path)
    base_dir = os.path.dirname(bin_dir)
    if os.path.islink(base_dir):
        # Do not resolve launcher
        data['integration']['disable'] = True
    else:
        lib_path = os.path.realpath(os.path.join(base_dir, 'python/lib'))
        if os.path.exists(lib_path):
            has_python2_interpreter = False
            for filename in os.listdir():
                if filename.startswith('python2'):
                    has_python2_interpreter = True
            if has_python2_interpreter:
                logger.debug(
                    'Not discovering non-py3k Houdini build ("{0}").'.format(
                        app_path
                    )
                )
                data['integration']['disable'] = True
        else:
            logger.warning(
                'Cannot detect linux Python framework version for executable {}'.format(
                    app_path
                )
            )


platform_options = {
    'windows': get_windows_options,
    'darwin': get_darwin_options,
    'linux': get_linux_options,
}


def on_discover_pipeline_houdini(session, event):
    from ftrack_connect_pipeline_houdini import (
        __version__ as integration_version,
    )

    data = {
        'integration': {
            'name': integration_name,
            'version': integration_version,
        }
    }

    options_function = platform_options.get(event['data']['platform'])
    options_function(event, data)

    return data


def on_launch_pipeline_houdini(session, event):
    pipeline_houdini_base_data = on_discover_pipeline_houdini(session, event)

    houdini_plugins_path = os.path.join(
        plugin_base_dir, 'resource', 'plugins', 'python'
    )

    houdini_bootstrap_path = os.path.join(
        plugin_base_dir, 'resource', 'bootstrap'
    )

    houdini_bootstrap_plugin_path = os.path.join(
        houdini_bootstrap_path, 'plugins'
    )

    current_houdini_path = os.environ.get('HOUDINI_PATH')

    houdini_path_append = (
        os.path.pathsep.join(['&', houdini_bootstrap_path])
        if current_houdini_path and not current_houdini_path.endswith('&')
        else houdini_bootstrap_path
    )

    houdini_definitions_path = os.path.join(
        plugin_base_dir, 'resource', 'definitions'
    )

    pipeline_houdini_base_data['integration']['env'] = {
        'FTRACK_EVENT_PLUGIN_PATH.prepend': os.path.pathsep.join(
            [houdini_plugins_path, houdini_definitions_path]
        ),
        'FTRACK_DEFINITION_PATH.prepend': houdini_definitions_path,
        'PYTHONPATH.prepend': python_dependencies,
        'HOUDINI_PATH.append': os.path.pathsep.join(
            [houdini_path_append, '&', houdini_bootstrap_plugin_path]
        ),
    }

    selection = event['data'].get('context', {}).get('selection', [])

    if selection:
        task = session.get('Context', selection[0]['entityId'])
        pipeline_houdini_base_data['integration']['env'][
            'FTRACK_CONTEXTID.set'
        ] = task['id']
        parent = session.query(
            'select custom_attributes from Context where id={}'.format(
                task['parent']['id']
            )
        ).first()  # Make sure updated custom attributes are fetched
        pipeline_houdini_base_data['integration']['env']['FS.set'] = parent[
            'custom_attributes'
        ].get('fstart', '1.0')
        pipeline_houdini_base_data['integration']['env']['FE.set'] = parent[
            'custom_attributes'
        ].get('fend', '100.0')
        pipeline_houdini_base_data['integration']['env']['FPS.set'] = parent[
            'custom_attributes'
        ].get('fps', '24.0')

    return pipeline_houdini_base_data


def register(session):
    '''Subscribe to application launch events on *registry*.'''
    if not isinstance(session, ftrack_api.session.Session):
        return

    handle_discovery_event = functools.partial(
        on_discover_pipeline_houdini, session
    )

    session.event_hub.subscribe(
        'topic=ftrack.connect.application.discover'
        ' and data.application.identifier=houdini*',
        handle_discovery_event,
        priority=40,
    )

    handle_launch_event = functools.partial(
        on_launch_pipeline_houdini, session
    )

    session.event_hub.subscribe(
        'topic=ftrack.connect.application.launch'
        ' and data.application.identifier=houdini*',
        handle_launch_event,
        priority=40,
    )
