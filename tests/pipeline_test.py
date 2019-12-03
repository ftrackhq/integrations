from ftrack_connect_pipeline.session import get_shared_session
from ftrack_connect_pipeline import client, host
from ftrack_connect_pipeline import event
import os
os.environ['FTRACK_EVENT_PLUGIN_PATH'] = '/Users/lluisftrack/work/brokenC/ftrack/repos/ftrack-connect-pipeline-definition/resource/application_hook'


session = get_shared_session()
event_thread = event.NewApiEventHubThread()
event_thread.start(session)


baseHost = host.initialise(session, host='api', ui=None)
baseClient = client.BasePipelineClient(ui=None, host='api', hostid=baseHost)
print baseClient.packages





