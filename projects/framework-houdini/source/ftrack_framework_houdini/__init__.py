# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

import logging
import os
import xml.etree.ElementTree as ET
from xml.sax.saxutils import unescape
import platform

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

from ftrack_framework_houdini.utils import (
    dock_houdini_right,
    run_in_main_thread,
)

import hou


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
    'ftrack_framework_houdini',
    extra_modules=['ftrack_qt'],
    propagate=False,
)

logger = logging.getLogger(__name__)
logger.debug('v{}'.format(__version__))

client_instance = None


@run_in_main_thread
def on_run_tool_callback(tool_name, dialog_name=None, options=None):
    client_instance.run_tool(
        tool_name,
        dialog_name,
        options,
        dock_func=dock_houdini_right if dialog_name else None,
    )


def get_ftrack_menu():
    '''Construct the xml representation of the ftrack menu.'''
    root = ET.Element("mainMenu")
    menubar = ET.SubElement(root, "menuBar")
    ftrack_menu = ET.SubElement(menubar, "subMenu")
    label = ET.SubElement(ftrack_menu, "label")
    label.text = "ftrack"
    insert_before = ET.SubElement(ftrack_menu, "insertBefore")
    insert_before.text = "help_menu"
    return (root, ftrack_menu)


def bootstrap_integration(framework_extensions_path):
    '''
    Initialise Houdini Framework integration
    '''
    logger.debug(
        'Houdini standalone integration initialising, extensions path:'
        f' {framework_extensions_path}'
    )

    global client_instance

    # Create ftrack session and instantiate event manager
    session = ftrack_api.Session(auto_connect_event_hub=True)
    event_manager = EventManager(session=session)
    logger.debug(f"framework_extensions_path:{framework_extensions_path}")
    # Instantiate registry
    registry_instance = Registry()
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
                app="Houdini",
                registry=registry_info_dict,
                version=__version__,
                app_version=hou.applicationVersionString(),
                os=platform.platform(),
            ),
        )
    )

    # Instantiate Host and Client
    Host(
        event_manager,
        registry=registry_instance,
        run_in_main_thread_wrapper=run_in_main_thread,
    )
    client_instance = Client(
        event_manager,
        registry=registry_instance,
        run_in_main_thread_wrapper=run_in_main_thread,
    )

    # Init tools
    dcc_config = registry_instance.get_one(
        name='framework-houdini', extension_type='dcc_config'
    )['extension']

    logger.debug(f'Read DCC config: {dcc_config}')

    # Generate ftrack menu
    root, ftrack_menu = get_ftrack_menu()

    # Register tools into ftrack menu
    for tool in dcc_config['tools']:
        run_on = tool.get("run_on")
        on_menu = tool.get("menu", True)
        if on_menu:
            menu_item = ET.SubElement(ftrack_menu, "scriptItem")
            menu_item.set("id", tool['name'])
            label = ET.SubElement(menu_item, "label")
            label.text = tool['label']
            menu_item_script = ET.SubElement(menu_item, "scriptCode")
            menu_item_script.text = _get_menu_item_script(tool)
        if run_on:
            if run_on == "startup":
                # Execute startup tool-configs
                on_run_tool_callback(
                    tool.get('name'),
                    tool.get('dialog_name'),
                    tool['options'],
                )
            else:
                logger.error(
                    f"Unsupported run_on value: {run_on} tool section of the "
                    f"tool {tool.get('name')} on the tool config file: "
                    f"{dcc_config['name']}. \n Currently supported values:"
                    f" [startup]"
                )

    # Convert xml to string
    # Unescaping and decoding to avoid ending up with encoded CDATA
    xml = unescape(ET.tostring(root).decode())

    # Find the temp file where to write xml for MainMenuCommon.xml
    xml_menu_file_folder = os.environ['FTRACK_HOUDINI_XML_MENU_FILE']

    # Write xml to file
    xml_path = os.path.join(xml_menu_file_folder, "MainMenuCommon.xml")
    with open(xml_path, "w") as xml_file_handle:
        xml_file_handle.write(xml)
        xml_file_handle.close()

    return client_instance


def _get_menu_item_script(tool):
    '''Return script for ftrack menu item'''
    return f"""
<![CDATA[
import functools
import hdefereval
import ftrack_framework_houdini
callable = functools.partial(
    ftrack_framework_houdini.on_run_tool_callback,
    "{tool['name']}",
    "{tool['dialog_name']}",
    {tool['options']}
)
hdefereval.executeDeferred(callable)
]]>
"""


# Find and read DCC config
try:
    bootstrap_integration(get_extensions_path_from_environment())
except Exception as error:
    # Make sure any exception that happens are logged as there is most likely no console
    logger.exception(error)
    raise
