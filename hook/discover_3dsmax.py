# :coding: utf-8
# :copyright: Copyright (c) 2016 ftrack

import logging
import os
import sys
import imp

import ftrack_api
import functools

logger = logging.getLogger('ftrack_connect_pipeline_3dsmax.listen_3dsmax_launch')


plugin_base_dir = os.path.normpath(
    os.path.join(
        os.path.abspath(
            os.path.dirname(__file__)
        ),
        '..'
    )
)

python_dependencies = os.path.abspath(os.path.join(
    plugin_base_dir, 'dependencies'
))

sys.path.append(python_dependencies)



def on_discover_3dsmax_pipeline(session, event):

    from ftrack_connect_pipeline_3dsmax import __version__ as integration_version

    data = {
        'integration': {
            "name": 'ftrack-connect-pipeline-3dsmax',
            'version': integration_version

        }
    }
    return data


def on_launch_3dsmax_pipeline(session, event):
    pipeline_max_base_data = on_discover_3dsmax_pipeline(session, event)

    max_script_path = os.path.abspath(os.path.join(plugin_base_dir, 'resource', 'scripts'))
    max_connect_plugins_path = os.path.abspath(os.path.join(plugin_base_dir, 'resource', 'plug_ins'))
    max_startup_folder = os.path.abspath(os.path.join(max_script_path, 'startup'))
    max_startup_script = os.path.join(max_startup_folder, 'initftrack.ms')

    # Discover plugins from definitions
    definitions_plugin_hook = os.getenv("FTRACK_DEFINITION_PLUGIN_PATH")
    plugin_hook = os.path.join(definitions_plugin_hook, '3dsmax', 'python')

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


    pipeline_max_base_data['integration']['env']  = {
        '3DSMAX_PLUG_IN_PATH.set': max_connect_plugins_path,
        'FTRACK_EVENT_PLUGIN_PATH.prepend': plugin_hook,
        'PYTHONPATH.prepend': os.path.pathsep.join([python_dependencies,max_startup_script]),
        'PATH.remove': os.path.pathsep.join([paths_to_remove])
    }
    pipeline_max_base_data['integration']['launch_arguments'] = ['-U', 'MAXScript', max_startup_script]

    selection = event['data'].get('context', {}).get('selection', [])

    if selection:
        task = session.get('Context', selection[0]['entityId'])
        pipeline_max_base_data['integration']['env']['FTRACK_CONTEXTID.set'] =  task['id']
        pipeline_max_base_data['integration']['env']['FS.set'] = task['parent']['custom_attributes'].get('fstart', '1.0')
        pipeline_max_base_data['integration']['env']['FE.set'] = task['parent']['custom_attributes'].get('fend', '100.0')
        pipeline_max_base_data['integration']['env']['FPS.set'] = task['parent']['custom_attributes'].get('fps', '24.0')
        
    return pipeline_max_base_data


def register(session):
    '''Subscribe to application launch events on *registry*.'''
    if not isinstance(session, ftrack_api.session.Session):
        return

    handle_discovery_event = functools.partial(
        on_discover_3dsmax_pipeline,
        session
    )
    session.event_hub.subscribe(
        'topic=ftrack.connect.application.discover'
        ' and data.application.identifier=3ds-max*'
        ' and data.application.version >= 2020',
        handle_discovery_event, priority=40
    )

    handle_launch_event = functools.partial(
        on_launch_3dsmax_pipeline,
        session
    )  
    session.event_hub.subscribe(
        'topic=ftrack.connect.application.launch'
        ' and data.application.identifier=3ds-max*'
        ' and data.application.version >= 2020',
        handle_launch_event, priority=40
    )

