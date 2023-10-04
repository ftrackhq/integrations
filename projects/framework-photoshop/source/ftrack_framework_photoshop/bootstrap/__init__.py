# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack
import os
import logging
import time

from Qt import QtWidgets

import ftrack_api

from ftrack_constants import framework as constants
from ftrack_framework_core import host
from ftrack_framework_core.event import EventManager
from ftrack_framework_core import client

from ftrack_framework_core.configure_logging import configure_logging

configure_logging(
    'ftrack_framework_photoshop',
    extra_modules=["ftrack_qt"],
    propagate=False,
)

logger = logging.getLogger('ftrack_framework_photoshop.bootstrap')

session = ftrack_api.Session(auto_connect_event_hub=False)

remote_session = ftrack_api.Session(auto_connect_event_hub=True)

event_manager = EventManager(
    session=session,
    mode=constants.event.LOCAL_EVENT_MODE,
    remote_session=remote_session,
)


# DEBUG events during dev, will be removed
def handle_event_debug_callback(event):
    try:
        import datetime, json, sys

        print("[{}] ---- New event: ----".format(datetime.datetime.now()))

        print(json.dumps(event._data, indent=4))
        sys.stdout.flush()
    except:
        import traceback

        sys.stderr.write(traceback.format_exc())
        raise


event_manager.remote.subscribe_topic(
    'ftrack.*',
    handle_event_debug_callback,
)

host = host.Host(event_manager)

client = client.Client(event_manager)

# Create Qt application
app = QtWidgets.QApplication([])

use_uxp = (os.environ.get('FTRACK_PHOTOSHOP_UXP') or '').lower() in [
    'true',
    '1',
]

# Create remote connection
if use_uxp:
    from ftrack_framework_photoshop.remote_connection.uxp_connection import (
        UXBasePhotoshopRemoteConnection,
    )

    photoshop_connection = UXBasePhotoshopRemoteConnection(event_manager)
else:
    from ftrack_framework_photoshop.remote_connection.cep_connection import (
        CEPBasePhotoshopRemoteConnection,
    )

    photoshop_connection = CEPBasePhotoshopRemoteConnection(event_manager)

# Connect with Photoshop
photoshop_connection.connect()

# Wait for Photoshop to get ready to receive events
time.sleep(0.5)

# Probe and store Photoshop PID
photoshop_connection.probe_photoshop_pid()

# Run until it's closed, or CTRL+C
active_time = 0
while True:
    app.processEvents()
    time.sleep(0.01)
    active_time += 10
    # Failsafe check if PS is still alive
    if active_time % 1000 == 0:
        print('.', end='', flush=True)
    if active_time % (60 * 1000) == 0:
        if not photoshop_connection.connected:
            if not photoshop_connection.check_running():
                logger.warning(
                    'Photoshop never connected and process gone, shutting down!'
                )
                photoshop_connection.terminate()
        else:
            # Check if process still is with us
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
