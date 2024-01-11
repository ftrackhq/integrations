# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

import logging
import time
import sys
import os
import traceback

from Qt import QtWidgets, QtCore

import nuke, nukescripts
from nukescripts import panels

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

from ftrack_qt.utils.decorators import invoke_in_qt_main_thread

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


def get_ftrack_menu(menu_name='ftrack', submenu_name='pipeline'):
    '''Get the current ftrack menu, create it if does not exists.'''

    nuke_menu = nuke.menu("Nuke")
    ftrack_menu = nuke_menu.findItem(menu_name)
    if not ftrack_menu:
        ftrack_menu = nuke_menu.addMenu(menu_name)
    if submenu_name is not None:
        ftrack_sub_menu = ftrack_menu.findItem(submenu_name)
        if not ftrack_sub_menu:
            ftrack_sub_menu = ftrack_menu.addMenu(submenu_name)

        return ftrack_sub_menu
    else:
        return ftrack_menu


class WidgetLauncher(object):
    def __init__(self, client):
        self._client = client

    def launch(self, dialog_name, tool_config_names):
        if dialog_name == 'publish':
            # Restore panel
            pane = nuke.getPaneFor("Properties.1")
            panel = nukescripts.restorePanel(dialog_name)
            panel.addToPane(pane)
        else:
            self._client.run_dialog(
                dialog_name,
                dialog_options={'tool_config_names': tool_config_names},
            )


def bootstrap_integration(framework_extensions_path):
    logger.debug(
        'Maya integration initialising, extensions path:'
        f' {framework_extensions_path}'
    )

    session = ftrack_api.Session(auto_connect_event_hub=False)

    event_manager = EventManager(
        session=session, mode=constants.event.LOCAL_EVENT_MODE
    )

    registry_instance = registry.Registry()
    registry_instance.scan_extensions(paths=framework_extensions_path)

    Host(event_manager, registry=registry_instance)

    client = Client(event_manager, registry=registry_instance)

    # Init tools
    dcc_config = registry_instance.get_one(
        name='framework-nuke', extension_type='dcc_config'
    )['extension']

    logger.debug(f'Read DCC config: {dcc_config}')

    # Create menus

    ftrack_menu = get_ftrack_menu(submenu_name=None)

    globals()['ftrackWidgetLauncher'] = WidgetLauncher(client)

    for tool_definition in dcc_config['tools']:
        name = tool_definition['name']
        dialog_name = tool_definition['dialog_name']
        tool_config_names = tool_definition.get('options', {}).get(
            'tool_configs'
        )
        label = tool_definition.get('label')

        if name == 'separator':
            ftrack_menu.addSeparator()
        else:
            if name in ['publish']:
                # Setup panel

                def wrap_class(*args, **kwargs):
                    widget = client.run_dialog(
                        dialog_name,
                        dialog_options={
                            'tool_config_names': tool_config_names
                        },
                    )
                    return widget

                class_name = f'ftrack{name.title()}Class'
                globals()[class_name] = wrap_class

                # Register docked panel
                panels.registerWidgetAsPanel(
                    f'{__name__}.{class_name}',
                    f'ftrack {label}',
                    name,
                )

            print(
                f'@@@ {__name__}.ftrackWidgetLauncher.launch("{name}",{str(tool_config_names)})'
            )
            ftrack_menu.addCommand(
                label,
                f'{__name__}.ftrackWidgetLauncher.launch("{name}",{str(tool_config_names)})',
            )


# Find and read DCC config
try:
    bootstrap_integration(get_extensions_path_from_environment())
except:
    # Make sure any exception that happens are logged as there is most likely no console
    logger.error(traceback.format_exc())
    raise
