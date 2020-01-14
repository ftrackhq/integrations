import os
from ftrack_connect_pipeline import host, constants, event
from ftrack_connect_pipeline.session import get_shared_session
from ftrack_connect_pipeline_qt import client
from Qt import QtWidgets
import sys

CWD = os.path.dirname(__name__)

event_paths = [
    os.path.abspath(os.path.join('ftrack-connect-pipeline-definition', 'resource', 'application_hook')),
    os.path.abspath(os.path.join('ftrack-connect-pipeline', 'resource', 'application_hook'))
]

# os.environ['FTRACK_EVENT_PLUGIN_PATH'] = os.pathsep.join(event_paths)

# create event manager
session = get_shared_session(plugin_paths=event_paths)

# session = ftrack_api.Session(auto_connect_event_hub=True)
event_manager = event.EventManager(
    session=session, mode=constants.LOCAL_EVENT_MODE
)

type(event_manager)

# init host
host.Host(event_manager)

# init client
app = QtWidgets.QApplication(sys.argv)
client_connection= client.QtClient(event_manager, ui="qt")
#client_connection.on_ready(ready_callback, time_out=30)
client_connection.on_ready(time_out=30)
client_connection.show()
sys.exit(app.exec_())

