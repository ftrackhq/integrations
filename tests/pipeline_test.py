import os
from ftrack_connect_pipeline import client, host, constants, event
from ftrack_connect_pipeline.session import get_shared_session


CWD = os.path.dirname(__name__)

event_paths = [
    os.path.abspath(os.path.join('ftrack-connect-pipeline-definition', 'resource', 'application_hook')),
    os.path.abspath(os.path.join('ftrack-connect-pipeline', 'resource', 'application_hook'))
]

os.environ['FTRACK_EVENT_PLUGIN_PATH'] = os.pathsep.join(event_paths)

# create event manager
event_manager = event.EventManager(mode=constants.LOCAL_EVENT_MODE)

# init host
host_id = host.initialise(event_manager, host=constants.HOST)


def ready_callback(hosts):
    host = hosts[0]
    publisher = host.data['publishers'][0]
    print 'using publisher: ', publisher['name']
    host.run(publisher)



# init client
client_connection= client.Client(event_manager, ui=constants.UI)
# print client_connection.connected
client_connection.on_ready(ready_callback, time_out=3)
