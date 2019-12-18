import os
from ftrack_connect_pipeline import client, host, constants, event
from ftrack_connect_pipeline.session import get_shared_session


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

# init host
host.Host(event_manager, host=constants.HOST)


# on client ready callback
def ready_callback(hosts):
    host = hosts[0]
    print "host {}".format(host)
    print "host.definitions {}".format(host.definitions)
    print "host.definitions['publishers'] {}".format(host.definitions['publishers'])
    publisher = host.definitions['publishers'][0]
    print 'using publisher: ', publisher
    publisher['components'][0]['stages'][0]['collectors'][0]['options']['path'] = "/test/path"
    host.run(publisher)


# init client
client_connection= client.Client(event_manager, ui=constants.UI)
client_connection.on_ready(ready_callback, time_out=10)

