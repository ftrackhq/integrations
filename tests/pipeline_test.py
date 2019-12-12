import os
from ftrack_connect_pipeline import client, host, constants
from ftrack_connect_pipeline.session import get_shared_session

event_paths = [
    os.path.abspath(os.path.join('ftrack-connect-pipeline-definition', 'resource', 'application_hook')),
    os.path.abspath(os.path.join('ftrack-connect-pipeline', 'resource', 'application_hook'))
]


session = get_shared_session(plugin_paths=event_paths)
host = host.initialise(session, host=constants.HOST, ui=constants.UI)
baseClient = client.BasePipelineClient(ui=None, host=constants.UI, hostid=host)
print baseClient.packages
