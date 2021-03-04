# :coding: utf-8
# :copyright: Copyright (c) 2016 ftrack

import logging
import os
import sys
import imp

import ftrack_api
from functools import partial

logger = logging.getLogger('ftrack_connect_pipeline_3dsmax.listen_3dsmax_launch')

def on_application_launch(session, event):

    plugin_base_dir = os.path.normpath(
        os.path.join(
            os.path.abspath(
                os.path.dirname(__file__)
            ),
            '..'
        )
    )

    max_script_path = os.path.abspath(os.path.join(
        plugin_base_dir, 'resource', 'scripts'
    ))

    max_connect_plugins_path = os.path.abspath(os.path.join(
        plugin_base_dir, 'resource', 'plug_ins'
    ))

    max_startup_folder = os.path.abspath(os.path.join(max_script_path, 'startup'))
    max_startup_script = os.path.join(max_startup_folder, 'initftrack.ms')
    python_dependencies = os.path.abspath(os.path.join(
        plugin_base_dir, 'dependencies'
    ))
    sys.path.append(python_dependencies)

    # logger.debug('Adding ftrackShotId')
    entity = event['data']['context']['selection'][0]
    task = session.get('Context', entity['entityId'])

    # Discover plugins from definitions
    definitions_plugin_hook = os.getenv("FTRACK_DEFINITION_PLUGIN_PATH")
    plugin_hook = os.path.join(definitions_plugin_hook, '3dsmax')

    # This is not needed, but we make sure to remove PySide to not override
    # the one in 3dmax.
    modules_to_remove = ['PySide', 'PySide2']
    paths_to_remove = ''
    for m in modules_to_remove:
        try:
            module_path = imp.find_module(m)[1]
            paths_to_remove = module_path
        except ImportError:
            pass


    data = {
        'integration': {
            "name": 'ftrack-connect-pipeline-3dsmax',
            'version': '0.0.0',
            'env': {
                '3DSMAX_PLUG_IN_PATH.set': max_connect_plugins_path,
                'FTRACK_EVENT_PLUGIN_PATH.prepend': plugin_hook,
                'PYTHONPATH.prepend': os.path.pathsep.join([
                    python_dependencies,
                    max_startup_script
                ]),
                'PATH.remove': os.path.pathsep.join([paths_to_remove]),
                'VIRTUAL_ENV.unset': '',
                'FTRACK_CONTEXTID.set': task['id'],
                'FS.set': task['parent']['custom_attributes'].get('fstart', '1.0'),
                'FE.set': task['parent']['custom_attributes'].get('fend', '100.0')
            },
            'launch_arguments':['-U', 'MAXScript', max_startup_script]
        }
    }


    return data

def register(session):
    '''Subscribe to application launch events on *registry*.'''
    if not isinstance(session, ftrack_api.session.Session):
        return

    handle_event = partial(on_application_launch, session)

    session.event_hub.subscribe(
        'topic=ftrack.connect.application.launch'
        ' and data.application.identifier=3ds-max*'
        ' and data.application.version >= 2020',
        handle_event, priority=40
    )
    session.event_hub.subscribe(
        'topic=ftrack.connect.application.discover'
        ' and data.application.identifier=3ds-max*'
        ' and data.application.version >= 2020',
        handle_event, priority=40
    )
