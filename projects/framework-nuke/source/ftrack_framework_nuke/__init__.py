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


# TODO: activate this on implementing run in main thread for nuke like in maya
@run_in_main_thread
def on_run_dialog_callback(dialog_name, tool_config_names, docked):
    client_instance.run_dialog(
        dialog_name,
        dialog_options={
            'tool_config_names': tool_config_names,
            'docked': docked,
        },
        dock_func=partial(dock_nuke_right),
    )
    # Prevent bug in Nuke were curve editor is activated on docking a panel
    if docked:
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
        'launchers': [item['name'] for item in registry_instance.launchers]
        if registry_instance.launchers
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

    globals()['onRunDialogCallback'] = on_run_dialog_callback

    ftrack_menu = get_ftrack_menu(submenu_name=None)

    for tool in dcc_config['tools']:
        name = tool['name']
        dialog_name = tool['dialog_name']
        tool_config_names = tool.get('options', {}).get('tool_configs')
        label = tool.get('label')
        docked = tool.get('options', {}).get('docked')

        if name == 'separator':
            ftrack_menu.addSeparator()
        else:
            ftrack_menu.addCommand(
                label,
                f'{__name__}.onRunDialogCallback("{dialog_name}",{str(tool_config_names)}, {docked})',
            )

    # TODO: setup animation timeline - frame rate, start and end frame


# Find and read DCC config
try:
    bootstrap_integration(get_extensions_path_from_environment())
except:
    # Make sure any exception that happens are logged as there is most likely no console
    logger.error(traceback.format_exc())
    raise
