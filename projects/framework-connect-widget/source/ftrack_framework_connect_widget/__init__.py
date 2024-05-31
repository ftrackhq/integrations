# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack
import os
import logging
import traceback
from functools import partial
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

from ftrack_framework_connect_widget.utils import dock_to_connect

import ftrack_connect

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
    'ftrack_framework_connect_widget',
    extra_modules=['ftrack_qt'],
    propagate=False,
)

logger = logging.getLogger(__name__)
logger.debug('v{}'.format(__version__))


def on_run_tool_callback(
    session, client_instance, tool_name, dialog_name=None, options=dict
):
    client_instance.run_tool(
        tool_name,
        dialog_name,
        options,
        dock_func=partial(dock_to_connect, session) if dialog_name else None,
    )


def bootstrap_integration(framework_extensions_path):
    # Create ftrack session and instantiate event manager
    session = ftrack_api.Session(auto_connect_event_hub=False)
    event_manager = EventManager(
        session=session, mode=constants.event.LOCAL_EVENT_MODE
    )

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
                app="framework Connect widget",
                registry=registry_info_dict,
                version=__version__,
                app_version=ftrack_connect.__version__,
                os=platform.platform(),
            ),
        )
    )

    # Instantiate Host and Client
    Host(event_manager, registry=registry_instance)
    client_instance = Client(event_manager, registry=registry_instance)

    # Init tools
    dcc_config = registry_instance.get_one(
        name='framework-connect', extension_type='dcc_config'
    )['extension']

    # Register tools into Connect
    for tool in dcc_config['tools']:
        on_run_tool_callback(
            session,
            client_instance,
            tool.get('name'),
            tool.get('dialog_name'),
            tool['options'],
        )

    return client_instance


# Find and read DCC config
try:
    bootstrap_integration(get_extensions_path_from_environment())
except:
    # Make sure any exception that happens are logged as there is most likely no console
    logger.error(traceback.format_exc())
    raise
