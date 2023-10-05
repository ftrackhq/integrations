# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack
import os
import logging
import time
import sys

from Qt import QtWidgets

import ftrack_api

from ftrack_constants import framework as constants
from ftrack_framework_core.host import Host
from ftrack_framework_core.event import EventManager
from ftrack_framework_core.client import Client

from ftrack_framework_core.configure_logging import configure_logging

configure_logging(
    'ftrack_framework_photoshop',
    extra_modules=["ftrack_qt"],
    propagate=False,
)

logger = logging.getLogger('ftrack_framework_photoshop.bootstrap')

# Create Qt application
app = QtWidgets.QApplication.instance()

if not app:
    app = QtWidgets.QApplication(sys.argv)

photoshop_connection = None


def initialise():
    '''Initialise Photoshop Framework Python standalone part.'''

    global photoshop_connection

    session = ftrack_api.Session(auto_connect_event_hub=False)

    remote_session = ftrack_api.Session(auto_connect_event_hub=True)

    event_manager = EventManager(
        session=session,
        mode=constants.event.LOCAL_EVENT_MODE,
        remote_session=remote_session,
    )

    Host(event_manager)

    client = Client(event_manager)

    # Create remote connection

    from ftrack_framework_photoshop.remote_connection.cep_connection import (
        CEPBasePhotoshopRemoteConnection,
    )

    photoshop_version = os.environ.get('FTRACK_PHOTOSHOP_VERSION')
    assert (
        photoshop_version
    ), 'Photoshop integration requires FTRACK_PHOTOSHOP_VERSION passed as environment variable!'

    photoshop_connection = CEPBasePhotoshopRemoteConnection(
        client, int(photoshop_version)
    )

    # Connect with Photoshop
    photoshop_connection.connect()

    # Wait for Photoshop to get ready to receive events
    time.sleep(0.5)

    # Probe and store Photoshop PID
    photoshop_connection.probe_photoshop_pid()


def run():
    '''Run Photoshop Framework Python standalone part as long as Photoshop is alive.'''

    # Run until it's closed, or CTRL+C
    active_time = 0
    while True:
        app.processEvents()
        time.sleep(0.01)
        active_time += 10
        # Failsafe check if PS is still alive
        if active_time % 10000 == 0:
            logger.info(
                "Integration alive has been for {}s, connected: {}".format(
                    active_time / 1000, photoshop_connection.connected
                )
            )
        if active_time % (10 * 1000) == 0:
            if not photoshop_connection.connected:
                # Check if Photoshop still is running
                if not photoshop_connection.check_running():
                    logger.warning(
                        'Photoshop never connected and process gone, shutting down!'
                    )
                    photoshop_connection.terminate()
            else:
                # Check if Photoshop panel is alive
                if not photoshop_connection.check_responding():
                    if not photoshop_connection.check_running():
                        logger.warning(
                            'Photoshop is not responding and process gone, shutting down!'
                        )
                        photoshop_connection.terminate()
                    else:
                        logger.warning(
                            'Photoshop is not responding but process is still there, panel temporarily closed?'
                        )


initialise()
run()
