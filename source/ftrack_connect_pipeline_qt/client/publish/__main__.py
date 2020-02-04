import sys
import os

import logging
from Qt import QtWidgets

logger = logging.getLogger(__name__)

deps_paths = os.environ.get('PYTHONPATH', '').split(os.pathsep)
for path in deps_paths:
    sys.path.append(path)


QtWidgets.QApplication.setStyle('plastique')

import ftrack_api
from ftrack_connect_pipeline import constants, event, host
from ftrack_connect_pipeline_qt.client.publish import QtPublisherClient

if __name__ == '__main__':
    app = QtWidgets.QApplication.instance()
    session = ftrack_api.Session(auto_connect_event_hub=False)
    event_manager = event.EventManager(
        session=session, mode=constants.LOCAL_EVENT_MODE
    )
    host.Host(event_manager)
    wid = QtPublisherClient(event_manager)
    wid.show()
    sys.exit(app.exec_())
