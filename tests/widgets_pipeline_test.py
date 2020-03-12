import os
from ftrack_connect_pipeline import host, constants, event
import ftrack_api

from Qt import QtWidgets

import sys

CWD = os.path.dirname(__name__)

event_paths = [
    os.path.abspath(os.path.join('ftrack-connect-pipeline-definition', 'resource', 'application_hook')),
    os.path.abspath(os.path.join('ftrack-connect-pipeline', 'resource', 'application_hook')),
    os.path.abspath(os.path.join('ftrack-connect-pipeline-qt', 'resource', 'application_hook')),
]

app = QtWidgets.QApplication(sys.argv)

session = ftrack_api.Session(auto_connect_event_hub=False, plugin_paths=event_paths)
event_manager = event.EventManager(
    session=session, mode=constants.LOCAL_EVENT_MODE
)

# init host
host.Host(event_manager)
CONTEXT_ID = None

def ready_callback(event):
    global CONTEXT_ID
    host_connection = event[0]
    task = host_connection.session.query(
        'select name from Task where project.name is "pipelinetest"'
    ).first()
    os.environ['FTRACK_CONTEXTID'] = task['id']
    CONTEXT_ID = task['id']


from ftrack_connect_pipeline_qt import client

client_connection = client.QtClient(event_manager)
client_connection.on_ready(ready_callback, time_out=30)

client_connection.context = CONTEXT_ID

client_connection.show()
sys.exit(app.exec_())