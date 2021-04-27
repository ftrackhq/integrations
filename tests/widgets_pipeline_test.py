import os
from ftrack_connect_pipeline import host, constants, event
import ftrack_api

from Qt import QtWidgets

import sys

# Example of how to quick test Asset Manager, Log viewer, Publisher and Loader
# in standalone mode

# Setup the environments
os.environ['FTRACK_EVENT_PLUGIN_PATH'] ='<YOUR-PATH-TO>/ftrack-connect-pipeline-definition/resource/plugins/python:' \
                                        '<YOUR-PATH-TO>/ftrack-connect-pipeline-definition/resource/plugins/qt:' \
                                        '<YOUR-PATH-TO>/ftrack-connect-pipeline-definition/resource/application_hook: ' \
                                        '<YOUR-PATH-TO>/ftrack-connect-pipeline-definition/resource/definitions:'


app = QtWidgets.QApplication(sys.argv)

session = ftrack_api.Session(auto_connect_event_hub=False)
event_manager = event.EventManager(
    session=session, mode=constants.LOCAL_EVENT_MODE
)

# init host
host.Host(event_manager)

from ftrack_connect_pipeline_qt.client import asset_manager, log_viewer, publish, load

# Init a client
am_client_connection = asset_manager.QtAssetManagerClient(event_manager)
lv_client_connection = log_viewer.QtLogViewerClient(event_manager)
pub_client_connection = publish.QtPublisherClient(event_manager)
load_client_connection = load.QtLoaderClient(event_manager)

context_id = '<Add a context id here>'#'690afd58-06d0-11ea-bbbb-ee594985c7e2'

# Set the context
am_client_connection.context = context_id
lv_client_connection.context = context_id
pub_client_connection.context = context_id
load_client_connection.context = context_id

# Show the ui
am_client_connection.show()
lv_client_connection.show()
pub_client_connection.show()
load_client_connection.show()

sys.exit(app.exec_())
