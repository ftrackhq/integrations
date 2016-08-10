import os
import sys
import signal
import logging

from PySide import QtGui

import ftrack_api

logging.basicConfig(level=logging.INFO)

BASE_DIR = os.path.abspath(
    os.path.dirname(
        __file__
    )
)

print os.path.join(
            BASE_DIR,
            'resource',
            'hook'
        )

session = ftrack_api.Session(
    plugin_paths=[
        os.path.join(
            BASE_DIR,
            'resource',
            'hook'
        )
    ]
)


os.environ['PYBLISHPLUGINPATH'] = os.path.join(
    BASE_DIR,
    'resource',
    'pyblish_plugin'
)

sys.path.append(
    os.path.join(
        BASE_DIR,
        'source'
    )
)

os.environ['FTRACK_CONTEXT_ID'] = '9e9b2100-5910-11e4-8a3c-3c0754282242'

# Enable ctrl+c to quit application when started from command line.
signal.signal(signal.SIGINT, signal.SIG_DFL)

application = QtGui.QApplication([])

import ftrack_connect_pipeline.ui.theme
ftrack_connect_pipeline.ui.theme.applyFont()
ftrack_connect_pipeline.ui.theme.applyTheme(application, 'light', 'cleanlooks')

import ftrack_connect_pipeline.ui.publish_actions_dialog
ftrack_connect_pipeline.ui.publish_actions_dialog.show(session)
