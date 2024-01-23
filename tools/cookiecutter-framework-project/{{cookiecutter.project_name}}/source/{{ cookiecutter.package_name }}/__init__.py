# :coding: utf-8
# :copyright: Copyright (c) 2014-2024 ftrack
import logging
import os
import traceback

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

from ftrack_framework_{{ cookiecutter.plugin_name }}.utils import dock_{{ cookiecutter.plugin_name }}_right, run_in_main_thread


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
    '{{ cookiecutter.package_name }}',
    extra_modules=['ftrack_qt'],
    propagate=False,
)

logger = logging.getLogger(__name__)
logger.debug('v{}'.format(__version__))


@run_in_main_thread
def on_run_dialog_callback(
    client_instance, dialog_name, tool_config_names, {{ cookiecutter.plugin_name }}_args
):
    client_instance.run_dialog(
        dialog_name,
        dialog_options={'tool_config_names': tool_config_names},
        dock_func=dock_{{ cookiecutter.plugin_name }}_right,
    )


def bootstrap_integration(framework_extensions_path):
    '''
    Initialise {{ cookiecutter.plugin_name.capitalize() }} Framework integration
    '''
    logger.debug(
        '{{ cookiecutter.plugin_name.capitalize() }} standalone integration initialising, extensions path:'
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

    # Instantiate Host and Client
    Host(event_manager, registry=registry_instance)
    client_instance = Client(event_manager, registry=registry_instance)

    # Init tools
    dcc_config = registry_instance.get_one(
        name='framework-{{ cookiecutter.plugin_name }}', extension_type='dcc_config'
    )['extension']

    logger.debug(f'Read DCC config: {dcc_config}')

    # Create ftrack menu

    # Register tools into ftrack menu
    for tool in dcc_config['tools']:
        pass

    return client_instance


# Find and read DCC config
try:
    bootstrap_integration(get_extensions_path_from_environment())
except:
    # Make sure any exception that happens are logged as there is most likely no console
    logger.error(traceback.format_exc())
    raise
