# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack
import logging
import os
import traceback
import functools
import platform

from PySide6 import QtWidgets

import bpy

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

from ftrack_utils.session import create_api_session
from ftrack_utils.decorators.threading import run_in_main_thread


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
    'ftrack_framework_blender',
    extra_modules=['ftrack_qt'],
    propagate=False,
)

logger = logging.getLogger(__name__)
logger.debug('v{}'.format(__version__))

app = QtWidgets.QApplication.instance()
if app is None:
    app = QtWidgets.QApplication([])

on_menu_tools = []


# Operator to execute commands
class FTRACK_OT_ExecuteCommand(bpy.types.Operator):
    bl_idname = "ftrack.execute_command"
    bl_label = "Execute Command"

    func_key: bpy.props.StringProperty()

    def execute(self, context):
        try:
            for tool in on_menu_tools:
                if tool.get("label") == self.func_key:
                    func = tool.get("command")
                    func()
        except Exception as e:
            self.report({'ERROR'}, f"Error executing command: {e}")
            return {'CANCELLED'}

        # Register a timer to process Qt events
        bpy.app.timers.register(self.process_qt_events)
        return {'FINISHED'}

    def process_qt_events(self):
        app.processEvents()
        return 0.01  # Call this function every 0.01 seconds


@run_in_main_thread
def create_ftrack_menu(tools_list):
    class FTRACK_MT_Menu(bpy.types.Menu):
        bl_label = "ftrack"
        bl_idname = "FTRACK_MT_menu"

        def draw(self, context):
            layout = self.layout
            for tool in tools_list:
                op = layout.operator(
                    "ftrack.execute_command", text=tool.get("label")
                )
                op.func_key = tool.get("label")

    return FTRACK_MT_Menu


@run_in_main_thread
# Function to add the menu to the UI
def draw_ftrack_menu(self, context):
    self.layout.menu("FTRACK_MT_menu")


@run_in_main_thread
def on_run_tool_callback(
    client_instance,
    tool_name,
    dialog_name=None,
    options=None,
    blender_args=None,
):
    client_instance.run_tool(
        tool_name,
        dialog_name,
        options,
        dock_func=None,
    )


def bootstrap_integration(framework_extensions_path):
    '''
    Initialise Blender Framework integration
    '''
    logger.debug(
        'Blender standalone integration initialising, extensions path:'
        f' {framework_extensions_path}'
    )
    # Create ftrack session and instantiate event manager
    session = create_api_session(auto_connect_event_hub=True)
    event_manager = EventManager(
        session=session, mode=constants.event.LOCAL_EVENT_MODE
    )
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
                app="Blender",
                registry=registry_info_dict,
                version=__version__,
                app_version=1,  # cmds.about(version=True),
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
        name='framework-blender', extension_type='dcc_config'
    )['extension']

    logger.debug(f'Read DCC config: {dcc_config}')

    # Create ftrack menu
    # Register tools into ftrack menu

    for tool in dcc_config['tools']:
        run_on = tool.get("run_on")
        on_menu = tool.get("menu", True)
        if on_menu:
            on_menu_tools.append(
                {
                    'label': tool['label'],
                    'command': (
                        functools.partial(
                            on_run_tool_callback,
                            client_instance,
                            tool.get('name'),
                            tool.get('dialog_name'),
                            tool['options'],
                        )
                    ),
                    'image': ":/{}.png".format(tool['icon']),
                }
            )

        if run_on:
            if run_on == "startup":
                # Execute startup tool-configs
                on_run_tool_callback(
                    client_instance,
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

    FTRACK_MT_Menu = create_ftrack_menu(on_menu_tools)

    bpy.utils.register_class(FTRACK_OT_ExecuteCommand)
    bpy.utils.register_class(FTRACK_MT_Menu)
    bpy.types.TOPBAR_MT_editor_menus.append(draw_ftrack_menu)

    return client_instance


# Find and read DCC config
try:
    bootstrap_integration(get_extensions_path_from_environment())
except:
    # Make sure any exception that happens are logged as there is most likely no console
    logger.error(traceback.format_exc())
    raise
