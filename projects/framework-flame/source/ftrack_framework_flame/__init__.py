# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack
import functools
import logging
import os
import platform

import ftrack_api

from ftrack_constants import framework as constants
from ftrack_framework_core.client import Client
from ftrack_framework_core.configure_logging import configure_logging
from ftrack_framework_core.event import EventManager
from ftrack_framework_core.host import Host
from ftrack_framework_core.registry import Registry
from ftrack_utils.extensions.environment import (
    get_extensions_path_from_environment,
)
from ftrack_utils.usage import UsageTracker, set_usage_tracker

# Evaluate version and log package version
try:
    from ftrack_utils.version import get_version

    __version__ = get_version(
        os.path.basename(os.path.dirname(__file__)),
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    )
except Exception:
    __version__ = '0.0.0'

configure_logging(
    'ftrack_framework_flame',
    extra_modules=['ftrack_qt'],
    propagate=False,
)

logger = logging.getLogger(__name__)
logger.debug('v{}'.format(__version__))


# @run_in_main_thread
def on_run_tool_callback(
        client_instance, tool_name, dialog_name=None, options=dict, extra_args=None
):
    client_instance.run_tool(
        tool_name,
        dialog_name,
        options
    )


def bootstrap_integration(framework_extensions_path):
    '''
    Initialise Flame Framework integration
    '''
    logger.debug(
        'Flame standalone integration initialising, extensions path:'
        f' {framework_extensions_path}'
    )
    # Create ftrack session and instantiate event manager
    session = ftrack_api.Session(auto_connect_event_hub=False)
    event_manager = EventManager(
        session=session, mode=constants.event.LOCAL_EVENT_MODE
    )
    logger.debug(f"framework_extensions_path:{framework_extensions_path}")
    # Instantiate registry
    registry_instance = Registry()
    registry_instance.scan_extensions(paths=framework_extensions_path)

    registry_info_dict = {
        'tool_configs': [
            item['name'] for item in registry_instance.tool_configs
        ]
        if registry_instance.tool_configs
        else [],
        'plugins': [item['name'] for item in registry_instance.plugins]
        if registry_instance.plugins
        else [],
        'engines': [item['name'] for item in registry_instance.engines]
        if registry_instance.engines
        else [],
        'widgets': [item['name'] for item in registry_instance.widgets]
        if registry_instance.widgets
        else [],
        'dialogs': [item['name'] for item in registry_instance.dialogs]
        if registry_instance.dialogs
        else [],
        'launch_configs': [
            item['name'] for item in registry_instance.launch_configs
        ]
        if registry_instance.launch_configs
        else [],
        'dcc_configs': [item['name'] for item in registry_instance.dcc_configs]
        if registry_instance.dcc_configs
        else [],
    }

    # Set mix panel event
    set_usage_tracker(
        UsageTracker(
            session=session,
            default_data=dict(
                app="Flame",
                registry=registry_info_dict,
                version=__version__,
                app_version="2023",  # TODO: fetch DCC version through API
                os=platform.platform(),
            ),
        )
    )

    # Instantiate Host and Client
    Host(event_manager, registry=registry_instance)
    client_instance = Client(event_manager, registry=registry_instance)

    return client_instance, registry_instance


def scope_node(show_on, selection):
    for item in selection:
        if isinstance(item, show_on):
            return True

    return False


def get_ftrack_menu(show_on=None):
    show_on = show_on or ()
    client_instance, registry_instance = bootstrap_integration(get_extensions_path_from_environment())

    dcc_config = registry_instance.get_one(
        name='framework-flame', extension_type='dcc_config'
    )['extension']

    logger.debug(f'Read DCC config: {dcc_config}')

    # Create ftrack menu
    actions = []
    # Register tools into ftrack menu
    for tool in dcc_config['tools']:
        run_on = tool.get("run_on")
        on_menu = tool.get("menu", True)
        if on_menu:
            new_action = {
                'name': tool['label'],
                'execute': functools.partial(
                    on_run_tool_callback,
                    client_instance,
                    tool.get('name'),
                    tool.get('dialog_name'),
                    tool['options']
                ),
                'minimumVersion': '2023',
                'isVisible': functools.partial(
                    scope_node, show_on
                ),
            }
            actions.append(new_action)

        if run_on:
            if run_on == "startup":
                # Execute startup tool-configs
                on_run_tool_callback(
                    client_instance,
                    tool.get('name'),
                    tool.get('dialog_name'),
                    tool['options']
                )
            else:
                logger.error(
                    f"Unsupported run_on value: {run_on} tool section of the "
                    f"tool {tool.get('name')} on the tool config file: "
                    f"{dcc_config['name']}. \n Currently supported values:"
                    f" [startup]"
                )

    return [
        {
            "name": "ftrack",
            "actions": actions
        }
    ]
