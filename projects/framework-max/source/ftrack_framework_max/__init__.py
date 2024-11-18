# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack
import functools
import logging
import os
import traceback
import platform

from pymxs import runtime as rt

import ftrack_api

from ftrack_framework_core.host import Host
from ftrack_framework_core.event import EventManager
from ftrack_framework_core.client import Client
from ftrack_framework_core.registry import Registry
from ftrack_framework_core.configure_logging import configure_logging

from ftrack_constants import framework as constants

from ftrack_utils.extensions.environment import (
    get_extensions_path_from_environment,
)

from ftrack_utils.usage import set_usage_tracker, UsageTracker

from ftrack_framework_max.utils import run_in_main_thread

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
    'ftrack_framework_max',
    extra_modules=['ftrack_qt'],
    propagate=False,
)

logger = logging.getLogger(__name__)
logger.debug('v{}'.format(__version__))


@run_in_main_thread
def on_run_tool_callback(
    client_instance, tool_name, dialog_name=None, options=None
):
    client_instance.run_tool(tool_name, dialog_name, options, dock_func=None)


def bootstrap_integration(framework_extensions_path):
    '''
    Initialise Max Framework integration
    '''
    logger.debug(
        'Max standalone integration initialising, extensions path:'
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
                app="3ds Max",
                registry=registry_info_dict,
                version=__version__,
                app_version=rt.maxVersion()[7],
                os=platform.platform(),
            ),
        )
    )

    # Instantiate Host and Client
    Host(event_manager, registry=registry_instance)
    client_instance = Client(event_manager, registry=registry_instance)

    # Init tools
    dcc_config = registry_instance.get_one(
        name='framework-max', extension_type='dcc_config'
    )['extension']

    logger.debug(f'Read DCC config: {dcc_config}')

    tools_on_menu = [
        tool for tool in dcc_config['tools'] if tool.get('menu', True)
    ]
    startup_tools = [
        tool for tool in dcc_config['tools'] if tool.get('run_on') == 'startup'
    ]

    for tool in startup_tools:
        on_run_tool_callback(
            client_instance,
            tool.get('name'),
            tool.get('dialog_name'),
            tool['options'],
        )

    # Register tools into ftrack menu and run startup tools directly
    # https://help.autodesk.com/view/MAXDEV/2025/ENU/?guid=MAXDEV_Python_using_pymxs_pymxs_macroscripts_menus_html
    for tool in tools_on_menu:
        normalized_tool_name = f"ftrack{tool['name'].lower().replace(' ', '')}"

        rt.macros.new(
            "ftrack",  # Category for the macro script
            normalized_tool_name,  # Name of the macro script
            tool["label"],  # Tooltip text for the action
            tool["label"],  # Text displayed in the menu
            f"{normalized_tool_name}()",  # Function to execute when this action is triggered
        )

        # Our plugin specific function that gets called when the user clicks the menu item
        def callback():
            return functools.partial(
                on_run_tool_callback,
                client_instance,
                tool.get("name"),
                tool.get("dialog_name"),
                tool.get("options"),
            )

        # Expose this function to the maxscript global namespace
        rt.execute(f'{normalized_tool_name} = ""')
        rt.globalVars.set(normalized_tool_name, callback())

    def menucallback():
        import uuid

        """Register the a menu an its items.
        This callback is registered on the "cuiRegistermenus" event of 3dsMax and
        is typically called in he startup of 3dsMax.
        """
        menumgr = rt.callbacks.notificationparam()
        mainmenubar = menumgr.mainmenubar

        # Create a new submenu at the end of the 3dsMax main menu bar
        # To place the menu at a specific position, use the 'beforeID' parameter with the GUID of the suceeding menu item
        # Note, that every menu item in the menu system needs a persistent Guid for identification and referencing
        submenu = mainmenubar.createsubmenu(str(uuid.uuid4()), "ftrack")

        for tool in tools_on_menu:
            normalized_tool_name = (
                f"ftrack{tool['name'].lower().replace(' ', '')}"
            )
            # Add the first macroscript action to the submenu
            macroscriptTableid = 647394
            submenu.createaction(
                str(uuid.uuid4()),
                macroscriptTableid,
                f"{normalized_tool_name}`ftrack",
            )  # Note the action identifier created from the macroscripts name and category

    # Make sure menucallback is called on cuiRegisterMenus events
    # so that it can register menus at the appropriate moment
    MENU_ID = rt.name("ftrack")
    rt.callbacks.removescripts(id=MENU_ID)
    rt.callbacks.addscript(
        rt.name("cuiRegisterMenus"), menucallback, id=MENU_ID
    )

    return client_instance


# Find and read DCC config
try:
    bootstrap_integration(get_extensions_path_from_environment())
except:
    # Make sure any exception that happens are logged as there is most likely no console
    logger.error(traceback.format_exc())
    raise
