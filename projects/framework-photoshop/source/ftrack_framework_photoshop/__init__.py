# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack
import os
import logging
import time
import sys
import os

from Qt import QtWidgets, QtCore

import ftrack_api

from ftrack_constants import framework as constants
from ftrack_utils.framework.config.dcc import read_dcc_config
from ftrack_utils.extensions.environment import (
    get_extensions_path_from_environment,
)
from ftrack_utils.framework.remote import get_integration_session_id
from ftrack_framework_core.host import Host
from ftrack_framework_core.event import EventManager
from ftrack_framework_core.client import Client
from ftrack_framework_core import registry

from ftrack_framework_core.configure_logging import configure_logging


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
    'ftrack_framework_photoshop',
    extra_modules=["ftrack_qt"],
    propagate=False,
)

logger = logging.getLogger(__name__)
logger.debug('v{}'.format(__version__))

photoshop_connection = None

# Create Qt application
app = QtWidgets.QApplication.instance()

if not app:
    app = QtWidgets.QApplication(sys.argv)


def bootstrap_integration(framework_extensions_path, dcc_config):
    '''Initialise Photoshop Framework Python standalone part,
    with panels defined in *panel_launchers*'''

    global photoshop_connection

    session = ftrack_api.Session(auto_connect_event_hub=False)

    remote_session = ftrack_api.Session(auto_connect_event_hub=True)

    event_manager = EventManager(
        session=session,
        mode=constants.event.LOCAL_EVENT_MODE,
        remote_session=remote_session,
    )

    registry_instance = registry.Registry()
    registry_instance.scan_extensions(paths=framework_extensions_path)

    Host(event_manager, registry=registry_instance)

    client = Client(event_manager, registry=registry_instance)

    # Init tools
    # TODO: Implement tool init
    print('Got dcc config: ', dcc_config)


# Find and read DCC config
framework_extensions_path = get_extensions_path_from_environment()
print('Got framework extensions path: ', framework_extensions_path)

bootstrap_integration(
    framework_extensions_path,
    read_dcc_config('photoshop', framework_extensions_path),
)
# TODO: Implement RCP connection and process monitor
time.sleep(5)
logger.error('Test launch shutting down!')
