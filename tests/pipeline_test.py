import os
from ftrack_connect_pipeline import client, host
from ftrack_connect_pipeline.session import get_shared_session

os.environ['FTRACK_EVENT_PLUGIN_PATH'] = '/Path/to/your/ftrack-connect-pipeline-definition/resource/application_hook:/Path/to/your/ftrack-connect-pipeline/resource/application_hook'
print os.environ['FTRACK_EVENT_PLUGIN_PATH']

session =get_shared_session()
host = host.initialise(session, host='api', ui=None)
baseClient = client.BasePipelineClient(ui=None, host='api', hostid=host)
print baseClient.packages
