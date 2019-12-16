import os
from ftrack_connect_pipeline import client, host, constants
from ftrack_connect_pipeline.session import get_shared_session

CWD = os.path.dirname(__name__)

event_paths = [
    os.path.abspath(os.path.join('ftrack-connect-pipeline-definition', 'resource', 'application_hook')),
    os.path.abspath(os.path.join('ftrack-connect-pipeline', 'resource', 'application_hook'))
]

print event_paths
os.environ['FTRACK_EVENT_PLUGIN_PATH'] = os.pathsep.join(event_paths)

session = get_shared_session()
host_id = host.initialise(session, host=constants.HOST)
# init client
baseClient = client.BasePipelineClient(session, ui=constants.UI)
host = baseClient.hosts[0]
publisher = host.data['publishers'][0]
print 'using publisher: ', publisher['name']
host.run(publisher)
