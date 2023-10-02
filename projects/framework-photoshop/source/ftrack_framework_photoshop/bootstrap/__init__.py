# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

import os
import logging
import time

from ftrack_framework_core.configure_logging import configure_logging


configure_logging(
    'ftrack_framework_photoshop',
    propagate=False,
)

logger = logging.getLogger('ftrack_framework_photoshop.bootstrap')

use_uxp = (os.environ.get('FTRACK_PHOTOSHOP_UXP') or '').lower() in [
    'true',
    '1',
]

# Init QApplication
if use_uxp:
    from ftrack_framework_photoshop.app.uxp_app import UXPPhotoshopApplication

    app = UXPPhotoshopApplication()
else:
    from ftrack_framework_photoshop.app.cep_app import CEPPhotoshopApplication

    app = CEPPhotoshopApplication()

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
        # Check if Photoshop still is with us
        if not app.check_responding():
            if not app.check_alive():
                logger.warning(
                    'Photoshop is not responding and process gone, shutting down!'
                )
                app.terminate()
            else:
                logger.warning(
                    'Photoshop is not responding but process is still there, panel temporarily closed?'
                )
