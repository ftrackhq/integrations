import os
from ftrack_connect_pipeline import host, constants, event
import ftrack_api

from Qt import QtWidgets

import sys

os.environ['FTRACK_EVENT_PLUGIN_PATH'] = '/Users/lluisftrack/work/brokenC/ftrack/repos/ftrack-connect-pipeline-definition/resource/application_hook:/Users/lluisftrack/work/brokenC/ftrack/repos/ftrack-connect-pipeline/resource/application_hook:/Users/lluisftrack/work/brokenC/ftrack/repos/ftrack-connect-pipeline-qt/resource/application_hook'
print os.environ['FTRACK_EVENT_PLUGIN_PATH']

app = QtWidgets.QApplication(sys.argv)

session = ftrack_api.Session(auto_connect_event_hub=False)
event_manager = event.EventManager(
    session=session, mode=constants.LOCAL_EVENT_MODE
)

# init host
host.Host(event_manager)

from ftrack_connect_pipeline_qt.client import asset_manager
from ftrack_connect_pipeline_qt.client import log_manager

client_connection = asset_manager.QtAssetManagerClient(event_manager)
log_connection = log_manager.QtLogManagerClient(event_manager)

client_connection.context = '690afd58-06d0-11ea-bbbb-ee594985c7e2'
log_connection.context = '690afd58-06d0-11ea-bbbb-ee594985c7e2'

client_connection.show()
log_connection.show()
sys.exit(app.exec_())
