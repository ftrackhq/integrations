# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

import logging
import os
import traceback
from functools import partial
import platform

import nuke, nukescripts

import ftrack_api

from ftrack_constants import framework as constants
from ftrack_utils.extensions.environment import (
    get_extensions_path_from_environment,
)
from ftrack_framework_core.host import Host
from ftrack_framework_core.event import EventManager
from ftrack_framework_core.client import Client
from ftrack_framework_core import registry

from ftrack_framework_core.configure_logging import configure_logging

from ftrack_utils.usage import set_usage_tracker, UsageTracker

from ftrack_framework_nuke.utils import (
    dock_nuke_right,
    find_nodegraph_viewer,
    run_in_main_thread,
)

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
    'ftrack_framework_nuke',
    extra_modules=['ftrack_qt'],
    propagate=False,
)

logger = logging.getLogger(__name__)
logger.debug(f'v{__version__}')


def get_ftrack_menu(menu_name='ftrack', submenu_name=None):
    '''Get the current ftrack menu, create it if does not exists.'''

    nuke_menu = nuke.menu("Nuke")
    ftrack_menu = nuke_menu.findItem(menu_name)
    if not ftrack_menu:
        ftrack_menu = nuke_menu.addMenu(menu_name)
    if submenu_name:
        ftrack_sub_menu = ftrack_menu.findItem(submenu_name)
        if not ftrack_sub_menu:
            ftrack_sub_menu = ftrack_menu.addMenu(submenu_name)

        return ftrack_sub_menu
    else:
        return ftrack_menu


client_instance = None


@run_in_main_thread
def on_run_tool_callback(tool_name, dialog_name=None, options=dict):
    client_instance.run_tool(
        tool_name,
        dialog_name,
        options,
        dock_func=partial(dock_nuke_right) if dialog_name else None,
    )
    # Prevent bug in Nuke were curve editor is activated on docking a panel
    if options.get("docked"):
        find_nodegraph_viewer(activate=True)


def bootstrap_integration(framework_extensions_path):
    global client_instance

    logger.debug(
        'Nuke integration initialising, extensions path:'
        f' {framework_extensions_path}'
    )

    session = ftrack_api.Session(auto_connect_event_hub=False)

    event_manager = EventManager(
        session=session, mode=constants.event.LOCAL_EVENT_MODE
    )

    registry_instance = registry.Registry()
    registry_instance.scan_extensions(paths=framework_extensions_path)

    # TODO: clean up this dictionary creation or move it as a query function of
    #  the registry.
    # Create a registry dictionary with all extension names to pass to the mix panel event
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
                app="Nuke",
                registry=registry_info_dict,
                version=__version__,
                app_version=nuke.NUKE_VERSION_STRING,
                os=platform.platform(),
            ),
        )
    )

    Host(event_manager, registry=registry_instance)

    client_instance = Client(event_manager, registry=registry_instance)

    # Init tools
    dcc_config = registry_instance.get_one(
        name='framework-nuke', extension_type='dcc_config'
    )['extension']

    logger.debug(f'Read DCC config: {dcc_config}')

    globals()['onRunToolCallback'] = on_run_tool_callback

    ftrack_menu = get_ftrack_menu(submenu_name=None)

    for tool in dcc_config['tools']:
        execute_on = tool.get("execute_on", "menu")
        name = tool['name']
        dialog_name = tool.get('dialog_name')
        options = tool.get('options')
        if execute_on == "menu":
            if tool['name'] == 'separator':
                ftrack_menu.addSeparator()
            else:
                ftrack_menu.addCommand(
                    tool['label'],
                    f'{__name__}.onRunToolCallback("{name}","{dialog_name}", {options})',
                )
        elif execute_on == "startup":
            # Execute startup tool-configs
            on_run_tool_callback(
                name,
                dialog_name,
                options,
            )
        else:
            logger.error(
                f"Unsuported execute on: {execute_on} tool section of the "
                f"tool {tool.get('name')} on the tool config file: "
                f"{dcc_config['name']}. \n Currently supported values:"
                f" [startup, menu]"
            )


# Find and read DCC config
try:
    bootstrap_integration(get_extensions_path_from_environment())
except:
    # Make sure any exception that happens are logged as there is most likely no console
    logger.error(traceback.format_exc())
    raise
