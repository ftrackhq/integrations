# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack
import logging
import os
import traceback
import functools
import platform

import maya.cmds as cmds
import maya.mel as mm

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
from ftrack_utils.framework.config.tool import (
    get_tool_config_by_name,
    get_plugins,
)

from ftrack_framework_maya.utils import dock_maya_right, run_in_main_thread


# Evaluate version and log package version
try:
    from ftrack_utils.version import get_version

    __version__ = get_version(
        os.path.basename(os.path.dirname(__file__)),
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    )
except Exception:
    __version__ = '0.0.0'

extra_handlers = {
    'maya': {
        'class': 'maya.utils.MayaGuiLogHandler',
        'level': 'INFO',
        'formatter': 'file',
    }
}

configure_logging(
    'ftrack_framework_maya',
    extra_modules=['ftrack_qt'],
    extra_handlers=extra_handlers,
    propagate=False,
)

logger = logging.getLogger(__name__)
logger.debug('v{}'.format(__version__))


def get_ftrack_menu(menu_name='ftrack', submenu_name=None):
    '''Get the current ftrack menu, create it if does not exists.'''
    # TODO: check why isn't this working with cmds
    gMainWindow = mm.eval('$temp1=$gMainWindow')
    logger.info(f"gMainWindow: {gMainWindow}")

    if cmds.menu(menu_name, exists=True, parent=gMainWindow, label=menu_name):
        menu = menu_name

    else:
        menu = cmds.menu(
            menu_name, parent=gMainWindow, tearOff=True, label=menu_name
        )

    if submenu_name:
        if cmds.menuItem(
            submenu_name, exists=True, parent=menu, label=submenu_name
        ):
            submenu = submenu_name
        else:
            submenu = cmds.menuItem(
                submenu_name, subMenu=True, label=submenu_name, parent=menu
            )
        return submenu
    else:
        return menu


# We could use the ftrack @invoke_in_qt_main_thread utility which should act
# the same way as the DCC specific one. But using this means it ensures
# synchronization with Maya’s undo stack, event loop, and other core
# functionalities, which might not be guaranteed if you use Qt’s threading
# mechanisms directly.
@run_in_main_thread
def on_run_tool_callback(
    client_instance, dialog_name, tool_config_names, docked, maya_args
):
    if dialog_name:
        client_instance.run_dialog(
            dialog_name,
            dialog_options={
                'tool_config_names': tool_config_names,
                'docked': docked or False,
            },
            dock_func=dock_maya_right,
        )
    else:
        # TODO move this to the client run_tool_config and get it out from here and from the dialog
        for tool_config_name in tool_config_names:
            tool_config = get_tool_config_by_name(
                client_instance.tool_configs['publisher'], tool_config_name
            )
            if not tool_config:
                logger.error(
                    f"Couldn't find any tool config matching the name {tool_config_name}"
                )
                continue
            client_instance.run_tool_config(tool_config['reference'])


@run_in_main_thread
def run_bootstrap(client_instance, bootstrap_config):
    name = bootstrap_config.get('name')
    label = bootstrap_config.get('label')
    tool_config_names = bootstrap_config['options']['tool_configs']
    if bootstrap_config.get('dialog_name'):
        dialog_name = bootstrap_config.get('dialog_name')
        logger.info(
            f"Executing {dialog_name} for bootstrap {name}, with label {label}."
        )
        client_instance.run_dialog(
            dialog_name,
            dialog_options={
                'tool_config_names': tool_config_names,
                'docked': bootstrap_config['options'].get('docked', False),
            },
            dock_func=dock_maya_right,
        )
    else:
        # TODO move this to the client run_tool_config and get it out from here and from the dialog
        for tool_config_name in tool_config_names:
            print(client_instance.tool_configs)
            # TODO: fix tool configs to not be categorized by publisher or opener also be plain, and also in case contain all types
            tool_config = get_tool_config_by_name(
                client_instance.tool_configs['publisher'], tool_config_name
            )
            if not tool_config:
                logger.error(
                    f"Couldn't find any tool config matching the name {tool_config_name}"
                )
                continue
            client_instance.run_tool_config(tool_config['reference'])


def bootstrap_integration(framework_extensions_path):
    '''
    Initialise Maya Framework integration
    '''
    logger.debug(
        'Maya standalone integration initialising, extensions path:'
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
                app="Maya",
                registry=registry_info_dict,
                version=__version__,
                app_version=cmds.about(version=True),
                os=platform.platform(),
            ),
        )
    )

    # Instantiate Host and Client
    Host(event_manager, registry=registry_instance)
    client_instance = Client(event_manager, registry=registry_instance)

    # Init tools
    dcc_config = registry_instance.get_one(
        name='framework-maya', extension_type='dcc_config'
    )['extension']

    logger.debug(f'Read DCC config: {dcc_config}')

    # Create ftrack menu
    ftrack_menu = get_ftrack_menu()

    # Register tools into ftrack menu
    for tool in dcc_config['tools']:
        cmds.menuItem(
            parent=ftrack_menu,
            label=tool['label'],
            command=(
                functools.partial(
                    on_run_tool_callback,
                    client_instance,
                    tool.get('dialog_name'),
                    tool['options']['tool_configs'],
                    tool['options'].get('docked'),
                )
            ),
            image=":/{}.png".format(tool['icon']),
        )
    # Execute bootstrap tool-configs
    for bootstrap in dcc_config['bootstrap']:
        run_bootstrap(client_instance, bootstrap)

    return client_instance


# Find and read DCC config
try:
    bootstrap_integration(get_extensions_path_from_environment())
except:
    # Make sure any exception that happens are logged as there is most likely no console
    logger.error(traceback.format_exc())
    raise
