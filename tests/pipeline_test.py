import os
from ftrack_connect_pipeline import client, host, constants, event
from ftrack_connect_pipeline.session import get_shared_session


CWD = os.path.dirname(__name__)

event_paths = [
    os.path.abspath(os.path.join('ftrack-connect-pipeline-definition', 'resource', 'application_hook')),
    os.path.abspath(os.path.join('ftrack-connect-pipeline', 'resource', 'application_hook'))
]

os.environ['FTRACK_EVENT_PLUGIN_PATH'] = os.pathsep.join(event_paths)

event_manager = event.EventManager()
host_id = host.initialise(event_manager, host=constants.HOST)

# init client
baseClient = client.BasePipelineClient(event_manager, ui=constants.UI)
host = baseClient.hosts[0]
publisher = host.data['publishers'][0]
print 'using publisher: ', publisher['name']
host.run(publisher)
