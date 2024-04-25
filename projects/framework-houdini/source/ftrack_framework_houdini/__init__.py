# :coding: utf-8
# :copyright: Copyright (c) 2014-2024 ftrack

import logging
import os
import traceback
import xml.etree.ElementTree as ET
from xml.sax.saxutils import unescape
import six

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

from ftrack_framework_houdini.utils import dock_houdini_right, run_in_main_thread


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

@run_in_main_thread
def on_run_dialog_callback(
    dialog_name, tool_config_names, docked
):
    client_instance.run_dialog(
        dialog_name,
        dialog_options={
            'tool_config_names': tool_config_names,
            'docked': docked
        },
        dock_func=dock_houdini_right,
    )


def get_ftrack_menu():
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
    session = ftrack_api.Session(auto_connect_event_hub=False)
    event_manager = EventManager(
        session=session, mode=constants.event.LOCAL_EVENT_MODE
    )
    logger.debug(f"framework_extensions_path:{framework_extensions_path}")
    # Instantiate registry
    registry_instance = Registry()
    registry_instance.scan_extensions(paths=framework_extensions_path)

    # Instantiate Host and Client
    Host(event_manager, registry=registry_instance)
    client_instance = Client(event_manager, registry=registry_instance)

    # Init tools
    dcc_config = registry_instance.get_one(
        name='framework-houdini', extension_type='dcc_config'
    )['extension']

    logger.debug(f'Read DCC config: {dcc_config}')

    # Generate ftrack menu
    root, ftrack_menu = get_ftrack_menu()

    for tool in dcc_config['tools']:
        menu_item = ET.SubElement(ftrack_menu, "scriptItem")
        menu_item.set("id", tool['name'])
        label = ET.SubElement(menu_item, "label")
        label.text = tool['label']
        menu_item_script = ET.SubElement(menu_item, "scriptCode")
        menu_item_script.text = f"""
<![CDATA[
import functools
import hdefereval
import ftrack_framework_houdini
callable = functools.partial(
    ftrack_framework_houdini.on_run_dialog_callback,
    "{tool['dialog_name']}",
    {tool['options']['tool_configs']},
    {tool['options']['docked']}
)
hdefereval.executeDeferred(callable)
]]>
"""

    # Convert xml to string
    # Unescaping and decoding to avoid ending up with encoded CDATA
    xml = six.ensure_str(unescape(ET.tostring(root).decode()))

    # Find the bootstrap folder where to save MainMenuCommon.xml
    dirname = os.path.dirname(__file__)
    framework_path = os.path.abspath(os.path.join(dirname, "..", ".."))
    bootstrap_path = os.path.join(framework_path, "resource", "bootstrap")

    # Write xml to file
    xml_path = os.path.join(bootstrap_path, "MainMenuCommon.xml")
    if not os.path.exists(xml_path):
        with open(xml_path, "w") as xml_file_handle:
            xml_file_handle.write(xml)
            xml_file_handle.close()

    return client_instance


# Find and read DCC config
try:
    bootstrap_integration(get_extensions_path_from_environment())
except:
    # Make sure any exception that happens are logged as there is most likely no console
    logger.error(traceback.format_exc())
    raise
