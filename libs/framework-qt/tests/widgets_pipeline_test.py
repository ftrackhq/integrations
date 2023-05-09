import os
from ftrack_connect_pipeline import host, constants, event
import ftrack_api

from Qt import QtWidgets

import sys

# Example of how to quick test Asset Manager, Log viewer, Publisher and Loader
# in standalone mode

# Set the minimum required Environment variables.
os.environ['FTRACK_EVENT_PLUGIN_PATH'] = os.pathsep.join(
    [
        '<PATH-TO-PIPELINE-DEFINITION>\\resource\\plugins\\qt',
        '<PATH-TO-PIPELINE-DEFINITION>\\resource\\plugins\\common',
        '<PATH-TO-PIPELINE-DEFINITION>\\resource\\definitions',
    ]
)


# Init QApplication
app = QtWidgets.QApplication(sys.argv)

# Create a session and Event Manager
session = ftrack_api.Session(auto_connect_event_hub=False)
event_manager = event.EventManager(
    session=session, mode=constants.LOCAL_EVENT_MODE
)

# Init host
host.Host(event_manager)

# Init Client
from ftrack_connect_pipeline_qt.client import (
    publish,
    load,
    asset_manager,
    log_viewer,
)

pub_client_connection = publish.QtPublisherClientWidget(event_manager)
# load_client_connection = load.QtLoaderClient(event_manager)
# am_client_connection = asset_manager.QtAssetManagerClient(event_manager)
# lv_client_connection = log_viewer.QtLogViewerClient(event_manager)

# Set the context
context_entity = session.query("Task").first()

pub_client_connection.context_selector.set_context_id(context_id)
# load_client_connection.context_selector.set_context_id(context_id))
# am_client_connection.context_id(context_id)
# lv_client_connection.context_id(context_id)

# Execute the UI
pub_client_connection.show()
# load_client_connection.show()
# am_client_connection.show()
# lv_client_connection.show()

sys.exit(app.exec_())
